#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from argparse import ArgumentParser
from io import BufferedReader
from pathlib import Path
from typing import Dict, List

from liblp import (
	LP_SECTOR_SIZE,
	LP_TARGET_TYPE_LINEAR,
	LpMetadata,
	LpMetadataPartition,
	GetPartitionName,
	ReadMetadata,
)

class ImageExtractor:
	def __init__(self,
	             image_fd: BufferedReader,
	             metadata: LpMetadata,
	             partitions: List[str],
	             output_dir: str):
		self.image_fd = image_fd
		self.metadata = metadata
		self.partitions = partitions or []
		self.output_dir = output_dir

		self.partition_map: Dict[str, LpMetadataPartition] = {}

	def Extract(self):
		self.BuildPartitionList()

		for _, info in self.partition_map.items():
			self.ExtractPartition(info)

	def BuildPartitionList(self):
		extract_all = not self.partitions

		for partition in self.metadata.partitions:
			name = GetPartitionName(partition)
			if extract_all or name in self.partitions:
				self.partition_map[name] = partition
				if name in self.partitions:
					self.partitions.remove(name)

		if not extract_all and self.partitions:
			raise Exception(f"Partitions not found: {self.partitions}")

	def ExtractPartition(self, partition: LpMetadataPartition):
		# Validate the extents and find the total image size.
		total_size = 0
		for i in range(partition.num_extents):
			index = partition.first_extent_index + i
			extent = self.metadata.extents[index]

			if extent.target_type != LP_TARGET_TYPE_LINEAR:
				raise Exception(f"Unsupported target type in extent: {extent.target_type}")
			if extent.target_source != 0:
				raise Exception("Split super devices are not supported.")
			total_size += extent.num_sectors * LP_SECTOR_SIZE

		with (self.output_dir / f"{GetPartitionName(partition)}.img").open('wb') as output_fd:
			block_size = self.metadata.geometry.logical_block_size
			for i in range(partition.num_extents):
				index = partition.first_extent_index + i
				extent = self.metadata.extents[index]

				super_offset = extent.target_data * LP_SECTOR_SIZE
				self.image_fd.seek(super_offset)

				remaining_bytes = extent.num_sectors * LP_SECTOR_SIZE
				while remaining_bytes:
					if remaining_bytes < block_size:
						raise Exception("extent is not block-aligned")

					output_fd.write(self.image_fd.read(block_size))

					remaining_bytes -= block_size

def lpunpack(image: Path, output: Path = Path('.'),
             partitions: List[str] = None, slot: int = 0):
	with image.open('rb') as image_fd:
		metadata = ReadMetadata(image, slot)

		extractor = ImageExtractor(image_fd, metadata, partitions, output)
		extractor.Extract()

def main():
	parser = ArgumentParser(description='command-line tool for extracting partition images from super')
	parser.add_argument('image', help='Super image path', type=Path)
	parser.add_argument('-o', '--output', help='Output directory (default is current dir)', type=Path, default=Path('.'))
	parser.add_argument('-p', '--partition', help='Extract the named partition. This can be specified multiple times.', action='append')
	parser.add_argument('-S', '--slot', help='Slot number (default is 0).', type=int, default=0)
	args = parser.parse_args()

	lpunpack(args.image, args.output, args.partition, args.slot)

if __name__ == '__main__':
	main()
