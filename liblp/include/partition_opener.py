#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from liblp.partition_opener import (
	BlockDeviceInfo as _BlockDeviceInfo,
	IPartitionOpener as _IPartitionOpener,
	PartitionOpener as _PartitionOpener,
)

BlockDeviceInfo = _BlockDeviceInfo

IPartitionOpener = _IPartitionOpener

PartitionOpener = _PartitionOpener
