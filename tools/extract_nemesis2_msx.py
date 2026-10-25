#!/usr/bin/env python3
"""Nemesis 2 source-resource reader. Not a NES gameplay implementation.
Format evidence: antxiko/Nemesis2-disassembly tools/dibuja.py (blob
4f79f3f1b78a7f1f52727cd83002e52cb0382dd6) and tools/vram.py (blob
0349a197a038bb41a1bae7cb309813777c3d076d), read 2026-10-25.
Preserves raw column scripts/metablocks alongside decoded inspection images.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib
from PIL import Image
from extract_nemesis_msx import ROOT,REV,render_map,tile_indices,indexed_image
EXPECTED='227113f94d9900cb48d2f9e88627224dd8cc3d9504614a01e94cf6b23ba508dc'
class Window:
 def __init__(self,rom,banks):self.rom=rom;self.banks=(0,)+tuple(banks)
 def offset(self,a):
  if not 0x4000<=a<0xc000:raise ValueError('Unmapped address %04X'%a)
  return self.banks[(a-0x4000)//8192]*8192+(a&8191)
 def __call__(self,a):return self.rom[self.offset(a)]
 def word(self,a):return self(a)|(self(a+1)<<8)
 def raw(self,a,n):return bytes(self(a+i) for i in range(n))
class Extractor:
 def __init__(self,rom):
  if hashlib.sha256(rom).hexdigest()!=EXPECTED:raise ValueError('Wrong Nemesis 2 revision')
  self.rom=rom;self.gfx=Window(rom,(7,8,9));self.maps=Window(rom,(13,14,15));self.streams={};self.copy_records=[]
 def rle(self,v,w,src,dst):
  start=src;writes=0
  for _ in range(16384):
   n=w(src);src+=1
   if n==0:
    raw=w.raw(start,src-start);key=(w.offset(start),len(raw));self.streams[key]=dict(rom_offset=key[0],compressed_bytes=key[1],decoded_writes=writes,sha256=hashlib.sha256(raw).hexdigest());return
   if n==0x80:dst=w.word(src);src+=2;continue
   if n<0x80:data=bytes([w(src)])*n;src+=1
   else:data=w.raw(src,n&127);src+=n&127
   for b in data:v[dst&0x3fff]=b;dst+=1;writes+=1
  raise ValueError('Unterminated RLE')
 def lists(self,v,a):
  w=self.gfx
  for _ in range(256):
   flags=w(a)
   if not flags:return
   for bit,base in [(0,0x1000),(1,0x800),(2,0)]:
    if flags>>bit&1:
     target=base+8*w(a+3);self.rle(v,w,w.word(a+1),0x2000+target);self.rle(v,w,w.word(a+4),target)
   a+=6
  raise ValueError('Unterminated graphics list')
 def mirrors(self,v,a,vertical):
  w=self.gfx
  for _ in range(256):
   source=w(a)
   if not source:return
   dest=w(a+1);flags=w(a+2);count=(flags>>6)&3;size=3
   if not count:count=w(a+3);size=4
   third=0 if flags&4 else 0x800 if flags&2 else 0x1000
   p=bytearray(v[(0x2000+third+8*source+i)&0x3fff] for i in range(count*8));c=bytearray(v[(third+8*source+i)&0x3fff] for i in range(count*8))
   if vertical:
    for i in range(0,len(p),8):p[i:i+8]=p[i:i+8][::-1];c[i:i+8]=c[i:i+8][::-1]
   else:p=bytearray(REV[b] for b in p)
   for bit,base in [(3,0x1000),(4,0x800),(5,0)]:
    if flags>>bit&1:
     for i in range(len(p)):v[(0x2000+base+dest*8+i)&0x3fff]=p[i];v[(base+dest*8+i)&0x3fff]=c[i]
   self.copy_records.append(dict(address=a,source=source,destination=dest,flags=flags,count=count,record_bytes=size,vertical=vertical));a+=size
  raise ValueError('Unterminated mirror list')
 def vram(self,stage):
  v=bytearray(16384);w=self.gfx;self.lists(v,0x6048);self.lists(v,w.word(0x6000+2*stage));self.mirrors(v,w.word(0x6018+2*stage),False);self.mirrors(v,w.word(0x6030+2*stage),True);self.lists(v,0x4358);return v
 def sprite_copies(self,v,w,a):
  for _ in range(256):
   kind=w(a)
   if not kind:return
   n,src,dst=w(a+1),w(a+2),w(a+3)
   for k in range(n):
    pos=0x1800+src*8+k*32;data=v[pos:pos+32]
    if len(data)!=32:raise ValueError('Sprite overrun')
    if kind==1:data=data[:16][::-1]+data[16:][::-1]
    else:data=bytes(REV[b] for b in data);data=data[16:]+data[:16]
    pos=0x1800+dst*8+k*32;v[pos:pos+32]=data
   a+=4
  raise ValueError('Unterminated sprite copy list')
 def sprites(self,stage,base,penguin=False,drill=False):
  v=bytearray(base);w=self.gfx
  if penguin:
   other=Window(self.rom,(7,8,12));self.rle(v,other,0xbf19,0x1800);self.rle(v,other,0xbf82,0x19e0)
  else:self.rle(v,w,0x936f,0x1800);self.rle(v,w,0x942b,0x1960)
  self.rle(v,w,0x93c0,0x18c0)
  if drill:self.rle(v,w,0x9d17,0x1800);self.rle(v,w,0x9d68,0x1960)
  self.rle(v,w,0x94b8,0x1a20);self.sprite_copies(v,w,0x44ea)
  a=w.word(0x92b3+stage*2)
  for _ in range(256):
   if not w(a):break
   self.rle(v,w,w.word(a+1),0x1800+8*w(a));a+=3
  else:raise ValueError('Unterminated sprite stream list')
  self.sprite_copies(v,w,w.word(0x9348+stage*2));return bytes(v[0x1800:0x2000])
 def terrain(self,stage):
  w=self.maps;pointers=[w.word(0x7900+2*k) for k in range(12)];start=pointers[stage];end=min([x for x in pointers if x>start]+[0x91a8])
  if (end-start)%6:raise ValueError('Non-integral column-script length')
  script=w.raw(start,end-start);table=w.word(0x5557+2*stage);threshold=w(0x494a+stage)
  rows=[bytearray() for _ in range(22)];used={}
  for pos in range(0,len(script),6):
   blocks=[]
   for original in script[pos:pos+6]:
    n=original
    if stage not in (0,8) and n<4:address=0x6000+16*n;size=16
    else:
     if stage not in (0,8):n-=4
     address=table+16*n if n<threshold else table+16*threshold+8*(n-threshold);size=16 if n<threshold else 8
    raw=w.raw(address,size);block=raw+bytes(16-size);blocks.append(block);used[original]=dict(id=original,address=address,rom_offset=w.offset(address),bytes=size,hex=raw.hex())
   for col in range(4):
    for row in range(22):rows[row].append(blocks[row//4][(row%4)*4+col])
  return dict(stage_id=stage,rows=22,columns=len(rows[0]),column_script_address=start,column_script_rom_offset=w.offset(start),column_script_bytes=len(script),metatile_table_address=table,compact_metatile_threshold=threshold,metatiles=list(used.values()),runtime_integration=False,dynamic_terrain_and_enemy_events='not_extracted'),rows,script

def sprite_sheet(data):
 im=Image.new('1',(16*18,4*18));px=im.load()
 for k in range(64):
  for side in range(2):
   for y in range(16):
    b=data[k*32+side*16+y]
    for x in range(8):px[(k%16)*18+1+side*8+x,(k//16)*18+1+y]=bool(b&(0x80>>x))
 return im.resize((576,144),Image.Resampling.NEAREST)

def extract():
 selected=json.loads((ROOT/'manifests/selected_sources.json').read_text())['nemesis2_msx'];ex=Extractor((ROOT/selected['path']).read_bytes());out=ROOT/'assets/msx/nemesis2';out.mkdir(parents=True,exist_ok=True)
 manifest=[];tiles={};colors=collections.Counter();previews=[]
 for stage in range(12):
  folder=out/('map_%02d'%stage);folder.mkdir(exist_ok=True);v=ex.vram(stage);meta,rows,script=ex.terrain(stage);manifest.append(meta)
  (folder/'source_vram.bin').write_bytes(v);(folder/'terrain_rows.bin').write_bytes(b''.join(rows));(folder/'column_script.bin').write_bytes(script);(folder/'stage.json').write_text(json.dumps(meta,indent=2)+'\n');img=render_map(v,rows);img.save(folder/'terrain.png');previews.append(img.crop((0,0,256,176)).convert('RGB'))
  for penguin,drill,name in [(False,False,'normal'),(False,True,'drill'),(True,False,'penguin'),(True,True,'penguin_drill')]:
   data=ex.sprites(stage,v,penguin,drill);(folder/('sprites_'+name+'.bin')).write_bytes(data)
   if name=='normal':sprite_sheet(data).save(folder/'sprites.png')
  for third in range(3):
   for tile in range(256):
    pix=tile_indices(v,tile,third);tiles.setdefault(pix,[]).append([stage,third,tile]);colors[len(set(pix))]+=1
 (out/'source_tile_dictionary.bin').write_bytes(b''.join(tiles))
 (out/'source_tile_references.json').write_text(json.dumps([dict(sha256=hashlib.sha256(p).hexdigest(),references=r) for p,r in tiles.items()]))
 (out/'stage_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'compressed_streams.json').write_text(json.dumps(list(ex.streams.values()),indent=2)+'\n');(out/'mirror_records.json').write_text(json.dumps(ex.copy_records,indent=2)+'\n')
 contact=Image.new('RGB',(1024,528))
 for i,im in enumerate(previews):contact.paste(im,((i%4)*256,(i//4)*176))
 contact.save(out/'all_12_map_previews.png')
 report=dict(source_sha256=EXPECTED,map_records=12,terrain_columns=sum(m['columns'] for m in manifest),source_tile_occurrences=9216,unique_source_pixel_tiles=len(tiles),sprite_sets=48,compressed_streams=len(ex.streams),runtime_integration=False,source_hardware_vram_comparison='pending',color_counts_per_tile=dict(colors),limitations=['Map IDs are not twelve consecutive campaign stages. Return traversal and secret/interior maps require original progression events.','Static graphics extraction only. Enemy objects, collision behavior, bosses and cutscenes are not implemented.','VRAM snapshots and expanded maps are inspection files, not a proposed ROM representation.'])
 (ROOT/'reports/nemesis2_extraction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':extract()
