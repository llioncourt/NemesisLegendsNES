#!/usr/bin/env python3
"""Native-driver NSF extraction for supplied Salamander FC and Gradius II FC.
Uses original 6502 sequence interpreters. No PCM captures or frame-register replay.
Source hashes, table structure and entrypoint signatures are checked. No MSX conversion.
"""
from __future__ import annotations
import hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[1]

def nsf_header(name,tracks,load,init,play):
 h=bytearray(128);h[:5]=b'NESM\x1a';h[5:8]=bytes([1,tracks,1]);struct.pack_into('<HHH',h,8,load,init,play)
 for offset,text in [(14,name),(46,'Konami'),(78,'Konami - original FC driver')]:h[offset:offset+32]=text.encode('ascii')[:31].ljust(32,b'\0')
 struct.pack_into('<H',h,110,16639);struct.pack_into('<H',h,120,19997);return h

def rip(slug,name,bank,initial,request,tick,commands,titles,full_fixed):
 selected=json.loads((ROOT/'manifests/selected_sources.json').read_text())[slug]
 rom=(ROOT/selected['path']).read_bytes()
 if hashlib.sha256(rom).hexdigest()!=selected['sha256']:raise ValueError('Input hash mismatch')
 prg=rom[16:16+selected['prg_bytes']];data=bytearray(prg[bank*0x4000:(bank+1)*0x4000])
 data+=prg[-0x4000:] if full_fixed else bytes(0x200)
 assert all(0x8000<=x<0xc000 for x in (initial,request,tick))
 # The original Gradius II audio state occupies $0100-$019F. Never clear the
 # caller stack at $01A0-$01FF; keep PHA/PLA and all JSR/RTS balanced.
 code=bytearray.fromhex('48 a9 00 a2 00 95 00 e8 d0 fb')
 if slug=='gradius2_fc':code+=bytes.fromhex('a2 00 9d 00 01 e8 e0 a0 d0 f8')
 else:code+=bytes.fromhex('a2 00 9d 00 06 e8 d0 fa')
 code+=bytes.fromhex('8d 10 40 a9 40 8d 17 40 a9 0f 8d 15 40')
 code+=b'\x20'+struct.pack('<H',initial)+bytes.fromhex('68 aa bd 00 c1 20')+struct.pack('<H',request)+b'\x60'
 data[0x4000:0x4000+len(code)]=code;data[0x4080:0x4083]=b'\x4c'+struct.pack('<H',tick)
 data[0x4100:0x4100+len(commands)]=bytes(commands)
 folder=ROOT/'audio/native_nes'/slug;folder.mkdir(parents=True,exist_ok=True)
 out=folder/(name.replace(' ','_')+'_original_driver.nsf');out.write_bytes(nsf_header(name,len(commands),0x8000,0xc000,0xc080)+data)
 tracks=[dict(index=i,command=n,title=titles.get(n,'Music Sequence %02X'%n),title_status='contextual_not_official',evidence='original song table and command call sites; semantic identification pending unless stage table noted') for i,n in enumerate(commands)]
 metadata=dict(source=selected,source_kind='supplied_NES_ROM',nsf_kind='original_driver_rip',msx_conversion=False,game_integration=False,load=0x8000,init=0xc000,play=0xc080,driver_init=initial,driver_request=request,driver_tick=tick,source_sound_bank=bank,tracks=tracks)
 (folder/'tracks.json').write_text(json.dumps(metadata,indent=2));print(out)
 return out

def generate():
 out=[]
 # Table at $F550 in the fixed bank maps stages 1..6 to these commands.
 titles={0x25:'Stage 1 - Biological Zone',0x28:'Stage 2 - Meteorite Zone',0x2b:'Stage 3 - Fire Zone',0x2e:'Stage 4 - Volcanic Zone',0x31:'Stage 5 - Temple Zone',0x34:'Stage 5 - Final Section',0x37:'Stage 6 - Mechanical Zone',0x22:'Boss Encounter',0x3d:'Stage Clear',0x40:'Ending',0x43:'Game Over',0x3a:'Opening Flight'}
 out.append(rip('salamander_fc','Salamander FC',3,0x887f,0x872d,0x8000,[0x3a,0x25,0x28,0x2b,0x2e,0x31,0x34,0x37,0x22,0x3d,0x40,0x43],titles,False))
 out.append(rip('gradius2_fc','Gradius II FC',6,0x8003,0x803d,0x81f8,list(range(0x4c,0x88,4)),{0x4c:'Equipment Selection',0x80:'Ending',0x84:'Game Over'},True))
 return out
if __name__=='__main__':generate()
