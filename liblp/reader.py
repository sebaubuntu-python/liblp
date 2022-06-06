#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from ctypes import sizeof, c_uint8
from hashlib import sha256
from io import SEEK_SET, BufferedIOBase

from liblp.include.metadata_format import (
	LP_BLOCK_DEVICE_SLOT_SUFFIXED,
	LP_GROUP_SLOT_SUFFIXED,
	LP_METADATA_GEOMETRY_MAGIC,
	LP_METADATA_GEOMETRY_SIZE,
	LP_METADATA_HEADER_MAGIC,
	LP_METADATA_MAJOR_VERSION,
	LP_METADATA_MINOR_VERSION_MAX,
	LP_METADATA_VERSION_FOR_EXPANDED_HEADER,
	LP_METADATA_VERSION_FOR_UPDATED_ATTR,
	LP_PARTITION_ATTR_SLOT_SUFFIXED,
	LP_PARTITION_ATTRIBUTE_MASK_V0,
	LP_PARTITION_ATTRIBUTE_MASK_V1,
	LP_SECTOR_SIZE,
	LP_TARGET_TYPE_LINEAR,
	LpMetadataExtent,
	LpMetadataGeometry,
	LpMetadataHeader,
	LpMetadataHeaderV1_0,
	LpMetadataPartition,
	LpMetadataPartitionGroup,
	LpMetadataBlockDevice,
	LpMetadataTableDescriptor
)
from liblp.liblp import LpMetadata
from liblp.partition_opener import IPartitionOpener, PartitionOpener
from liblp.utility import (
	GetMetadataSuperBlockDevice,
	GetPrimaryGeometryOffset,
	GetBackupGeometryOffset,
	GetTotalMetadataSize,
	GetPrimaryMetadataOffset,
	GetBackupMetadataOffset,
	SlotSuffixForSlotNumber,
	UpdatePartitionName,
	UpdateBlockDevicePartitionName,
	UpdatePartitionGroupName,
)

def ParseGeometry(buffer: bytes):
	geometry = LpMetadataGeometry.from_buffer_copy(buffer)

	# Check the magic signature.
	assert geometry.magic == LP_METADATA_GEOMETRY_MAGIC, \
		"Logical partition metadata has invalid geometry magic signature."

	# Reject if the struct size is larger than what we compiled. This is so we
    # can compute a checksum with the |struct_size| field rather than using
    # sizeof.
	assert geometry.struct_size <= sizeof(LpMetadataGeometry), \
		"Logical partition metadata has unrecognized fields."

	# Recompute and check the CRC32.
	temp = LpMetadataGeometry.from_buffer_copy(bytes(geometry))
	temp.checksum = (c_uint8*32)(0)
	crc = sha256(bytes(temp)).digest()
	assert crc == bytes(geometry.checksum), \
		"Logical partition metadata has invalid geometry checksum."

	# Check that the struct size is equal (this will have to change if we ever
	# change the struct size in a release).
	assert geometry.struct_size == sizeof(LpMetadataGeometry), \
		"Logical partition metadata has invalid struct size."
	assert geometry.metadata_slot_count != 0, \
		"Logical partition metadata has invalid slot count."
	assert geometry.metadata_max_size % LP_SECTOR_SIZE == 0, \
		"Metadata max size is not sector-aligned."

	return geometry

def ReadPrimaryGeometry(fd: BufferedIOBase) -> LpMetadataGeometry:
	fd.seek(GetPrimaryGeometryOffset(), SEEK_SET)
	buffer = fd.read(LP_METADATA_GEOMETRY_SIZE)
	return ParseGeometry(buffer)

def ReadBackupGeometry(fd: BufferedIOBase) -> LpMetadataGeometry:
	fd.seek(GetBackupGeometryOffset(), SEEK_SET)
	buffer = fd.read(LP_METADATA_GEOMETRY_SIZE)
	return ParseGeometry(buffer)

def ReadLogicalPartitionGeometry(fd: BufferedIOBase) -> LpMetadataGeometry:
	"""
	Read and validate geometry information from a block device that holds
	logical partitions. If the information is corrupted, this will attempt
	to read it from a secondary backup location.
	"""
	geometry = ReadPrimaryGeometry(fd)
	if not geometry:
		geometry = ReadBackupGeometry(fd)

	return geometry

def ValidateTableBounds(header: LpMetadataHeader, table: LpMetadataTableDescriptor):
	assert table.offset <= header.tables_size
	table_size = table.num_entries * table.entry_size
	assert header.tables_size - table.offset >= table_size

def ReadMetadataHeader(fd: BufferedIOBase) -> LpMetadataHeader:
	header = LpMetadataHeader.from_buffer_copy(fd.read(sizeof(LpMetadataHeaderV1_0))
		+ b'\x00' * (sizeof(LpMetadataHeader) - sizeof(LpMetadataHeaderV1_0)))

	assert header.magic == LP_METADATA_HEADER_MAGIC, \
		"Logical partition metadata has invalid magic value."
	assert (header.major_version == LP_METADATA_MAJOR_VERSION
	        and header.minor_version <= LP_METADATA_MINOR_VERSION_MAX), \
		"Logical partition metadata has incompatible version."

	expected_struct_size = sizeof(header)
	if header.minor_version < LP_METADATA_VERSION_FOR_EXPANDED_HEADER:
		expected_struct_size = sizeof(LpMetadataHeaderV1_0)
	if header.header_size != expected_struct_size:
		raise Exception("Invalid partition metadata header struct size.")

	# Read in any remaining fields, the last step needed before checksumming.
	remaining_bytes = header.header_size - sizeof(LpMetadataHeaderV1_0)
	if remaining_bytes:
		header = LpMetadataHeader.from_buffer_copy(
			bytes(header)[:sizeof(LpMetadataHeaderV1_0)] + fd.read(remaining_bytes))

	# To compute the header's checksum, we have to temporarily set its checksum
    # field to 0. Note that we must only compute up to |header_size|.
	temp = LpMetadataHeader.from_buffer_copy(bytes(header))
	temp.header_checksum = (c_uint8*32)(0)
	crc = sha256(bytes(temp)).digest()
	assert crc == bytes(header.header_checksum), \
		"Logical partition metadata has invalid checksum."

	ValidateTableBounds(header, header.partitions)
	ValidateTableBounds(header, header.extents)
	ValidateTableBounds(header, header.groups)
	ValidateTableBounds(header, header.block_devices)

	# Check that table entry sizes can accomodate their respective structs. If
    # table sizes change, these checks will have to be adjusted.
	assert header.partitions.entry_size == sizeof(LpMetadataPartition), \
		"Logical partition metadata has invalid partition table entry size."
	assert header.extents.entry_size == sizeof(LpMetadataExtent), \
		"Logical partition metadata has invalid extent table entry size."
	assert header.groups.entry_size == sizeof(LpMetadataPartitionGroup), \
		"Logical partition metadata has invalid group table entry size."

	return header

def ParseMetadata(geometry: LpMetadataGeometry, fd: BufferedIOBase) -> LpMetadata:
	"""
	Read and validate metadata information from a block device that holds
	logical partitions. If the information is corrupted, this will attempt
	to read it from a secondary backup location.
	"""
	metadata = LpMetadata()

	metadata.geometry = geometry
	metadata.header = ReadMetadataHeader(fd)

	assert metadata.header.tables_size <= geometry.metadata_max_size, \
		"Invalid partition metadata header table size."

	buffer = fd.read(metadata.header.tables_size)

	checksum = sha256(buffer).digest()
	assert checksum == bytes(metadata.header.tables_checksum), \
		"Logical partition metadata has invalid table checksum."

	valid_attributes = LP_PARTITION_ATTRIBUTE_MASK_V0
	if metadata.header.minor_version >= LP_METADATA_VERSION_FOR_UPDATED_ATTR:
		valid_attributes |= LP_PARTITION_ATTRIBUTE_MASK_V1

	# ValidateTableSize ensured that |cursor| is valid for the number of
    # entries in the table.
	offset = metadata.header.partitions.offset
	for _ in range(metadata.header.partitions.num_entries):
		partition = LpMetadataPartition.from_buffer_copy(buffer, offset)
		offset += metadata.header.partitions.entry_size

		if partition.attributes & ~valid_attributes:
			raise Exception("Logical partition has invalid attribute set.")
		assert partition.first_extent_index + partition.num_extents >= partition.first_extent_index, \
			"Logical partition first_extent_index + num_extents overflowed."
		assert partition.first_extent_index + partition.num_extents <= metadata.header.extents.num_entries, \
			"Logical partition has invalid extent list."
		assert partition.group_index < metadata.header.groups.num_entries, \
			"Logical partition has invalid group index."

		metadata.partitions.append(partition)

	offset = metadata.header.extents.offset
	for _ in range(metadata.header.extents.num_entries):
		extent = LpMetadataExtent.from_buffer_copy(buffer, offset)
		offset += metadata.header.extents.entry_size

		if (extent.target_type == LP_TARGET_TYPE_LINEAR
				and extent.target_source >= metadata.header.block_devices.num_entries):
			raise Exception("Logical partition extent has invalid block device.")

		metadata.extents.append(extent)

	offset = metadata.header.groups.offset
	for _ in range(metadata.header.groups.num_entries):
		group = LpMetadataPartitionGroup.from_buffer_copy(buffer, offset)
		offset += metadata.header.groups.entry_size

		metadata.groups.append(group)

	offset = metadata.header.block_devices.offset
	for _ in range(metadata.header.block_devices.num_entries):
		block_device = LpMetadataBlockDevice.from_buffer_copy(buffer, offset)
		offset += metadata.header.block_devices.entry_size

		metadata.block_devices.append(block_device)

	super_device = GetMetadataSuperBlockDevice(metadata)
	assert super_device, "Metadata does not specify a super device."

	# Check that the metadata area and logical partition areas don't overlap.
	metadata_region = GetTotalMetadataSize(geometry.metadata_max_size, geometry.metadata_slot_count)
	if metadata_region > super_device.first_logical_sector * LP_SECTOR_SIZE:
		raise Exception("Logical partition metadata overlaps with logical partition contents.")

	return metadata

def ReadPrimaryMetadata(fd: BufferedIOBase, geometry: LpMetadataGeometry,
                        slot_number: int):
	offset = GetPrimaryMetadataOffset(geometry, slot_number)
	fd.seek(offset, SEEK_SET)
	return ParseMetadata(geometry, fd)

def ReadBackupMetadata(fd: BufferedIOBase, geometry: LpMetadataGeometry,
                       slot_number: int):
	offset = GetBackupMetadataOffset(geometry, slot_number)
	fd.seek(offset, SEEK_SET)
	return ParseMetadata(geometry, fd)


def AdjustMetadataForSlot(metadata: LpMetadata, slot_number: int):
	slot_suffix = SlotSuffixForSlotNumber(slot_number)

	for partition in metadata.partitions:
		if not (partition.attributes & LP_PARTITION_ATTR_SLOT_SUFFIXED):
			continue
		partition_name = GetPartitionName(partition) + slot_suffix
		UpdatePartitionName(partition, partition_name)
		partition.attributes &= ~LP_PARTITION_ATTR_SLOT_SUFFIXED

	for block_device in metadata.block_devices:
		if not (block_device.flags & LP_BLOCK_DEVICE_SLOT_SUFFIXED):
			continue
		partition_name = GetBlockDevicePartitionName(block_device) + slot_suffix
		UpdateBlockDevicePartitionName(block_device, partition_name)
		block_device.flags &= ~LP_BLOCK_DEVICE_SLOT_SUFFIXED

	for group in metadata.groups:
		if not (group.flags & LP_GROUP_SLOT_SUFFIXED):
			continue
		group_name = GetPartitionGroupName(group) + slot_suffix
		UpdatePartitionGroupName(group, group_name)
		group.flags &= ~LP_GROUP_SLOT_SUFFIXED

def ReadMetadata(super_partition: str, slot_number: int,
                 opener: IPartitionOpener = None) -> LpMetadata:
	if not opener:
		opener = PartitionOpener()
	
	fd = opener.Open(super_partition, 'rb')

	geometry = ReadLogicalPartitionGeometry(fd)

	if slot_number > geometry.metadata_slot_count:
		raise Exception('invalid metadata slot number')
	
	offsets = [
		GetPrimaryMetadataOffset(geometry, slot_number),
        GetBackupMetadataOffset(geometry, slot_number),
	]
	metadata = None

	for offset in offsets:
		fd.seek(offset, SEEK_SET)
		metadata = ParseMetadata(geometry, fd)
		if metadata:
			break

	if not metadata or not AdjustMetadataForSlot(metadata, slot_number):
		raise Exception('invalid metadata')

	return metadata

def NameFromFixedArray(name: bytes) -> str:
	return name.decode('ascii')

def GetPartitionName(partition: LpMetadataPartition) -> str:
	return NameFromFixedArray(partition.name)

def GetPartitionGroupName(group: LpMetadataPartitionGroup) -> str:
	return NameFromFixedArray(group.name)

def GetBlockDevicePartitionName(block_device: LpMetadataBlockDevice) -> str:
	return NameFromFixedArray(block_device.partition_name)
