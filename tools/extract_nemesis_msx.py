#!/usr/bin/env python3
"""Extract Nemesis MSX graphics and terrain data from the hash-verified ROM.
Independent implementation informed by antxiko/Nemesis-disassembly.
IMPORTANT: corrects the mirror-record decoder in upstream tools/graficos.py.
Upstream commit: 3e486bc2f39c65eb97a944cda246f85fd30218ec.
Record layout verified against original Z80 at 434D, 4408, 4426, 4454.
Output is source evidence and reusable assets, NOT an implemented NES level.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, struct, collections
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED='3210f8a0f2309dd4b9a89fc2b24d0f178ce4393a0a1f2854fbce545c361261bc'
ORG=[0x4000,0x6000,0x8000,0xA000,0x6000,0x8000,0xA000,0x8000,0xA000,0x8000,0xA000,0x8000,0xA000,0x8000,0x8000,0x8000]
PAL=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
GFX={0x4000:0,0x6000:4,0x8000:5,0xA000:6}; MAP={0x4000:0,0x8000:11,0xA000:12}
REV=bytes(int(f'{x:08b}'[::-1],2) for x in range(256))
class Extractor:
    def __init__(self,rom:bytes):
        if hashlib.sha256(rom).hexdigest()!=EXPECTED:raise ValueError('Wrong Nemesis MSX revision')
        self.rom=rom;self.streams={};self.mirrors=[]
    def byte(self,bank,addr):
        offset=addr-ORG[bank]
        if not 0<=offset<8192:raise ValueError(f'Bank overrun: bank {bank} addr {addr:04X}')
        return self.rom[bank*8192+offset]
    def word(self,bank,addr):return self.byte(bank,addr)|(self.byte(bank,addr+1)<<8)
    def rle(self,v,bank,src,dst):
        start=src;out=0
        def rb(a):
            if 4<=bank<=6 and a>=ORG[bank]+8192:
                return self.byte(GFX[a&0xe000],a)
            return self.byte(bank,a)
        for _ in range(8192):
            op=rb(src);src+=1
            if op==0:
                raw=self.rom[bank*8192+start-ORG[bank]:bank*8192+src-ORG[bank]]
                self.streams[(bank,start)]={'bank':bank,'cpu_address':start,'rom_offset':bank*8192+start-ORG[bank],
                                           'compressed_bytes':len(raw),'decoded_writes':out,'sha256':hashlib.sha256(raw).hexdigest()}
                return src
            if op==0x80:dst=rb(src)|(rb(src+1)<<8);src+=2;continue
            if op&0x80:
                n=op&127; data=bytes(rb(src+i) for i in range(n));src+=n
            else:
                n=op;data=bytes([rb(src)])*n;src+=1
            for val in data:v[dst&0x3fff]=val;dst+=1;out+=1
        raise ValueError('RLE stream missing terminator')
    def load_records(self,v,addr):
        bank=GFX[addr&0xe000]
        for _ in range(256):
            flags=self.byte(bank,addr)
            if not flags:return
            patterns=self.word(bank,addr+1);tile=self.byte(bank,addr+3);colors=self.word(bank,addr+4)
            for bit,third in [(0,0x1000),(1,0x800),(2,0)]:
                if flags&(1<<bit):
                    self.rle(v,GFX[patterns&0xe000],patterns,0x2000+third+tile*8)
                    self.rle(v,GFX[colors&0xe000],colors,third+tile*8)
            addr+=6
        raise ValueError('Graphics record table missing terminator')
    def mirror_table(self,v,table,stage,vertical):
        addr=self.word(5,table+2*stage)
        for _ in range(256):
            # 434D: count is byte 3. 4454: source is byte 0.
            # 4426: destination is byte 1. 4460/4408: third flags are byte 2.
            source=self.byte(5,addr)
            if source==0:return
            dest=self.byte(5,addr+1);flags=self.byte(5,addr+2);count=self.byte(5,addr+3)
            source_third=0 if flags&4 else 0x800 if flags&2 else 0x1000
            n=count*8
            pat=bytes(v[0x2000+source_third+source*8:0x2000+source_third+source*8+n])
            col=bytes(v[source_third+source*8:source_third+source*8+n])
            if len(pat)!=n or len(col)!=n:raise ValueError('Mirror source out of VRAM')
            if vertical:
                pat=b''.join(pat[i:i+8][::-1] for i in range(0,n,8))
                col=b''.join(col[i:i+8][::-1] for i in range(0,n,8))
            else:
                pat=bytes(REV[x] for x in pat)
                # Original 43F2 only visits E300 (patterns), NOT E700 (colors).
            for bit,third in [(3,0x1000),(4,0x800),(5,0)]:
                if flags&(1<<bit):
                    a=0x2000+third+dest*8;c=third+dest*8
                    if a+n>0x4000 or c+n>0x4000:raise ValueError('Mirror destination out of VRAM')
                    v[a:a+n]=pat;v[c:c+n]=col
            self.mirrors.append(dict(stage=stage,record_address=addr,vertical=vertical,source=source,destination=dest,flags=flags,count=count))
            addr+=4
        raise ValueError('Mirror table missing terminator')
    def stage_vram(self,stage):
        v=bytearray(0x4000)
        self.load_records(v,0x932d)
        self.load_records(v,self.word(5,0x92e3+2*stage))
        self.mirror_table(v,0x92fb,stage,False);self.mirror_table(v,0x9313,stage,True)
        self.rle(v,5,0x86bb,0x1800)
        for tile in [0xf6,0xf7,0xf8]:
            for third in range(3):v[0x2000+third*0x800+tile*8]=0x10
        return v
    def stage_map(self,stage):
        a=0x4499+6*stage;start=self.word(0,a);end=self.word(0,a+2);event=self.word(0,a+4)
        script=self.word(11,0x97de+2*stage);pieces=0x8ff0 if stage in (5,9,10,12) else 0x8000
        width=(end if start!=0xffff else event if event!=0xffff else 0x100)+0x28
        if not 32<=width<=2048:raise ValueError(f'Unexpected preview width {width}')
        rows=[bytearray(width) for _ in range(22)]
        for d in range(width):
            if start<=d<=end and start!=0xffff:
                record=((d-start)>>2)*6;column=[]
                for i in range(6):
                    pos=script+record+i;piece=self.byte(MAP[pos&0xe000],pos)
                    p=pieces+piece*16+((d-start)&3)
                    column.extend(self.byte(11,p+4*k) for k in range(2 if i==5 else 4))
            else:
                column=[0]*22;y=self.byte(0,0x478e+(d&31))
                if 1<=y<=22:column[y-1]=0xf6
            for y,val in enumerate(column):rows[y][d]=val
        meta=dict(stage=stage,terrain_start=start,terrain_end=end,event_marker=event,script_address=script,
                  metatile_address=pieces,preview_columns=width,rows=22,
                  extraction='static terrain only; enemy spawns and dynamic terrain NOT integrated',
                  preview_extent_is_arbitrary=(start==0xffff and event==0xffff))
        if start!=0xffff:
            n=((end-start)//4+1)*6;bank=MAP[script&0xe000];off=bank*8192+script-ORG[bank]
            meta.update(script_rom_offset=off,script_bytes=n,script_hex=self.rom[off:off+n].hex())
        return meta,rows

def tile_indices(v,tile,third):
    a=third*0x800+tile*8;out=bytearray()
    for y in range(8):
        bits=v[0x2000+a+y];color=v[a+y];fg=color>>4;bg=color&15
        out.extend(fg if bits&(0x80>>x) else bg for x in range(8))
    return bytes(out)

def indexed_image(data,size):
    im=Image.frombytes('P',size,bytes(data));im.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-48));return im

def render_map(v,rows):
    width=len(rows[0]);im=Image.new('P',(width*8,176));im.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-48))
    cache={}
    for y,row in enumerate(rows):
        third=y//8
        for x,tile in enumerate(row):
            key=third,tile
            if key not in cache:cache[key]=indexed_image(tile_indices(v,tile,third),(8,8))
            im.paste(cache[key],(x*8,y*8))
    return im

def extract(root=ROOT):
    src=json.loads((root/'manifests/selected_sources.json').read_text())['nemesis_msx']
    ex=Extractor((root/src['path']).read_bytes());out=root/'assets/msx/nemesis';out.mkdir(parents=True,exist_ok=True)
    stage_meta=[];tiles={};colors=collections.Counter();nonblack=collections.Counter();total=0
    previews=[]
    for stage in range(1,13):
        v=ex.stage_vram(stage);meta,rows=ex.stage_map(stage);stage_meta.append(meta)
        folder=out/f'stage_{stage:02d}';folder.mkdir(exist_ok=True)
        (folder/'source_vram.bin').write_bytes(v)
        (folder/'terrain_rows.bin').write_bytes(b''.join(rows))
        (folder/'stage.json').write_text(json.dumps(meta,indent=2))
        img=render_map(v,rows);img.save(folder/'terrain.png')
        crop=img.crop((max(0,min(0x80*8,img.width-256)),0,max(0,min(0x80*8,img.width-256))+256,176)).convert('RGB')
        previews.append(crop)
        sheet=Image.new('P',(16*8*3,16*8));sheet.putpalette(img.getpalette())
        for third in range(3):
            for tile in range(256):
                pix=tile_indices(v,tile,third);key=hashlib.sha256(pix).hexdigest()
                tiles.setdefault(key,{'pixels':pix,'references':[]})['references'].append([stage,third,tile]);total+=1
                distinct=set(1 if c==0 else c for c in pix);colors[len(distinct)]+=1;nonblack[len(distinct-{1})]+=1
                sheet.paste(indexed_image(pix,(8,8)),(third*128+(tile%16)*8,(tile//16)*8))
        sheet.resize((768,256),Image.Resampling.NEAREST).save(folder/'tiles.png')
    (out/'stage_manifest.json').write_text(json.dumps(stage_meta,indent=2))
    streams=list(ex.streams.values());(out/'compressed_streams.json').write_text(json.dumps(streams,indent=2))
    (out/'mirror_records.json').write_text(json.dumps(ex.mirrors,indent=2))
    # Preserve compact source metatiles, not expanded screenshots, for the port.
    (out/'metatiles_bank11.bin').write_bytes(ex.rom[11*8192:11*8192+0x17de])
    dictionary=b''.join(v['pixels'] for v in tiles.values());(out/'source_indexed_tile_dictionary.bin').write_bytes(dictionary)
    (out/'source_indexed_tile_references.json').write_text(json.dumps([{'sha256':h,'references':v['references']} for h,v in tiles.items()]))
    contact=Image.new('RGB',(4*256,3*176))
    for i,im in enumerate(previews):contact.paste(im,((i%4)*256,(i//4)*176))
    contact.save(out/'all_12_terrain_previews.png')
    report={'source_sha256':EXPECTED,'terrain_records':12,'tile_occurrences':total,'unique_pixel_tiles':len(tiles),
            'color_counts_per_tile':dict(colors),'nonblack_color_counts_per_tile':dict(nonblack),
            'unique_rle_streams':len(streams),'rle_stream_bytes_sum':sum(s['compressed_bytes'] for s in streams),
            'mirror_records':len(ex.mirrors),'upstream_mirror_decoder_corrected':True,
            'runtime_integration':False,'original_machine_vram_comparison':'pending',
            'limitations':['Static terrain and source graphics only; no claims of gameplay completion.',
                           'Background objects and animations must be implemented from event/object routines.',
                           'Starfield lengths use recorded event marker for a finite inspection preview.',
                           'No NES palette quantization has silently been applied.']}
    (root/'reports/nemesis_extraction.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':extract()
