#!/usr/bin/env python3
"""Compile the approved artwork into a real MMC5 extended-attribute background.
No emulation shortcuts: 256x240, four palettes, three opaque colours per 8x8
background tile, deduplicated 2bpp CHR. The menu is drawn by the cartridge.
"""
from __future__ import annotations
import hashlib, json, pathlib
import cv2
import numpy as np
from PIL import Image, ImageFilter
from skimage.color import rgb2lab
from build_native_assets import NES_RGB, encode
from gradius2_font import glyphs, shape, EXPECTED_GLYPH_SHA256
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/title_art'
PALETTE=np.frombuffer(NES_RGB,dtype=np.uint8).reshape(64,3)

def prepare():
    im=Image.open(OUT/'approved.png').convert('RGB')
    if im.size != (1448,1086):
        raise ValueError('Expected the exact approved 1448x1086 composition')
    im=im.resize((1408,1056),Image.Resampling.LANCZOS)
    a=np.array(im);mask=np.zeros(a.shape[:2],np.uint8)
    # Remove baked menu/cursor so native text can be positioned and selected.
    # This is a local build-time repair, not regeneration of the scene or ship.
    for x0,y0,x1,y1 in [(559,700,810,745),(560,749,845,791),
                         (559,795,930,838),(560,840,786,884),
                         (507,703,553,752),(516,982,899,1024)]:
        part=a[y0:y1,x0:x1].astype(np.int16)
        white=(part.min(2)>115)&(part.max(2)-part.min(2)<95)
        if x0==507:white|=(part[:,:,0]>150)&(part[:,:,1]<120)
        local=np.zeros(mask.shape,np.uint8);local[y0:y1,x0:x1]=white*255
        local=cv2.dilate(local,np.ones((11,11),np.uint8))
        mask|=local
    repaired=cv2.inpaint(a,mask,9,cv2.INPAINT_TELEA)
    im=Image.fromarray(repaired).resize((256,240),Image.Resampling.LANCZOS)
    im=im.filter(ImageFilter.UnsharpMask(radius=.55,percent=115,threshold=3))
    im.save(OUT/'native_colour_reference.png')
    return im

def compile_art():
    OUT.mkdir(exist_ok=True,parents=True)
    im=prepare();a=np.array(im)
    # Tile-colour optimisation, keeping the shared backdrop physically black.
    pixels=rgb2lab(a/255.).reshape(30,8,32,8,3).transpose(0,2,1,3,4).reshape(960,64,3)
    neslab=rgb2lab(PALETTE[None,:,:]/255.)[0]
    # Modest lightness emphasis retains ship silhouettes and lettering.
    weights=np.array([1.25,1.0,1.0]);dist=(((pixels[:,:,None,:]-neslab[None,None,:,:])*weights)**2).sum(3).astype(np.float32)
    # Separate blue/white, fire, stone and alien-biology colour families.
    pals=[[15,1,17,48],[15,6,22,39],[15,0,23,55],[15,4,20,52]]
    pools=[[[1,2,12],[17,18,33,34]],[[5,6,7],[21,22,23],[38,39,55]],
           [[0,7,8],[16,23,24],[48,55,61]],[[3,4,5],[19,20,21],[36,37,52]]]
    def costs(ps):return np.stack([dist[:,:,p].min(2).sum(1) for p in ps])
    # Coordinate descent assigns palettes per tile and refines actual NES indices.
    for epoch in range(4):
        for i in range(4):
            for k,choices in enumerate(pools[i],1):
                old=pals[i][k];best=costs(pals).min(0).sum();choice=old
                for val in choices:
                    pals[i][k]=val;err=costs(pals).min(0).sum()
                    if err<best:best=float(err);choice=val
                pals[i][k]=choice
    # Native text always uses colour 3 (white) in palette zero.
    pals[0][3]=48
    cc=costs(pals)
    tilepal=cc.argmin(0)
    # Avoid magenta spill onto the cool logo/ship when a tile crosses a glow.
    for ty in range(4,9):
        for tx in range(3,29):
            i=ty*32+tx;tilepal[i]=0 if cc[0,i]<=cc[2,i] else 2
    for ty in range(12,18):
        for tx in range(13,31):
            i=ty*32+tx
            if tx<22:tilepal[i]=0 if cc[0,i]<=cc[2,i] else 2
    ids=np.zeros((240,256),np.uint8)
    for i,p in enumerate(tilepal):
        ty,tx=divmod(i,32);local=dist[i][:,pals[p]].argmin(1).reshape(8,8)
        ids[ty*8:ty*8+8,tx*8:tx*8+8]=local
    # Recompose native footer using the ACTUAL Gradius II Famicom letter shapes.
    # Keep all underlying scene pixels; no black bar or all-zero rectangle.
    # The source's old menu labels were already inpainted above. Earlier builds
    # zero-filled rows 20,22,24 and y=224..239, producing rectangular holes.
    # Both operations are deliberately removed here.
    fnt=glyphs()
    credit='2026 SILICON FORGE'
    x=(256-len(credit)*8)//2
    y=224
    for ch in credit:
        for dy,rowv in enumerate(shape(fnt[ch])):
            for dx,value in enumerate(rowv):
                if value:ids[y+dy,x+dx]=3
        tilepal[(y//8)*32+(x//8)]=0
        x+=8
    # Do not install any baked menu labels in the base nametable: native_title.s
    # reveals a separate opaque panel through its bounded VBlank queue.
    tiles=[bytes(16)];lookup={tiles[0]:0};nt=bytearray();ext=bytearray()
    # New art starts at bank 19, after existing gameplay assets, without
    # relocating any of the first game's terrain, sprites or Big Core.
    for i,p in enumerate(tilepal):
        ty,tx=divmod(i,32);raw=encode(ids[ty*8:ty*8+8,tx*8:tx*8+8])
        if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
        n=lookup[raw];nt.append(n&255);ext.append((int(p)<<6)|(19+(n>>8)))
    raw=b''.join(tiles);chrdata=raw+bytes((-len(raw))%4096)
    if len(chrdata)>4*4096:raise ValueError('Art exceeds four reserved CHR banks')
    (OUT/'background.chr').write_bytes(chrdata)
    (OUT/'title.nam').write_bytes(bytes(nt)+bytes(64))
    (OUT/'title.exram').write_bytes(bytes(ext)+bytes(64))
    (OUT/'title.pal').write_bytes(bytes(c for p in pals for c in p))
    # Simple 8x16 red/white cursor in an independent sprite bank.
    idx=np.zeros((16,8),np.uint8)
    for yy in range(1,12):
        width=5-abs(6-yy)
        idx[yy,1:2+width]=1
        if width>1:idx[yy,2:1+width]=2
    cursor=encode(idx[:8])+encode(idx[8:]);(OUT/'cursor.chr').write_bytes(cursor.ljust(1024,b'\0'))
    (OUT/'title.inc').write_text('TitleArtBank = 19\nTitleCursorBank = 92\n')
    report=dict(source_sha256=hashlib.sha256((OUT/'approved.png').read_bytes()).hexdigest(),
        dimensions=[256,240],mode='MMC5 extended attributes',palette_indices=pals,
        unique_tiles=len(tiles),chr_payload_bytes=len(raw),chr_allocated_bytes=len(chrdata),
        bg_4k_base=19,cursor_1k_bank=92,background_colours=len(set(c for p in pals for c in p)),
        per_tile_opaque_colours=3,nametable_bytes=1024,exram_bytes=1024,
        transformation='Downsample approved composition; remove baked UI by local inpainting; preserve underlying quantized scenery and add Gradius II native credit glyphs, no zero-filled menu/credit holes.',
        fidelity='Lossy 256x240 NES conversion, not pixel-identical to the high-resolution reference.',
        menu_items=[],credit=credit,font_source='Gradius II (Japan) Famicom',font_source_tile_sha256=EXPECTED_GLYPH_SHA256,
        base_menu_rows_zero_filled=False,base_footer_zero_filled=False)
    (OUT/'title.json').write_text(json.dumps(report,indent=2)+'\n')
    # An asset preview only. The final evidence must be captured from the ROM.
    result=np.zeros((240,256,3),np.uint8)
    for i,p in enumerate(tilepal):
        ty,tx=divmod(i,32);result[ty*8:ty*8+8,tx*8:tx*8+8]=PALETTE[np.array(pals[p])[ids[ty*8:ty*8+8,tx*8:tx*8+8]]]
    Image.fromarray(result).resize((768,720),Image.Resampling.NEAREST).save(OUT/'background_preview.png')
    print(json.dumps(report,indent=2))
if __name__=='__main__':compile_art()
