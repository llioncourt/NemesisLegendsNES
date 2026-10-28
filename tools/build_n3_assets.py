#!/usr/bin/env python3
"""Nemesis 3 maps -> native stage descriptors (Frente F, chapter 4 structure).

Same descriptor layout as the Nemesis/Nemesis 2 descriptors. Nemesis 3 maps are
re-blocked from the extracted 22-row terrain into 4x4 character pieces (six per
four-column group, the engine's column format); every map has at most 141
distinct pieces. Static terrain, palettes and the map's 64 hardware sprite
frames only. Writes build/native/n3_map_NN.bin (11), n3_maps_a/b.bin,
n3_graphics.chr and n3_assets.json. CHR banks follow the chapter-2 graphics.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib,struct,sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_native_assets import encode,msxtile,palettes,NEAREST,DIST
SRC=ROOT/'assets/msx/nemesis3';OUT=ROOT/'build/native'
MAPS_A_BANK=0x80|39;MAPS_B_BANK=0x80|40
def main():
    n2=json.loads((OUT/'n2_assets.json').read_text())
    chr_base=n2['chr_base_bank']+n2['chr_4k_banks']
    chrdata=bytearray();dictionary={}
    def addtile(raw):
        if raw not in dictionary:dictionary[raw]=len(chrdata)//16;chrdata.extend(raw)
        return dictionary[raw]
    maps_a=bytearray();maps_b=bytearray();report=[];sheets=[]
    for st in range(1,12):
        folder=SRC/('map_%02d'%st);meta=json.loads((folder/'stage.json').read_text());v=(folder/'source_vram.bin').read_bytes()
        lim=meta['scroll_limits'];cols=meta['columns'];has=meta.get('has_map',cols>0)
        desc=bytearray(8192)
        if has:
            rows=(folder/'terrain_rows.bin').read_bytes();grid=[rows[r*cols:(r+1)*cols] for r in range(22)]
            blocks=[];index={};script=bytearray()
            for g in range(cols//4):
                for b in range(6):
                    blk=bytes(grid[b*4+rr][g*4+cc] if b*4+rr<22 else 0 for rr in range(4) for cc in range(4))
                    if blk not in index:index[blk]=len(blocks);blocks.append(blk)
                    script.append(index[blk])
            assert len(blocks)<256 and len(script)<=0x1900-0x700
            table=b''.join(blocks)
            if st<=7:bank=MAPS_A_BANK;base=0x8000+len(maps_a);maps_a+=table
            else:bank=MAPS_B_BANK;base=0x8000+len(maps_b);maps_b+=table
            assert len(maps_a)<=8192 and len(maps_b)<=8192
            first=lim['map_start'];last=first+cols;scroll_end=lim['word_e425'] if lim['word_e425']!=0xffff else last-1
            weights=[1]*768
            for y in range(22):
                third=min(y//8,2)
                for c,count in collections.Counter(grid[y]).items():weights[third*256+c]+=count
        else:
            blocks=[];script=b'';bank=MAPS_A_BANK;base=0x8000;first=last=0xffff;scroll_end=lim['word_e425'];weights=[1]*768
        tiles=[msxtile(v,c,t) for t in range(3) for c in range(256)];pals=palettes(tiles,weights)
        desc[0:6]=struct.pack('<HHH',first,(last-1)&0xffff if has else 0xffff,scroll_end);desc[6:8]=struct.pack('<H',base);desc[8:10]=struct.pack('<H',len(script));desc[10:12]=struct.pack('<H',0xffff);desc[12]=bank
        desc[0xa00:0xa02]=b'\xff\xff'
        for p,pal in enumerate(pals):desc[0x20+p*4:0x24+p*4]=bytes(NEAREST[c] for c in pal)
        for i,t in enumerate(tiles):
            arr=np.array(t);scores=[int(DIST[arr][:,p].min(1).sum()) for p in pals];p=int(np.argmin(scores))
            inds=DIST[arr][:,pals[p]].argmin(1)
            num=chr_base*256+addtile(encode(inds));desc[0x100+i]=num&255;desc[0x400+i]=(p<<6)|(num>>8)
        desc[0x700:0x700+len(script)]=script
        src=(folder/'sprites_normal.bin').read_bytes();sheet=bytearray()
        for frame in range(64):
            blk=src[frame*32:(frame+1)*32];pix=np.zeros((16,16),dtype=np.uint8)
            for yy in range(16):
                for xx in range(16):pix[yy,xx]=int(bool(blk[(xx//8)*16+yy]&(128>>(xx&7))))
            for xx in (0,8):
                for yy in (0,8):sheet+=encode(pix[yy:yy+8,xx:xx+8])
        sheet+=bytes(8192-len(sheet));sheets.append((st,desc,sheet))
        report.append(dict(map=st,has_map=bool(has),columns=cols,pieces=len(blocks),first_column=first,scroll_end=scroll_end,metatile_bank=bank,metatile_base=base,palettes=pals))
    chrdata+=bytes((-len(chrdata))%1024);tile_end=len(chrdata);banks={}
    for st,desc,sheet in sheets:
        ids=[]
        for off in range(0,8192,1024):
            b=bytes(sheet[off:off+1024])
            if b not in banks:banks[b]=chr_base*4+len(chrdata)//1024;chrdata.extend(b)
            ids.append(banks[b])
        assert max(ids)<256,max(ids)
        desc[0x10:0x18]=bytes(ids);(OUT/f'n3_map_{st:02d}.bin').write_bytes(desc)
    chrdata+=bytes((-len(chrdata))%4096)
    (OUT/'n3_graphics.chr').write_bytes(chrdata)
    (OUT/'n3_maps_a.bin').write_bytes(maps_a+bytes(8192-len(maps_a)));(OUT/'n3_maps_b.bin').write_bytes(maps_b+bytes(8192-len(maps_b)))
    summary=dict(maps=len(sheets),unique_bg_tiles=len(dictionary),bg_tile_bytes=tile_end,sprite_1k_banks=len(banks),chr_bytes=len(chrdata),chr_4k_banks=len(chrdata)//4096,chr_base_bank=chr_base,
                 maps_a_bytes=len(maps_a),maps_b_bytes=len(maps_b),sha256=hashlib.sha256(chrdata).hexdigest(),per_map=report,
                 scope='static terrain, palettes and hardware sprite frames only; no Nemesis 3 gameplay, bosses, interludes, pictures or events')
    (OUT/'n3_assets.json').write_text(json.dumps(summary,indent=1)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='per_map'},indent=1))
if __name__=='__main__':main()
