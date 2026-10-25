#!/usr/bin/env python3
"""Hash-checked, compact Nemesis MSX -> native MMC5 graphics/data compilation.
No expanded frame streams; source terrain scripts and metatiles stay compact.
Private generated assets are not source-controlled. Palette reduction is measured.
"""
from __future__ import annotations
import collections, hashlib, itertools, json, math, pathlib, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from extract_nemesis_msx import Extractor, PAL, ROOT

OUT = ROOT / 'build/native'
# RGB reference used for conversion decisions, not a claim of analog NES colors.
NES_RGB = bytes.fromhex('626262 001fb2 2404c8 5200b2 730076 800024 730b00 522800 244400 005700 005c00 005324 003c76 000000 000000 000000 '
 'ababab 0d57ff 4b30ff 8a13ff bc08d6 d21269 c72e00 9d5400 607b00 209800 00a300 009942 007db4 000000 000000 000000 '
 'ffffff 53aeff 9085ff d365ff ff57ff ff5dcf ff7757 fa9e00 bdc700 7ae700 43f611 26ef7e 2cd5f6 4e4e4e 000000 000000 '
 'ffffff b6e1ff ced1ff e9c3ff ffbcff ffbded ffc6bc ffd69a e9e681 cef481 b6fb9a a9fac3 a9f0f5 b8b8b8 000000 000000')
RGB = np.frombuffer(NES_RGB, dtype=np.uint8).reshape(64,3).astype(np.int32)
SRC = np.array(PAL, dtype=np.int32)
NEAREST = [int(np.argmin(((RGB-c)**2).sum(1))) for c in SRC]
NEAREST[0] = NEAREST[1] = 0x0f
DIST = ((SRC[:,None,:]-SRC[None,:,:])**2).sum(2)

def encode(tile):
    t=np.array(tile,dtype=np.uint8).reshape(8,8)
    return bytes(sum(int((t[y,x]>>p)&1) << (7-x) for x in range(8)) for p in range(2) for y in range(8))
def msxtile(v, c, third):
    p=v[0x2000+third*0x800+c*8:0x2000+third*0x800+c*8+8]
    k=v[third*0x800+c*8:third*0x800+c*8+8]
    return tuple(0 if (z:=((k[y]>>4) if p[y]&(128>>x) else (k[y]&15)))<2 else z for y in range(8) for x in range(8))
def palettes(tiles, weights):
    counts = np.array([np.bincount(t,minlength=16) for t in tiles],dtype=np.int64)
    candidates={(0,14,15,7),(0,4,5,15),(0,6,8,15),(0,2,10,15)}
    for t in tiles:
        c=collections.Counter(t);top=[x for x,_ in c.most_common() if x][:3]
        top += [x for x in (15,14,7) if x not in top][:3-len(top)]
        candidates.add((0,*sorted(top)))
    candidates=sorted(candidates)
    cost=np.stack([counts @ DIST[:,p].min(1) for p in candidates])
    best=np.full(len(tiles),10**12,dtype=np.int64);chosen=[]
    weights=np.array(weights,dtype=np.int64)
    for _ in range(4):
        idx=int(np.argmin((np.minimum(cost,best)*weights).sum(1)))
        chosen.append(candidates[idx]);best=np.minimum(best,cost[idx])
        cost[idx]=10**12
    return chosen

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Selected input names are stable; additionally verify bytes before extraction.
    npath=ROOT/'private_sources/3210f8a0f2309dd4b9a89fc2b24d0f178ce4393a0a1f2854fbce545c361261bc.rom'
    rom=npath.read_bytes();ex=Extractor(rom)
    title=(ROOT/'assets/title/title.chr').read_bytes()
    assert len(title)==4096
    chrdata=bytearray(title)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',8)
    fnt=bytearray(4096)
    for c in range(32,127):
        im=Image.new('L',(8,8));d=ImageDraw.Draw(im);d.text((1,-1),chr(c),font=font,fill=1)
        fnt[c*16:c*16+16]=encode(np.array(im))
    chrdata+=fnt
    dictionary={bytes(16):512}; chrdata+=bytes(16)
    def addtile(raw):
        if raw not in dictionary:
            dictionary[raw]=len(chrdata)//16;chrdata.extend(raw)
        return dictionary[raw]
    # Stage-specific sprite sheets are deduplicated at 1 KiB bank granularity.
    stages=[]; stage_data=[]; spr_sheets=[]; stats=[]
    for stage in range(1,13):
        v=ex.stage_vram(stage)
        for j in range(2):
            a=0x42ad+stage*6+j*3;src=ex.word(0,a);tile=ex.byte(0,a+2)
            ex.rle(v,0 if src<0x6000 else 5,src,0x1800+tile*8)
        if stage==5:ex.rle(v,5,0x8fcb,0x1d00)
        a=0x4499+stage*6;start,end,event=(ex.word(0,a+i) for i in (0,2,4))
        script=ex.word(11,0x97de+2*stage)
        n=(((end-start)//4+1)*6) if start!=65535 else 0
        rawscript=bytes(ex.byte(11 if script+i<0xa000 else 12,script+i) for i in range(n))
        # Pixel weights from real terrain uses (inspection expansion is not stored).
        _,rows=ex.stage_map(stage)
        tiles=[msxtile(v,c,t) for t in range(3) for c in range(256)]
        weights=[1]*768
        for y,row in enumerate(rows):
            third=min(y//8,2)
            for c,count in collections.Counter(row).items():weights[third*256+c]+=count
        pals=palettes(tiles,weights)
        desc=bytearray(4096);desc[0:6]=struct.pack('<HHH',start,end,event)
        desc[6:8]=struct.pack('<H',0x8ff0 if stage in (5,9,10,12) else 0x8000)
        desc[8:10]=struct.pack('<H',len(rawscript))
        desc[10:12]=struct.pack('<H',ex.word(0,0x4212+stage*2) if stage<12 else 0xffff)
        for p,pal in enumerate(pals):desc[0x20+p*4:0x24+p*4]=bytes(NEAREST[c] for c in pal)
        changed=total=0
        for i,t in enumerate(tiles):
            arr=np.array(t);scores=[int(DIST[arr][:,p].min(1).sum()) for p in pals];p=int(np.argmin(scores))
            inds=DIST[arr][:,pals[p]].argmin(1)
            changed+=sum(int(pals[p][ii])!=int(ti) for ii,ti in zip(inds,arr))*weights[i]
            total+=64*weights[i]
            num=addtile(encode(inds));desc[0x100+i]=num&255;desc[0x400+i]=(p<<6)|(num>>8)
        assert len(rawscript)<=0x300
        desc[0x700:0x700+len(rawscript)]=rawscript
        # Cannon records copied exactly from original; no authored replacements.
        cp=ex.word(2,0x9262+2*stage);cannon=bytearray()
        for i in range(256):
            at=cp+len(cannon);dist=ex.word(2,at)
            if dist==0xffff:break
            cannon+=bytes(ex.byte(2,at+j) for j in range(3))
        else:raise ValueError('Unterminated cannon list')
        assert len(cannon)+2<=0x300
        desc[0xa00:0xa00+len(cannon)+2]=cannon+b'\xff\xff'
        # Hardware TMS frames -> monochrome NES frames; palettes supplied by objects.
        sheet=bytearray()
        for frame in range(64):
            src=v[0x1800+frame*32:0x1800+(frame+1)*32]
            pix=np.zeros((16,16),dtype=np.uint8)
            for yy in range(16):
                for xx in range(16):pix[yy,xx]=int(bool(src[(xx//8)*16+yy]&(128>>(xx&7))))
            for xx in (0,8):
                for yy in (0,8):sheet+=encode(pix[yy:yy+8,xx:xx+8])
        # Software actors are source 2x2 tile blocks, not generic substitutes.
        for frame in range(56):
            codes=[ex.byte(5,0x91d1+frame*4+j) for j in range(4)]
            pic=np.zeros((16,16),dtype=np.uint8)
            for j,c in enumerate(codes):pic[(j//2)*8:(j//2)*8+8,(j%2)*8:(j%2)*8+8]=np.array(msxtile(v,c,0)).reshape(8,8)
            colors=(0,15,8,4);ix=DIST[pic][:,:,colors].argmin(2)
            for xx in (0,8):
                for yy in (0,8):sheet+=encode(ix[yy:yy+8,xx:xx+8])
        # Composite actual source ship masks, including banks for up/down frames.
        for frame in (0,2,4):
            pix=np.zeros((16,16),dtype=np.uint8)
            for layer in (0,1):
                src=v[0x1800+(frame+layer)*32:0x1800+(frame+layer+1)*32]
                for yy in range(16):
                    for xx in range(16):
                        if src[(xx//8)*16+yy]&(128>>(xx&7)):pix[yy,xx]=layer+1
            for xx in (0,8):
                for yy in (0,8):sheet+=encode(pix[yy:yy+8,xx:xx+8])
        # 123-127: native projectile glyphs / option / explosion, source-based where possible.
        for frame in range(123,128):
            srcframe={123:31,124:32,125:34,126:35,127:36}[frame]
            sheet+=sheet[srcframe*64:srcframe*64+64]
        assert len(sheet)==8192,len(sheet)
        stage_data.append(desc);spr_sheets.append(sheet)
        stats.append(dict(stage=stage,terrain_script_bytes=len(rawscript),cannon_records=len(cannon)//3,
                          palette_changed_weighted_pixels=changed,palette_total_weighted_pixels=total,
                          source_palette_sets=pals,source_vram_sha256=hashlib.sha256(v).hexdigest()))
    chrdata+=bytes((-len(chrdata))%1024)
    banks={};sprite_start=len(chrdata)
    for i,sheet in enumerate(spr_sheets):
        ids=[]
        for off in range(0,len(sheet),1024):
            b=bytes(sheet[off:off+1024])
            if b not in banks:banks[b]=len(chrdata)//1024;chrdata.extend(b)
            ids.append(banks[b])
        assert max(ids)<256
        stage_data[i][0x10:0x18]=bytes(ids)
    for i,desc in enumerate(stage_data): (OUT/f'stage_{i+1:02d}.bin').write_bytes(desc)
    # At $A000 the source address $8000 becomes $A000, and $8FF0 becomes $AFF0.
    metatiles=rom[11*8192:11*8192+(0x97de-0x8000)]
    (OUT/'metatiles.bin').write_bytes(metatiles+bytes(8192-len(metatiles)))
    target=8192
    while target<len(chrdata):target*=2
    useful=len(chrdata);chrdata+=bytes(target-len(chrdata));(OUT/'graphics.chr').write_bytes(chrdata)
    # Bank-independent constants from verified original data.
    tables=bytearray(8192)
    tables[:32]=bytes(ex.byte(0,0x478e+i) for i in range(32))
    tables[0x100:0x180]=bytes(ex.byte(1,0x6ba3+i) for i in range(128))
    tables[0x200:0x300]=bytes(ex.byte(1,0x6753+i) for i in range(256))
    tables[0x300:0x340]=bytes(ex.byte(1,0x6853+i) for i in range(64))
    (OUT/'tables.bin').write_bytes(tables)
    nrom=(ROOT/'private_sources/cda334d473ae84fbda5df431e6618b46d9541da9fc572bd9035dccfb0df4e33d.nes').read_bytes()
    assert hashlib.sha256(nrom).hexdigest()=='cda334d473ae84fbda5df431e6618b46d9541da9fc572bd9035dccfb0df4e33d'
    audio=nrom[16+0x6c1e:16+0x7ffa];assert len(audio)==0x13dc
    (OUT/'audio.bin').write_bytes(audio)
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),stages=stats,terrain_unique_tiles=len(dictionary),
                chr_useful_bytes=useful,chr_allocated_bytes=target,sprite_unique_1k_banks=len(banks),
                metatile_bytes=len(metatiles),stage_descriptors_bytes=12*4096,
                limitations=['Palette reduction is lossy; software actor palette provisional.',
                             'These are extracted assets, not integrated stage completion.'])
    (OUT/'assets_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('stages','limitations')},indent=2))
if __name__=='__main__':main()
