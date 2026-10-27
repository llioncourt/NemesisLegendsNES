#!/usr/bin/env python3
"""Encode a custom title as real NES 2bpp CHR, nametable and palette data.
This produces an integration asset, NOT a runnable ROM or an emulator screenshot.
"""
from __future__ import annotations
import hashlib,json,pathlib,random
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1]
FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01110'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
' ':['00000']*7}
PAL=[(0,0,0),(48,50,236),(236,238,236),(212,136,32)]
def text(im,s,y,scale=1,color=2,x=None):
 if x is None:x=(256-(len(s)*6-1)*scale)//2
 d=ImageDraw.Draw(im)
 for ch in s:
  for yy,row in enumerate(FONT[ch]):
   for xx,b in enumerate(row):
    if b=='1':d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=color)
  x+=6*scale

def encode(im):
 tiles=[bytes(16)];lookup={tiles[0]:0};nt=bytearray()
 for ty in range(30):
  for tx in range(32):
   low=bytearray();high=bytearray()
   for y in range(8):
    a=b=0
    for x in range(8):
     v=im.getpixel((tx*8+x,ty*8+y));a=(a<<1)|(v&1);b=(b<<1)|((v>>1)&1)
    low.append(a);high.append(b)
   tile=bytes(low+high)
   if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
   if lookup[tile]>255:raise ValueError('Title exceeds one 4 KiB background pattern bank')
   nt.append(lookup[tile])
 return b''.join(tiles).ljust(4096,b'\0'),bytes(nt)+bytes(64),len(tiles)
def decode(chrdata,nt):
 im=Image.new('P',(256,240));im.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-12))
 for y in range(240):
  for x in range(256):
   tile=nt[(y//8)*32+x//8];o=tile*16+y%8;b=7-x%8;im.putpixel((x,y),((chrdata[o]>>b)&1)|(((chrdata[o+8]>>b)&1)<<1))
 return im

def generate():
 out=ROOT/'assets/title';out.mkdir(parents=True,exist_ok=True);im=Image.new('P',(256,240));im.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-12));d=ImageDraw.Draw(im);rng=random.Random(742751758764)
 # Stars use a bounded vocabulary; keep the title bands clear of random pixels.
 for y in list(range(0,40,8))+list(range(128,184,8))+list(range(216,240,8)):
  for x in range(0,256,8):
   if rng.randrange(4)==0:
    ox,oy=rng.choice([(1,1),(5,2),(3,6)]);d.point((x+ox,y+oy),fill=rng.choice([1,1,2]))
 text(im,'SILICON FORGE',17,color=3)
 d.line((24,41,231,41),fill=1);d.line((32,43,223,43),fill=1)
 text(im,'NEMESIS',55,4,1);text(im,'NEMESIS',52,4,2)
 text(im,'LEGENDS',91,4,1);text(im,'LEGENDS',88,4,3)
 text(im,'THE BURTON LEGACY',126,color=2)
 # Custom fighter silhouette, kept as tile art rather than a high-resolution mockup.
 d.polygon([(102,159),(118,153),(124,142),(129,142),(132,153),(150,159),(139,163),(136,173),(127,167),(118,173),(116,163)],fill=1)
 d.polygon([(109,159),(122,156),(125,147),(128,147),(130,157),(141,160),(128,163)],fill=2)
 d.rectangle((125,154,128,159),fill=3);d.line((121,168,123,179),fill=3);d.line((132,168,130,179),fill=3)
 d.line((39,187,216,187),fill=1)
 for x in (40,96,152,216):d.rectangle((x-1,185,x+1,189),fill=3)
 text(im,'PRESS START',199,color=2);text(im,'THE COMPLETE MSX SAGA',222,color=1)
 # The subtitle describes the intended project scope, not this checkpoint's status.
 chrdata,nt,count=encode(im);recovered=decode(chrdata,nt)
 if recovered.tobytes()!=im.tobytes():raise AssertionError('Title CHR/nametable roundtrip differs')
 (out/'title.chr').write_bytes(chrdata);(out/'title.nam').write_bytes(nt);(out/'title.pal').write_bytes(bytes([0x0f,0x12,0x30,0x27])*4)
 recovered.save(out/'title_native_asset.png');recovered.resize((768,720),Image.Resampling.NEAREST).save(out/'title_preview_3x.png')
 report=dict(status='native_title_asset_generator_output',runnable_rom=False,emulator_screenshot=False,pixel_dimensions=[256,240],unique_tiles=count,chr_bytes=4096,nametable_bytes=1024,palette_bytes=16,bg_palette_count=1,pattern_banks_4k=1,roundtrip_exact=True,chr_sha256=hashlib.sha256(chrdata).hexdigest(),notes=['Preview RGB approximates a 2C02 palette. Actual console display depends on video palette.','This generator emits artwork only. Runtime title/input status is recorded in manifests/content_coverage.json.','This preview is not an emulator capture; see reports/cp0004/title.png for runtime evidence.'])
 (out/'title.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':generate()
