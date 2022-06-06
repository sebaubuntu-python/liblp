#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from io import BufferedIOBase

class BlockDeviceInfo:
	def __init__(self,
				 partition_name: str = "",
				 size: int = 0,
				 alignment: int = 0,
				 alignment_offset: int = 0,
				 logical_block_size: int = 0):
		# The physical partition name for this block device, as it would appear in
		# the GPT or under /dev/block/by-name.
		self.partition_name = partition_name
		# Size of the block device, in bytes.
		self.size = size
		# Optimal target alignment, in bytes. Partition extents will be aligned to
		# this value by default. This value must be 0 or a multiple of 512.
		self.alignment = alignment
		# Alignment offset to parent device (if any), in bytes. The sector at
		# |alignment_offset| on the target device is correctly aligned on its
		# parent device. This value must be 0 or a multiple of 512.
		self.alignment_offset = alignment_offset
		# Block size, for aligning extent sizes and partition sizes.
		self.logical_block_size = logical_block_size

class IPartitionOpener:
	"""Test-friendly interface for interacting with partitions."""
	def Open(self, partition_name: str, flags: int) -> BufferedIOBase:
		"""
		Open the given named physical partition with the provided open() flags.
		The name can be an absolute path if the full path is already known.
		"""
		raise NotImplementedError
	
	def GetInfo(self, partition_name: str) -> BlockDeviceInfo:
		"""
		Return block device information about the given named physical partition.
		The name can be an absolute path if the full path is already known.

		Note: Signature should have been
		GetInfo(self, partition_name: str, info: BlockDeviceInfo) -> bool

		For obvious reasons, we directly return a BlockDeviceInfo
		object or None if it failed.
		"""
		raise NotImplementedError

	def GetDeviceString(self, partition_name: str) -> str:
		"""
		Return a path that can be used to pass the block device to device-mapper.
		This must either result in an absolute path, or a major:minor device
		sequence.
		"""
		raise NotImplementedError

class PartitionOpener(IPartitionOpener):
	"""
	Helper class to implement IPartitionOpener. If |partition_name| is not an
	absolute path, /dev/block/by-name/ will be prepended.
	"""
	def Open(self, partition_name: str, flags: int) -> BufferedIOBase:
		return open(partition_name, flags)

	def GetInfo(self, partition_name: str) -> BlockDeviceInfo:
		return None # TODO

	def GetDeviceString(self, partition_name: str) -> str:
		return partition_name
