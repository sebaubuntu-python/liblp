#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from typing import List

from liblp.include.metadata_format import (
	LpMetadataBlockDevice,
	LpMetadataExtent,
	LpMetadataGeometry,
	LpMetadataHeader,
	LpMetadataPartition,
	LpMetadataPartitionGroup,
)

class LpMetadata:
	def __init__(self,
	             geometry: LpMetadataGeometry = None,
	             header: LpMetadataHeader = None,
	             partitions: List[LpMetadataPartition] = None,
	             extents: List[LpMetadataExtent] = None,
	             groups: List[LpMetadataPartitionGroup] = None,
	             block_devices: List[LpMetadataBlockDevice] = None):
		self.geometry = geometry
		self.header = header
		self.partitions = partitions or []
		self.extents = extents or []
		self.groups = groups or []
		self.block_devices = block_devices or []
