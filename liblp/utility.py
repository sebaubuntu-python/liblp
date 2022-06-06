#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from ctypes import sizeof
from io import BufferedIOBase
from typing import List

from liblp.include.metadata_format import (
	LP_METADATA_GEOMETRY_SIZE,
	LP_PARTITION_RESERVED_BYTES,
	LpMetadataBlockDevice,
	LpMetadataGeometry,
	LpMetadataPartition,
	LpMetadataPartitionGroup,
)
from liblp.liblp import LpMetadata

def GetDescriptorSize(fd: BufferedIOBase, size: int):
	raise NotImplementedError

def GetPrimaryGeometryOffset() -> int:
	return LP_PARTITION_RESERVED_BYTES

def GetBackupGeometryOffset() -> int:
	return GetPrimaryGeometryOffset() + LP_METADATA_GEOMETRY_SIZE

def GetPrimaryMetadataOffset(geometry: LpMetadataGeometry, slot_number: int) -> int:
	assert slot_number < geometry.metadata_slot_count
	offset = (LP_PARTITION_RESERVED_BYTES + (LP_METADATA_GEOMETRY_SIZE * 2) +
	          geometry.metadata_max_size * slot_number)
	return offset

def GetBackupMetadataOffset(geometry: LpMetadataGeometry, slot_number: int) -> int:
	assert slot_number < geometry.metadata_slot_count
	start = (LP_PARTITION_RESERVED_BYTES + (LP_METADATA_GEOMETRY_SIZE * 2) +
	         geometry.metadata_max_size * geometry.metadata_slot_count)
	return start + (geometry.metadata_max_size * slot_number)

def GetTotalMetadataSize(metadata_max_size: int, max_slots: int) -> int:
	return (LP_PARTITION_RESERVED_BYTES +
	        (LP_METADATA_GEOMETRY_SIZE + metadata_max_size * max_slots) * 2)

def GetMetadataSuperBlockDevice(metadata: LpMetadata) -> LpMetadataBlockDevice:
	return metadata.block_devices[0]

def SlotNumberForSlotSuffix(suffix: str) -> int:
	raise NotImplementedError

def GetTotalSuperPartitionSize(metadata: LpMetadata) -> int:
	raise NotImplementedError

def GetBlockDevicePartitionNames(metadata: LpMetadata) -> List[str]:
	raise NotImplementedError

def FindPartition(metadata: LpMetadata, name: str) -> LpMetadataPartition:
	raise NotImplementedError

def GetPartitionSize(metadata: LpMetadata, partition: LpMetadataPartition) -> int:
	raise NotImplementedError

def GetPartitionSlotSuffix(partition_name: str) -> str:
	raise NotImplementedError

def SlotSuffixForSlotNumber(slot_number: int) -> str:
	assert slot_number in [0, 1], \
		f"Slot number must be 0 or 1, not {slot_number}"
	return "_a" if slot_number == 0 else "_b"

def UpdateBlockDevicePartitionName(device: LpMetadataBlockDevice, name: str):
	assert len(name) + 1 <= sizeof(device.name)
	device.name = name

def UpdatePartitionGroupName(group: LpMetadataPartitionGroup, name: str):
	assert len(name) + 1 <= sizeof(group.name)
	group.name = name

def UpdatePartitionName(partition: LpMetadataPartition, name: str):
	assert len(name) + 1 <= sizeof(partition.name)
	partition.name = name

def SetBlockReadonly(fd: BufferedIOBase, readonly: bool):
	raise NotImplementedError

def GetControlFileOrOpen(path: str, flags: int):
	raise NotImplementedError

def UpdateMetadataForInPlaceSnapshot(metadata: LpMetadata, source_slot_number: int,
                                     target_slot_number: int):
	raise NotImplementedError

def ToHexString(value: int):
	raise NotImplementedError

def SetMetadataHeaderV0(metadata: LpMetadata):
	raise NotImplementedError
