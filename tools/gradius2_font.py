#!/usr/bin/env python3
"""Load exact 8x8 Gradius II (Famicom) glyphs from the user's owned ROM.

Tiles 128..137 are 0..9, and 138..163 are A..Z, in the seventh 4K
CHR-ROM page. Never package this original CHR data in the public repository.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROM_SHA256 = '0f0990bb5410ce292c1e1d0836d3aa8f7aaf415e568bf52acfc3b4a4a27e5701'
EXPECTED_GLYPH_SHA256 = 'c5ebbacfc0b66e13f1899a469154801c1b3337f1db42505fe7f69b0836f20441'
FONT_4K_PAGE = 6
FIRST_TILE = 128
TILE_COUNT = 36


def source_rom(root: Path = ROOT) -> bytes:
    selected = json.loads((root / 'manifests/selected_sources.json').read_text(encoding='utf-8'))
    item = selected['gradius2_fc']
    if item['sha256'] != EXPECTED_ROM_SHA256:
        raise ValueError('Unexpected Gradius II reference in selected_sources.json')
    relative = Path(item['path'])
    if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'private_sources':
        raise ValueError('Refusing unsafe source path')
    raw = (root / relative).read_bytes()
    if len(raw) != 262160 or hashlib.sha256(raw).hexdigest() != EXPECTED_ROM_SHA256:
        raise ValueError('Gradius II Famicom ROM does not match the approved source hash')
    if raw[:4] != b'NES\x1a' or raw[4] != 8 or raw[5] != 16:
        raise ValueError('Unexpected iNES header, 128 KiB PRG / 128 KiB CHR expected')
    return raw


def glyphs(root: Path = ROOT) -> dict[str,bytes]:
    raw = source_rom(root)
    offset = 16 + raw[4] * 16384 + FONT_4K_PAGE * 4096 + FIRST_TILE * 16
    source = raw[offset: offset + TILE_COUNT * 16]
    if hashlib.sha256(source).hexdigest() != EXPECTED_GLYPH_SHA256:
        raise ValueError('Gradius II font tile range differs from verified CHR source')
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = {}
    for i, char in enumerate(chars):
        tile = source[i * 16:i * 16 + 16]
        # Original glyph pixels use CHR bitplane zero (colour 1). Change only
        # colour value to 3 so they are white under the native title palette.
        # The outlines, advance width and geometry remain byte-for-byte shaped
        # after encoding. This is a palette remap, not a drawn imitation font.
        if any(tile[8:]):
            raise ValueError('Font contains unexpected nonzero bitplane 1')
        result[char] = tile[:8] * 2
    result[' '] = bytes(16)
    return result


def shape(tile: bytes) -> list[list[int]]:
    if len(tile) != 16:
        raise ValueError('Expected 8x8 two-plane tile')
    return [[((tile[y]>>(7-x))&1) | (((tile[y+8]>>(7-x))&1)<<1)
             for x in range(8)] for y in range(8)]


if __name__ == '__main__':
    f = glyphs()
    print('Verified original Gradius II font:', len(f)-1, 'glyphs; source SHA256', EXPECTED_GLYPH_SHA256)
