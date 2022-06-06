#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from ctypes import (
	Structure,
	c_char,
	c_uint8,
	c_uint16,
	c_uint32,
	c_uint64,
)

# Magic signature for LpMetadataGeometry.
LP_METADATA_GEOMETRY_MAGIC = 0x616c4467

# Space reserved for geometry information.
LP_METADATA_GEOMETRY_SIZE = 4096

# Magic signature for LpMetadataHeader.
LP_METADATA_HEADER_MAGIC = 0x414C5030

# Current metadata version.
LP_METADATA_MAJOR_VERSION = 10
LP_METADATA_MINOR_VERSION_MIN = 0
LP_METADATA_MINOR_VERSION_MAX = 2

# Metadata version needed to use the UPDATED partition attribute.
LP_METADATA_VERSION_FOR_UPDATED_ATTR = 1

# Metadata version needed for the new expanded header struct.
LP_METADATA_VERSION_FOR_EXPANDED_HEADER = 2

"""
Attributes for the LpMetadataPartition::attributes field.

READONLY - The partition should not be considered writable. When used with
device mapper, the block device will be created as read-only.
"""
LP_PARTITION_ATTR_NONE = 0x0
LP_PARTITION_ATTR_READONLY = (1 << 0)

"""
This flag is only intended to be used with super_empty.img and super.img on
retrofit devices. On these devices there are A and B super partitions, and
we don't know ahead of time which slot the image will be applied to.

If set, the partition name needs a slot suffix applied. The slot suffix is
determined by the metadata slot number (0 = _a, 1 = _b).
"""
LP_PARTITION_ATTR_SLOT_SUFFIXED = (1 << 1)

"""
This flag is applied automatically when using MetadataBuilder::NewForUpdate.
It signals that the partition was created (or modified) for a snapshot-based
update. If this flag is not present, the partition was likely flashed via
fastboot.
"""
LP_PARTITION_ATTR_UPDATED = (1 << 2)

# This flag marks a partition as disabled. It should not be used or mapped.
LP_PARTITION_ATTR_DISABLED = (1 << 3)

"""
Mask that defines all valid attributes. When changing this, make sure to
update ParseMetadata().
"""
LP_PARTITION_ATTRIBUTE_MASK_V0 = \
	(LP_PARTITION_ATTR_READONLY | LP_PARTITION_ATTR_SLOT_SUFFIXED)
LP_PARTITION_ATTRIBUTE_MASK_V1 = (LP_PARTITION_ATTR_UPDATED | LP_PARTITION_ATTR_DISABLED)
LP_PARTITION_ATTRIBUTE_MASK = \
	(LP_PARTITION_ATTRIBUTE_MASK_V0 | LP_PARTITION_ATTRIBUTE_MASK_V1)

"""
Default name of the physical partition that holds logical partition entries.
The layout of this partition will look like:

	+--------------------+
	| Disk Geometry      |
	+--------------------+
	| Geometry Backup    |
	+--------------------+
	| Metadata           |
	+--------------------+
	| Backup Metadata    |
	+--------------------+
	| Logical Partitions |
	+--------------------+
"""
LP_METADATA_DEFAULT_PARTITION_NAME = "super"

# Size of a sector is always 512 bytes for compatibility with the Linux kernel.
LP_SECTOR_SIZE = 512

"""
Amount of space reserved at the start of every super partition to avoid
creating an accidental boot sector.
"""
LP_PARTITION_RESERVED_BYTES = 4096

"""
This structure is stored at block 0 in the first 4096 bytes of the
partition, and again in the following block. It is never modified and
describes how logical partition information can be located.
"""
class LpMetadataGeometry(Structure):
	_fields_ = [
		# 0: Magic signature (LP_METADATA_GEOMETRY_MAGIC).
		("magic", c_uint32),

		# 4: Size of the LpMetadataGeometry struct.
		("struct_size", c_uint32),

		# 8: SHA256 checksum of this struct, with this field set to 0.
		("checksum", c_uint8 * 32),

		# 40: Maximum amount of space a single copy of the metadata can use. This
		# must be a multiple of LP_SECTOR_SIZE.
		("metadata_max_size", c_uint32),

		# 44: Number of copies of the metadata to keep. For A/B devices, this
		# will be 2. For an A/B/C device, it would be 3, et cetera. For Non-A/B
		# it will be 1. A backup copy of each slot is kept, so if this is "2",
		# there will be four copies total.
		("metadata_slot_count", c_uint32),

		# 48: Logical block size. This is the minimal alignment for partition and
		# extent sizes, and it must be a multiple of LP_SECTOR_SIZE. Note that
  		# this must be equal across all LUNs that comprise the super partition,
   		# and thus this field is stored in the geometry, not per-device.
		("logical_block_size", c_uint32),
	]
	_pack_ = 1

"""
The logical partition metadata has a number of tables; they are described
in the header via the following structure.

The size of the table can be computed by multiplying entry_size by
num_entries, and the result must not overflow a 32-bit signed integer.
"""
class LpMetadataTableDescriptor(Structure):
	_fields_ = [
		# 0: Location of the table, relative to end of the metadata header.
		("offset", c_uint32),
		# 4: Number of entries in the table.
		("num_entries", c_uint32),
		# 8: Size of each entry in the table, in bytes.
		("entry_size", c_uint32),
	]
	_pack_ = 1

"""
Binary format for the header of the logical partition metadata format.

The format has three sections. The header must occur first, and the
proceeding tables may be placed in any order after.

 +-----------------------------------------+
 | Header data - fixed size                |
 +-----------------------------------------+
 | Partition table - variable size         |
 +-----------------------------------------+
 | Partition table extents - variable size |
 +-----------------------------------------+

The "Header" portion is described by LpMetadataHeader. It will always
precede the other three blocks.

All fields are stored in little-endian byte order when serialized.

This struct is versioned; see the |major_version| and |minor_version|
fields.
"""
class LpMetadataHeader(Structure):
	_fields_ = [
		# 0: Four bytes equal to LP_METADATA_HEADER_MAGIC.
		("magic", c_uint32),

		# 4: Version number required to read this metadata. If the version is not
		# equal to the library version, the metadata should be considered
		# incompatible.
		("major_version", c_uint16),

		# 6: Minor version. A library supporting newer features should be able to
		# read metadata with an older minor version. However, an older library
		# should not support reading metadata if its minor version is higher.
		("minor_version", c_uint16),

		# 8: The size of this header struct.
		("header_size", c_uint32),

		# 12: SHA256 checksum of the header, up to |header_size| bytes, computed as
    	# if this field were set to 0.
		("header_checksum", c_uint8 * 32),

		# 44: The total size of all tables. This size is contiguous; tables may not
    	# have gaps in between, and they immediately follow the header.
		("tables_size", c_uint32),

		# 48: SHA256 checksum of all table contents.
		("tables_checksum", c_uint8 * 32),

		# 80: Partition table descriptor.
		("partitions", LpMetadataTableDescriptor),
		# 92: Extent table descriptor.
		("extents", LpMetadataTableDescriptor),
		# 104: Updateable group descriptor.
		("groups", LpMetadataTableDescriptor),
		# 116: Block device table.
		("block_devices", LpMetadataTableDescriptor),

		# Everything past here is header version 1.2+, and is only included if
		# needed. When liblp supporting >= 1.2 reads a < 1.2 header, it must
		# zero these additional fields.

		# See LP_HEADER_FLAG_ constants for possible values. Header flags are
		# independent of the version number and intended to be informational only.
		# New flags can be added without bumping the version.
		("flags", c_uint32),

		# 132: Reserved (zero), pad to 256 bytes.
		("reserved", c_uint8 * 124),
	]
	_pack_ = 1

"""
This device uses Virtual A/B. Note that on retrofit devices, the expanded
header may not be present.
"""
LP_HEADER_FLAG_VIRTUAL_AB_DEVICE = 0x1

"""
This struct defines a logical partition entry, similar to what would be
present in a GUID Partition Table.
"""
class LpMetadataPartition(Structure):
	_fields_ = [
		# 0: Name of this partition in ASCII characters. Any unused characters in
		# the buffer must be set to 0. Characters may only be alphanumeric or _.
		# The name must include at least one ASCII character, and it must be unique
		# across all partition names. The length (36) is the same as the maximum
		# length of a GPT partition name.
		("name", c_char * 36),

		# 36: Attributes for the partition (see LP_PARTITION_ATTR_* flags above).
		("attributes", c_uint32),

		# 40: Index of the first extent owned by this partition. The extent will
    	# start at logical sector 0. Gaps between extents are not allowed.
		("first_extent_index", c_uint32),

		# 44: Number of extents in the partition. Every partition must have at
    	# least one extent.
		("num_extents", c_uint32),

		# 48: Group this partition belongs to.
		("group_index", c_uint32),
	]
	_pack_ = 1

"""
This extent is a dm-linear target, and the index is an index into the
LinearExtent table.
"""
LP_TARGET_TYPE_LINEAR = 0

# This extent is a dm-zero target. The index is ignored and must be 0.
LP_TARGET_TYPE_ZERO = 1

# This struct defines an extent entry in the extent table block.
class LpMetadataExtent(Structure):
	_fields_ = [
		# 0: Length of this extent, in 512-byte sectors.
		("num_sectors", c_uint64),

		# 8: Target type for device-mapper (see LP_TARGET_TYPE_* values).
		("target_type", c_uint32),

		# 12: Contents depends on target_type.
		#
		# LINEAR: The sector on the physical partition that this extent maps onto.
		# ZERO: This field must be 0.
		("target_data", c_uint64),

		# 20: Contents depends on target_type.
		#
		# LINEAR: Must be an index into the block devices table.
		# ZERO: This field must be 0.
		("target_source", c_uint32),
	]
	_pack_ = 1

"""
This struct defines an entry in the groups table. Each group has a maximum
size, and partitions in a group must not exceed that size. There is always
a "default" group of unlimited size, which is used when not using update
groups or when using overlayfs or fastbootd.
"""
class LpMetadataPartitionGroup(Structure):
	_fields_ = [
		# 0: Name of this group. Any unused characters must be 0.
		("name", c_char * 36),

		# 36: Flags (see LP_GROUP_*).
		("flags", c_uint32),

		# 40: Maximum size in bytes. If 0, the group has no maximum size.
		("maximum_size", c_uint64),
	]
	_pack_ = 1

"""
This flag is only intended to be used with super_empty.img and super.img on
retrofit devices. If set, the group needs a slot suffix to be interpreted
correctly. The suffix is automatically applied by ReadMetadata().
"""
LP_GROUP_SLOT_SUFFIXED = (1 << 0)

"""
This struct defines an entry in the block_devices table. There must be at
least one device, and the first device must represent the partition holding
the super metadata.
"""
class LpMetadataBlockDevice(Structure):
	_fields_ = [
		# 0: First usable sector for allocating logical partitions. this will be
		# the first sector after the initial geometry blocks, followed by the
		# space consumed by metadata_max_size*metadata_slot_count*2.
		("first_logical_sector", c_uint64),

		# 8: Alignment for defining partitions or partition extents. For example,
		# an alignment of 1MiB will require that all partitions have a size evenly
		# divisible by 1MiB, and that the smallest unit the partition can grow by
		# is 1MiB.
		#
		# Alignment is normally determined at runtime when growing or adding
		# partitions. If for some reason the alignment cannot be determined, then
		# this predefined alignment in the geometry is used instead. By default
		# it is set to 1MiB.
		("alignment", c_uint32),

		# 12: Alignment offset for "stacked" devices. For example, if the "super"
		# partition itself is not aligned within the parent block device's
		# partition table, then we adjust for this in deciding where to place
		# |first_logical_sector|.
		#
		# Similar to |alignment|, this will be derived from the operating system.
		# If it cannot be determined, it is assumed to be 0.
		("alignment_offset", c_uint32),

		# 16: Block device size, as specified when the metadata was created. This
		# can be used to verify the geometry against a target device.
		("size", c_uint64),

		# 24: Partition name in the GPT. Any unused characters must be 0.
		("partition_name", c_char * 36),

		# 60: Flags (see LP_BLOCK_DEVICE_* flags below).
		("flags", c_uint32),
	]
	_pack_ = 1

"""
This flag is only intended to be used with super_empty.img and super.img on
retrofit devices. On these devices there are A and B super partitions, and
we don't know ahead of time which slot the image will be applied to.

If set, the block device needs a slot suffix applied before being used with
IPartitionOpener. The slot suffix is determined by the metadata slot number
(0 = _a, 1 = _b).
"""
LP_BLOCK_DEVICE_SLOT_SUFFIXED = (1 << 0)

"""
For ease of writing compatibility checks, the original metadata header is
preserved below, and typedefs are provided for the current version.
"""
class LpMetadataHeaderV1_0(Structure):
	_fields_ = [
		("magic", c_uint32),
		("major_version", c_uint16),
		("minor_version", c_uint16),
		("header_size", c_uint32),
		("header_checksum", c_uint8 * 32),
		("tables_size", c_uint32),
		("tables_checksum", c_uint8 * 32),
		("partitions", LpMetadataTableDescriptor),
		("extents", LpMetadataTableDescriptor),
		("groups", LpMetadataTableDescriptor),
		("block_devices", LpMetadataTableDescriptor),
	]
	_pack_ = 1

LpMetadataHeaderV1_2 = LpMetadataHeader
