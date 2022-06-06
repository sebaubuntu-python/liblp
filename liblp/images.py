#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: Apache-2.0
#

from typing import Dict

from liblp.liblp import LpMetadata

def IsEmptySuperImage(file: str) -> bool:
	raise NotImplementedError

def ReadFromImageFile(image_file: str) -> LpMetadata:
	raise NotImplementedError

def ReadFromImageBlob(data: bytes) -> LpMetadata:
	"""
	Note: signature should have been
	ReadFromImageBlob(data: bytes, bytes: int) -> LpMetadata
	but we don't need size in Python
	"""
	raise NotImplementedError

def WriteToImageFile(file: str, metadata: LpMetadata, block_size: int,
                     images: Dict[str, str], sparsify: bool) -> bool:
	raise NotImplementedError

def WriteSplitImageFiles(output_dir: str, metadata: LpMetadata,
                         block_size: int, images: Dict[str, str],
                         sparsify: bool) -> bool:
	raise NotImplementedError
