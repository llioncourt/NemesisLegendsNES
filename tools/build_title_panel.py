#!/usr/bin/env python3
"""Deterministic native UI tiles. Leaves the approved title art byte-identical."""
from pathlib import Path
import hashlib,json
from gradius2_font import glyphs, EXPECTED_ROM_SHA256, EXPECTED_GLYPH_SHA256
ROOT=Path(__file__).resolve().parents[1]
BANK=24

def tile(pixels):
    return bytes(sum((pixels[y][x]&1)<<(7-x) for x in range(8)) for y in range(8))+bytes(sum(((pixels[y][x]>>1)&1)<<(7-x) for x in range(8)) for y in range(8))

def generate():
    out=ROOT/'assets/title_art';raw=bytearray(4096)
    # True Famicom Gradius II 8x8 glyphs, not the old authored 5x7 imitation.
    # The original ROM stays in the user's private_sources; no CHR binary is
    # published to a public source tree.
    for ch,data in glyphs().items():
        raw[ord(ch)*16:ord(ch)*16+16]=data
    # Border IDs: top-left, top, left, right, top-right, bottom-left, bottom, bottom-right.
    for ident in range(0x80,0x88):
        p=[[0]*8 for _ in range(8)]
        if ident in (0x80,0x81,0x84):p[1]=[2]*8
        if ident in (0x85,0x86,0x87):p[6]=[2]*8
        if ident in (0x80,0x82,0x85):
            for y in range(8):p[y][1]=2
        if ident in (0x84,0x83,0x87):
            for y in range(8):p[y][6]=2
        raw[ident*16:ident*16+16]=tile(p)
    for ident,col in [(0x90,3),(0x91,2)]:
        p=[[0]*8 for _ in range(8)]
        for y in range(1,7):
            for x in range(2,3+min(y-1,6-y)):p[y][x]=col
        raw[ident*16:ident*16+16]=tile(p)
    (out/'panel.chr').write_bytes(raw)
    rows=[];attrs=[]
    for y in range(8):
        row=[32]*20;row[0]=0x82;row[-1]=0x83
        if y==0:row=[0x80]+[0x81]*18+[0x84]
        if y==7:row=[0x85]+[0x86]*18+[0x87]
        attr=[BANK]*20
        if y in (0,7):attr[0]=attr[-1]=BANK|64
        if y in (2,5):attr[2]=BANK|64
        rows+=row;attrs+=attr
    (out/'panel_rows.bin').write_bytes(bytes(rows))
    (out/'panel_attrs.bin').write_bytes(bytes(attrs))
    data=(ROOT/'build/native/graphics.chr').read_bytes()
    if len(data)!=131072:raise ValueError('Unexpected graphics allocation')
    current=data[BANK*4096:(BANK+1)*4096]
    old_bank_sha256='cb00520d9d7f0246b4ab293e3574fa52aa36bfea172a4cb6097b42199605a1c5'
    if any(current) and current!=raw and hashlib.sha256(current).hexdigest()!=old_bank_sha256:
        raise ValueError('UI bank 24 conflicts with unknown CHR; refusing to overwrite')
    data=data[:BANK*4096]+raw+data[(BANK+1)*4096:]
    (ROOT/'build/native/graphics.chr').write_bytes(data)
    report={'bank_4k':BANK,'chr_allocation':4096,'panel_pixels':[48,152,160,64],
        'native_menu_items':['START GAME','OPTIONS'],'hardware_sprites':0,
        'chr_sha256':hashlib.sha256(raw).hexdigest(),'base_art_changed':False,'font_source':'Gradius II (Japan) - Famicom 1988',
        'font_rom_sha256':EXPECTED_ROM_SHA256,'font_source_tile_sha256':EXPECTED_GLYPH_SHA256,
        'font_glyphs':36,'font_chrom_page_4k':6,'font_original_tile_start':128}
    (out/'panel.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Native panel tiles: Gradius II Famicom glyphs, CHR bank 24')
if __name__=='__main__':generate()
