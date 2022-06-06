#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from enum import Enum

# By default, partitions are aligned on a 1MiB boundary.
kDefaultPartitionAlignment = 1024 * 1024
kDefaultBlockSize = 4096

# Name of the default group in a metadata.
kDefaultGroup = "default"

class ExtentType(Enum):
	kZero = 0
	kLinear = 1
