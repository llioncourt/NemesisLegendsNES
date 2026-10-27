#!/usr/bin/env python3
"""Hash-checked, compact Nemesis MSX -> native MMC5 graphics/data compilation.
No expanded frame streams; source terrain scripts and metatiles stay compact.
Private generated assets are not source-controlled. Palette reduction is measured.
"""
from __future__ import annotations
import collections, hashlib, itertools, json, math, pathlib, struct, sys
import numpy as np
from PIL import Image, ImageDraw
from create_title_asset import FONT
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
    # Deterministic authored 5x7 font; no installed font-version dependency.
    glyphs=dict(FONT)
    glyphs.update({
      '0':['01110','10001','10011','10101','11001','10001','01110'],
      '1':['00100','01100','00100','00100','00100','00100','01110'],
      '2':['01110','10001','00001','00010','00100','01000','11111'],
      '3':['11110','00001','00001','01110','00001','00001','11110'],
      '4':['00010','00110','01010','10010','11111','00010','00010'],
      '5':['11111','10000','10000','11110','00001','00001','11110'],
      '6':['01110','10000','10000','11110','10001','10001','01110'],
      '7':['11111','00001','00010','00100','01000','01000','01000'],
      '8':['01110','10001','10001','01110','10001','10001','01110'],
      '9':['01110','10001','10001','01111','00001','00001','01110'],
      ':':['00000','00100','00100','00000','00100','00100','00000'],
      '-':['00000','00000','00000','11111','00000','00000','00000'],
      '.':['00000','00000','00000','00000','00000','00110','00110']})
    fnt=bytearray(4096)
    for ch,rows in glyphs.items():
        pic=np.zeros((8,8),dtype=np.uint8)
        for y,line in enumerate(rows):
            for x,v in enumerate(line):pic[y,x+1]=3 if v=='1' else 0
        fnt[ord(ch)*16:ord(ch)*16+16]=encode(pic)
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
        if stage <= 8:
            waves=ex.word(3,0xa3a6+stage*2)
            desc[0xd00:0xd10]=bytes(ex.byte(3,waves+j) for j in range(16))
            desc[0xd10]=ex.byte(3,0xa5af+stage)
        desc[0xd20:0xd24]=bytes(ex.byte(2,0x9205+orientation*12+stage-1) for orientation in range(4))
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
        # Source glyph $F8 normal shot and $FC laser. Option $44, missile $20.
        for frame in range(123,128):
            if frame in (123,125):
                glyph=np.array(msxtile(v,0xf8 if frame==123 else 0xfc,0)).reshape(8,8)
                pix=np.zeros((16,16),dtype=np.uint8)
                pix[:8,:8]=(glyph!=0).astype(np.uint8)
                if frame==125:pix[:8,8:]=(glyph!=0).astype(np.uint8)
                for xx in (0,8):
                    for yy in (0,8):sheet+=encode(pix[yy:yy+8,xx:xx+8])
            else:
                srcframe={124:17,126:8,127:6}[frame]
                sheet+=sheet[srcframe*64:srcframe*64+64]
        # Source player and force-field records. Original hardware frames 0..14
        # are player/field/weapon resources, not enemy frames. Weapons above were
        # copied first to their native slots. Preserve the source front-layer
        # priority when compositing the two source monochrome sprites.
        ship_records = [(0x99eb,3), (0x99f7,6), (0x9a0f,6)]
        ship_index=0
        for state,(base,count) in enumerate(ship_records):
            for variant in range(count):
                entries=[(ex.byte(2,base+variant*4+j),ex.byte(2,base+variant*4+j+1)) for j in (0,2)]
                pix=np.zeros((16,16),dtype=np.uint8)
                light_weak=state==1 and variant>=3
                palette={0:0,15:2 if light_weak else 1,8:2,5:3,6:2,9:3,7:2}
                for pattern,color in reversed(entries):
                    src=v[0x1800+pattern*8:0x1800+pattern*8+32]
                    for yy in range(16):
                        for xx in range(16):
                            if src[(xx//8)*16+yy]&(128>>(xx&7)):pix[yy,xx]=palette[color]
                raw=b''.join(encode(pix[yy:yy+8,xx:xx+8]) for xx in (0,8) for yy in (0,8))
                sheet[ship_index*64:(ship_index+1)*64]=raw
                ship_index+=1
        assert ship_index==15
        # Stage-one five-piece encounter: source character table p02:905C.
        # Source software frames 35..39 are blank in this stage and explicitly
        # reserved here, without altering any other stage's frame set.
        if stage == 1:
            for part in range(5):
                source_slot = 5 - part
                codes=[ex.byte(2,0x905c+source_slot*4+j) for j in range(4)]
                if part != 2: codes[2:]=[0,0]
                pix=np.zeros((16,16),dtype=np.uint8)
                for j,c in enumerate(codes):
                    pix[(j//2)*8:(j//2+1)*8,(j%2)*8:(j%2+1)*8]=np.array(msxtile(v,c,1)).reshape(8,8)
                ix=DIST[pix][:,:,(0,15,8,4)].argmin(2)
                raw=b''.join(encode(ix[yy:yy+8,xx:xx+8]) for xx in (0,8) for yy in (0,8))
                sheet[(99+part)*64:(100+part)*64]=raw
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
    # Big Core background graphics: original loader 4A6D / record 98A3.
    # E100=1 selects VERTICAL mirroring, including color-row reversal.
    bv=ex.stage_vram(1); ex.load_records(bv,0x98a3)
    a=0x98b0
    while ex.byte(5,a):
        source,dest,flags,count=[ex.byte(5,a+j) for j in range(4)]
        third=0 if flags&4 else 0x800 if flags&2 else 0x1000
        pat=bytes(bv[0x2000+third+source*8:0x2000+third+(source+count)*8])
        col=bytes(bv[third+source*8:third+(source+count)*8])
        pat=b''.join(pat[i:i+8][::-1] for i in range(0,len(pat),8))
        col=b''.join(col[i:i+8][::-1] for i in range(0,len(col),8))
        for bit,t in [(3,0x1000),(4,0x800),(5,0)]:
            if flags&(1<<bit):
                bv[0x2000+t+dest*8:0x2000+t+(dest+count)*8]=pat
                bv[t+dest*8:t+(dest+count)*8]=col
        a+=4
    body=bytes(ex.byte(1,0x7ee6+j) for j in range(88))
    eye=bytes(ex.byte(1,0x7f3e+j) for j in range(36))
    face=bytes(ex.byte(1,0x7f62+j) for j in range(18))
    btiles=[msxtile(bv,c,0) for c in range(256)]
    weights=collections.Counter(body+eye+face)
    counts=np.bincount([color for c in body+eye+face for color in btiles[c]],minlength=16)
    candidates=[(0,*p) for p in itertools.combinations(range(2,16),3)]
    bp=min(candidates,key=lambda p: int(counts@DIST[:,p].min(1)))
    chrdata+=bytes((-len(chrdata))%4096)
    bbank=len(chrdata)//4096
    for t in btiles:
        arr=np.array(t); ix=DIST[arr][:,bp].argmin(1);chrdata+=encode(ix)
    boss=bytearray(8192);boss[0]=bbank;boss[4:8]=bytes(NEAREST[c] for c in bp)
    boss[0x100:0x158]=body;boss[0x160:0x184]=eye;boss[0x190:0x1a2]=face
    boss[0x1b0:0x1d0]=bytes(ex.byte(1,0x718d+j) for j in range(32))
    boss[0x1d0:0x1d8]=bytes(ex.byte(1,0x7e03+j) for j in range(8))
    (OUT/'boss.bin').write_bytes(boss)
    (OUT/'boss.inc').write_text('BossBGbank = '+str(bbank)+'\n')
    # CP0005: approved title in previously unused CHR allocation. Gameplay
    # bank indices never move. Fail rather than overwrite a growing game.
    if len(chrdata) > 19*4096:
        raise ValueError('Gameplay CHR reached title bank 19; repack explicitly')
    title_dir=ROOT/'assets/title_art'
    art=(title_dir/'background.chr').read_bytes()
    if len(art)>4*4096:raise ValueError('Title art exceeds four CHR banks')
    chrdata+=bytes(19*4096-len(chrdata));chrdata+=art
    chrdata+=bytes(23*4096-len(chrdata))
    chrdata+=(title_dir/'cursor.chr').read_bytes()
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
    vel=[(ex.byte(1,0x6853+i)*0x50)>>5 for i in range(64)]
    (OUT/'aim.bin').write_bytes(bytes([v&255 for v in vel]+[v>>8 for v in vel]+[v&255 for v in vel[::-1]]+[v>>8 for v in vel[::-1]]))
    nrom=(ROOT/'private_sources/cda334d473ae84fbda5df431e6618b46d9541da9fc572bd9035dccfb0df4e33d.nes').read_bytes()
    assert hashlib.sha256(nrom).hexdigest()=='cda334d473ae84fbda5df431e6618b46d9541da9fc572bd9035dccfb0df4e33d'
    audio=nrom[16+0x6c1e:16+0x7ffa];assert len(audio)==0x13dc
    (OUT/'audio.bin').write_bytes(audio)
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),stages=stats,terrain_unique_tiles=len(dictionary),
                chr_useful_bytes=useful,chr_allocated_bytes=target,sprite_unique_1k_banks=len(banks),
                metatile_bytes=len(metatiles),stage_descriptors_bytes=12*4096,
                boss_chr_bank=bbank,boss_source_palette=bp,
                limitations=['Palette reduction is lossy; software actor palette provisional.',
                             'These are extracted assets, not integrated stage completion.'])
    (OUT/'assets_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('stages','limitations')},indent=2))
if __name__=='__main__':main()
