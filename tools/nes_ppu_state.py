#!/usr/bin/env python3
"""Read the full PPU state of a running NES game from the FCEUmm savestate.

FCEUmm exposes only CPU RAM through the libretro memory API. Its savestate,
however, carries the nametables (NTAR), palette (PRAM), OAM (SPRA), PPU
registers (PPUR) and, for CHR-RAM boards such as Life Force and Salamander
(Famicom), the pattern RAM (CHRR). This module parses those chunks so the
asset catalogue can capture what a CHR-RAM game really has on screen.

Reference-capture tool: reads private originals, writes private captures.

    from nes_test_host import NES
    from nes_ppu_state import ppu_state
    with NES(core, rom) as nes:
        nes.run(600)
        st = ppu_state(nes)   # dict: ram, ntar, pram, spra, ppur, chrr (if any), mapper chunks
"""
from __future__ import annotations
import ctypes as C, struct

SECTIONS = {1: 'cpu', 2: 'cpuc', 3: 'ppu', 4: 'ctlr', 5: 'snd', 16: 'mapper'}

def serialize(nes) -> bytes:
    lib = nes.lib
    lib.retro_serialize_size.argtypes = []; lib.retro_serialize_size.restype = C.c_size_t
    lib.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]; lib.retro_serialize.restype = C.c_bool
    size = lib.retro_serialize_size()
    buf = C.create_string_buffer(size)
    if not lib.retro_serialize(buf, size): raise RuntimeError('FCEUmm serialize failed')
    return buf.raw

def parse(raw: bytes) -> dict:
    if raw[:3] != b'FCS': raise ValueError('Not an FCEU savestate')
    out, p = {}, 16
    while p + 5 <= len(raw):
        sec = raw[p]; size = struct.unpack_from('<I', raw, p + 1)[0]; p += 5; end = p + size
        q = p
        while q + 8 <= end:
            name = raw[q:q + 4].rstrip(b'\0').decode('latin-1')
            n = struct.unpack_from('<I', raw, q + 4)[0]
            out['%s.%s' % (SECTIONS.get(sec, sec), name)] = raw[q + 8:q + 8 + n]
            q += 8 + n
        p = end
    return out

def ppu_state(nes) -> dict:
    s = parse(serialize(nes))
    st = {'ram': s.get('cpu.RAM'), 'ntar': s.get('ppu.NTAR'), 'pram': s.get('ppu.PRAM'),
          'spra': s.get('ppu.SPRA'), 'ppur': s.get('ppu.PPUR'), 'chrr': s.get('mapper.CHRR')}
    st['mapper'] = {k[7:]: v for k, v in s.items() if k.startswith('mapper.') and k != 'mapper.CHRR'}
    return st

def sprite_height(ppur: bytes) -> int:
    return 16 if ppur[0] & 0x20 else 8

def oam_entries(spra: bytes):
    """[(y, tile, attr, x)] for the 64 OAM slots (y+1 is the screen row)."""
    return [tuple(spra[i:i + 4]) for i in range(0, 256, 4)]
