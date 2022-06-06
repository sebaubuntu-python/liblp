#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from liblp.partition_opener import IPartitionOpener
from liblp.liblp import LpMetadata

def FlashPartitionTable(super_partition: str, metadata: LpMetadata,
                        opener: IPartitionOpener = None) -> bool:
	raise NotImplementedError

def UpdatePartitionTable(super_partition: str, metadata: LpMetadata, slot_number: int,
                         opener: IPartitionOpener = None) -> bool:
	raise NotImplementedError
