#!/usr/bin/env python3
"""Nemesis 2 maps -> native stage descriptors (Frente F, chapter 2 structure).

Reads the extracted Nemesis 2 data (assets/msx/nemesis2/) and writes, under
build/native/: n2_map_NN.bin (one 8 KiB descriptor per map, same header layout
as the Nemesis descriptors so DrawColumn/LoadStage can read them), two metatile
banks n2_maps_a.bin / n2_maps_b.bin, n2_graphics.chr (2bpp background tiles
with four palettes per map, plus the map's hardware sprite frames) and
n2_assets.json. Static terrain and graphics only: no Nemesis 2 enemies, bosses,
weapons or events are produced here.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib,struct,sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_native_assets import encode,msxtile,palettes,NEAREST,DIST
SRC=ROOT/'assets/msx/nemesis2';OUT=ROOT/'build/native'
CHR_BASE_BANK=25          # first 4 KiB CHR bank used by chapter 2 (after title art and panel)
MAPS_A_BANK=0x80|26;MAPS_B_BANK=0x80|27   # $5115 values of the two metatile banks (PRG banks 26/27)
def main():
    manifest=json.loads((SRC/'stage_manifest.json').read_text())
    # Source map limits and checkpoints (p01:6986, p01:694A) from the structure inventory.
    structure=json.loads((ROOT/'reports/nemesis2_structure.json').read_text())
    limits={int(s['map_id']):s for s in structure['stages']}
    chrdata=bytearray();dictionary={}
    def addtile(raw):
        if raw not in dictionary:dictionary[raw]=len(chrdata)//16;chrdata.extend(raw)
        return dictionary[raw]
    maps_a=bytearray();maps_b=bytearray();report=[];sheets=[]
    for m in manifest:
        st=m['stage_id'];folder=SRC/('map_%02d'%st)
        v=(folder/'source_vram.bin').read_bytes();script=(folder/'column_script.bin').read_bytes()
        rows=(folder/'terrain_rows.bin').read_bytes();cols=m['columns']
        by_id={x['id']:x for x in m['metatiles']}
        # local metatile list: 16-byte blocks (compact 8-byte blocks padded with empty rows)
        blocks=[];index={};new_script=bytearray()
        for n in script:
            meta=by_id[n];raw=bytes.fromhex(meta['hex']);raw=raw+bytes(16-len(raw))
            if raw not in index:index[raw]=len(blocks);blocks.append(raw)
            new_script.append(index[raw])
        assert len(blocks)<256 and len(new_script)<=0x1900-0x700
        table=b''.join(blocks)
        if st<=6:bank=MAPS_A_BANK;base=0x8000+len(maps_a);maps_a+=table
        else:bank=MAPS_B_BANK;base=0x8000+len(maps_b);maps_b+=table
        assert len(maps_a)<=8192 and len(maps_b)<=8192
        # palettes from real terrain usage (same method as the Nemesis descriptors)
        tiles=[msxtile(v,c,t) for t in range(3) for c in range(256)];weights=[1]*768
        for y in range(22):
            third=min(y//8,2)
            for c,count in collections.Counter(rows[y*cols:(y+1)*cols]).items():weights[third*256+c]+=count
        pals=palettes(tiles,weights)
        desc=bytearray(8192)
        lim=limits[st]['map_limits_p01_6986'];first=int(lim['first_map_column'],16);last=int(lim['last_map_column'],16);scroll_end=int(lim['scroll_end_column_0xE325'],16)
        table_last=last;last=first+cols   # map 8 (interior) lists $C0 but holds 160 columns; the script length is authoritative
        cp=limits[st]['checkpoint'].get('column');cp=int(cp,16) if cp else 0xffff
        desc[0:6]=struct.pack('<HHH',first,last-1,scroll_end);desc[6:8]=struct.pack('<H',base);desc[8:10]=struct.pack('<H',len(new_script));desc[10:12]=struct.pack('<H',cp);desc[12]=bank
        for p,pal in enumerate(pals):desc[0x20+p*4:0x24+p*4]=bytes(NEAREST[c] for c in pal)
        changed=total=0
        for i,t in enumerate(tiles):
            arr=np.array(t);scores=[int(DIST[arr][:,p].min(1).sum()) for p in pals];p=int(np.argmin(scores))
            inds=DIST[arr][:,pals[p]].argmin(1)
            changed+=sum(int(pals[p][ii])!=int(ti) for ii,ti in zip(inds,arr))*weights[i];total+=64*weights[i]
            num=CHR_BASE_BANK*256+addtile(encode(inds));desc[0x100+i]=num&255;desc[0x400+i]=(p<<6)|(num>>8)
        desc[0x700:0x700+len(new_script)]=new_script
        desc[0xa00:0xa02]=b'\xff\xff'   # no cannon records
        # hardware sprite frames (64 x 16x16, two 8x16 columns, 1bpp) -> 2bpp monochrome frames
        src=(folder/'sprites_normal.bin').read_bytes();sheet=bytearray()
        for frame in range(64):
            blk=src[frame*32:(frame+1)*32];pix=np.zeros((16,16),dtype=np.uint8)
            for yy in range(16):
                for xx in range(16):pix[yy,xx]=int(bool(blk[(xx//8)*16+yy]&(128>>(xx&7))))
            for xx in (0,8):
                for yy in (0,8):sheet+=encode(pix[yy:yy+8,xx:xx+8])
        sheet+=bytes(8192-len(sheet));sheets.append((st,desc,sheet))
        report.append(dict(map=st,columns=cols,first_column=first,last_column=last,table_last_column=table_last,scroll_end=scroll_end,checkpoint=cp,script_bytes=len(new_script),metatiles=len(blocks),metatile_bank=bank,metatile_base=base,palettes=pals,
                           palette_changed_weighted_pixels=changed,palette_total_weighted_pixels=total))
    chrdata+=bytes((-len(chrdata))%1024)
    banks={};tile_end=len(chrdata)
    for st,desc,sheet in sheets:
        ids=[]
        for off in range(0,8192,1024):
            b=bytes(sheet[off:off+1024])
            if b not in banks:banks[b]=CHR_BASE_BANK*4+len(chrdata)//1024;chrdata.extend(b)
            ids.append(banks[b])
        assert max(ids)<256
        desc[0x10:0x18]=bytes(ids);(OUT/f'n2_map_{st:02d}.bin').write_bytes(desc)
    chrdata+=bytes((-len(chrdata))%4096)
    (OUT/'n2_graphics.chr').write_bytes(chrdata)
    (OUT/'n2_maps_a.bin').write_bytes(maps_a+bytes(8192-len(maps_a)));(OUT/'n2_maps_b.bin').write_bytes(maps_b+bytes(8192-len(maps_b)))
    summary=dict(maps=len(sheets),unique_bg_tiles=len(dictionary),bg_tile_bytes=tile_end,sprite_1k_banks=len(banks),chr_bytes=len(chrdata),chr_4k_banks=len(chrdata)//4096,chr_base_bank=CHR_BASE_BANK,
                 maps_a_bytes=len(maps_a),maps_b_bytes=len(maps_b),sha256=hashlib.sha256(chrdata).hexdigest(),per_map=report,
                 scope='static terrain, palettes and hardware sprite frames only; no Nemesis 2 gameplay, software actors, bosses, weapons or events')
    (OUT/'n2_assets.json').write_text(json.dumps(summary,indent=1)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='per_map'},indent=1))
if __name__=='__main__':main()
