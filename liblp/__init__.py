#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""
Android logical partitions library.

As of commit 1e7af8d97552fbf536116a5445f45b6251627b54 (master)
AOSP link: https://github.com/aosp-mirror/platform_system_core/tree/master/fs_mgr/liblp
"""

from pathlib import Path

__version__ = "1.0.1"

module_path = Path(__file__).parent
current_path = Path.cwd()

from liblp.include.liblp import *
from liblp.include.metadata_format import *
from liblp.include.partition_opener import *
