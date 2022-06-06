#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from liblp.images import (
	IsEmptySuperImage as _IsEmptySuperImage,
	WriteToImageFile as _WriteToImageFile,
	ReadFromImageFile as _ReadFromImageFile,
	ReadFromImageBlob as _ReadFromImageBlob,
	WriteSplitImageFiles as _WriteSplitImageFiles,
)
from liblp.liblp import (
	LpMetadata as _LpMetadata,
)
from liblp.reader import (
	ReadMetadata as _ReadMetadata,
	GetPartitionName as _GetPartitionName,
	GetPartitionGroupName as _GetPartitionGroupName,
	GetBlockDevicePartitionName as _GetBlockDevicePartitionName,
)
from liblp.utility import (
	GetMetadataSuperBlockDevice as _GetMetadataSuperBlockDevice,
	GetTotalSuperPartitionSize as _GetTotalSuperPartitionSize,
	GetBlockDevicePartitionNames as _GetBlockDevicePartitionNames,
	SlotNumberForSlotSuffix as _SlotNumberForSlotSuffix,
	SlotSuffixForSlotNumber as _SlotSuffixForSlotNumber,
	GetPartitionSlotSuffix as _GetPartitionSlotSuffix,
	FindPartition as _FindPartition,
	GetPartitionSize as _GetPartitionSize,
)
from liblp.writer import (
	FlashPartitionTable as _FlashPartitionTable,
	UpdatePartitionTable as _UpdatePartitionTable,
)

LpMetadata = _LpMetadata
"""
Helper structure for easily interpreting deserialized metadata, or
re-serializing metadata.
"""

FlashPartitionTable = _FlashPartitionTable
"""
Place an initial partition table on the device. This will overwrite the
existing geometry, and should not be used for normal partition table
updates. False can be returned if the geometry is incompatible with the
block device or an I/O error occurs.
"""

UpdatePartitionTable = _UpdatePartitionTable
"""
Update the partition table for a given metadata slot number. False is
returned if an error occurs, which can include:
 - Invalid slot number.
 - I/O error.
 - Corrupt or missing metadata geometry on disk.
 - Incompatible geometry.
"""

ReadMetadata = _ReadMetadata
"""
Read logical partition metadata from its predetermined location on a block
device. If readback fails, we also attempt to load from a backup copy.
"""

# Helper functions that use the default PartitionOpener.
#FlashPartitionTable = _FlashPartitionTable
#UpdatePartitionTable = _UpdatePartitionTable
#ReadMetadata = _ReadMetadata

IsEmptySuperImage = _IsEmptySuperImage
"""
Returns whether an image is an "empty" image or not. An empty image contains
only metadata. Unlike a flashed block device, there are no reserved bytes or
backup sections, and only one slot is stored (even if multiple slots are
supported). It is a format specifically for storing only metadata.
"""

WriteToImageFile = _WriteToImageFile
"""
Read/Write logical partition metadata and contents to an image file, for
flashing.
"""

#WriteToImageFile = _WriteToImageFile
#WriteToImageFile = _WriteToImageFile
ReadFromImageFile = _ReadFromImageFile
ReadFromImageBlob = _ReadFromImageBlob
"""
Read/Write logical partition metadata to an image file, for producing a
super_empty.img (for fastboot wipe-super/update-super) or for diagnostics.
"""

WriteSplitImageFiles = _WriteSplitImageFiles
"""
Similar to WriteToSparseFile, this will generate an image that can be
flashed to a device directly. However unlike WriteToSparseFile, it
is intended for retrofit devices, and will generate one sparse file per
block device (each named super_<name>.img) and placed in the specified
output folder.
"""

# Helper to extract safe C++ strings from partition info.
GetPartitionName = _GetPartitionName
GetPartitionGroupName = _GetPartitionGroupName
GetBlockDevicePartitionName = _GetBlockDevicePartitionName

GetMetadataSuperBlockDevice = _GetMetadataSuperBlockDevice
"""
Return the block device that houses the super partition metadata; returns
null on failure.
"""

GetTotalSuperPartitionSize = _GetTotalSuperPartitionSize
"""Return the total size of all partitions comprising the super partition."""

GetBlockDevicePartitionNames = _GetBlockDevicePartitionNames
"""Get the list of block device names required by the given metadata."""

# Slot suffix helpers.
SlotNumberForSlotSuffix = _SlotNumberForSlotSuffix
SlotSuffixForSlotNumber = _SlotSuffixForSlotNumber
GetPartitionSlotSuffix = _GetPartitionSlotSuffix

# Helpers for common functions.
FindPartition = _FindPartition
GetPartitionSize = _GetPartitionSize
