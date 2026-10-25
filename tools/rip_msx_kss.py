#!/usr/bin/env python3
"""Reference KSS extraction from the three supplied original MSX revisions.
Keeps original Z80 interpreters and original PSG/SCC score data. These are MSX
reference recordings, explicitly NOT NSF files and NOT NES conversions.
Entrypoint/config evidence: antxiko/*-disassembly tools/musica.py, inspected
2026-10-25; KSS bank/BIOS semantics checked in libgme/gme/Kss_Emu.cpp.
"""
from __future__ import annotations
import hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
CONFIG={
 'nemesis_msx':dict(banks=[0,1,7,8],frame=0x8063,request=0x4a22,init=[],scc=False,psg=0xb8,ram=[(0xe043,0xb8)],tracks=[(0x32,'Stage 1 Start'),(0x13,'Other Stages Start'),(0x3b,'Core Explosion'),(0x41,'Ending'),(0x47,'Player Death')]+[(x,'Score Sequence %02X'%x) for x in (0x16,0x19,0x29,0x31,0x33,0x34,0x35,0x36,0x37)]),
 'nemesis2_msx':dict(banks=[0,4,5,6],frame=0x6934,request=0x4ae4,init=[0x71ae],scc=True,psg=0xbf,ram=[(0xe1ae,0xff),(0xe1af,0xff),(0xe1a6,0xbf)]+[(a,1) for a in range(0xe1b0,0xe1ba)],tracks=[(0x3e,'Opening Sequence'),(0x3f,'Story Introduction'),(0x40,'Ending Sequence'),(0x41,'True Ending'),(0x3b,'Boss Destruction'),(0x28,'Warning'),(0x3a,'Score Sequence 3A'),(0x3d,'Score Sequence 3D'),(0x42,'Score Sequence 42')]+[(x,'Stage Score %02X'%x) for x in (0x29,0x2b,0x2c,0x2d,0x2e,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x5b)]),
 'salamander_msx':dict(banks=[0,4,5,6],frame=0x6978,request=0x4d6e,init=[],scc=True,psg=0xb8,ram=[],tracks=[(0x4e,'Konami Logo'),(0x2e,'Title'),(0x28,'Takeoff'),(0x48,'Ship Departure'),(0x1b,'Stage 1'),(0x1c,'Stage 2'),(0x1e,'Stage 3'),(0x1d,'Stage 4'),(0x1f,'Stage 5'),(0x20,'Stage 6'),(0x19,'Operation X'),(0x21,'Boss Battle'),(0x24,'Boss Destruction'),(0x27,'Player Death'),(0x2f,'Between Stages'),(0x22,'Sequence at 56C4'),(0x30,'Incomplete Ending'),(0x31,'True Ending'),(0x32,'Game Over'),(0x34,'Intro Window')])}

def generate():
 selected=json.loads((ROOT/'manifests/selected_sources.json').read_text());outputs=[]
 for slug,c in CONFIG.items():
  s=selected[slug];rom=(ROOT/s['path']).read_bytes()
  if hashlib.sha256(rom).hexdigest()!=s['sha256']:raise ValueError('Input hash mismatch')
  data=bytearray(0x8200)
  for slot,bank in enumerate(c['banks']):data[slot*8192:(slot+1)*8192]=rom[bank*8192:(bank+1)*8192]
  # Preserve caller stack; only $E000-$EFFF is initialized.
  code=bytearray.fromhex('f5 af 21 00 e0 11 01 e0 01 ff 0f 77 ed b0')
  for addr,v in c['ram']:code+=bytes([0x3e,v,0x32])+struct.pack('<H',addr)
  bankcode=bytes.fromhex('3e 05 32 00 90 3e 06 32 00 b0') if c['scc'] else b''
  code+=bankcode+bytes([0x3e,7,0xd3,0xa0,0x3e,c['psg'],0xd3,0xa1])
  for addr in c['init']:code+=b'\xcd'+struct.pack('<H',addr)
  code+=bytes.fromhex('f1 6f 26 00 11 00 c1 19 7e cd')+struct.pack('<H',c['request'])+b'\xc9'
  if len(code)>0xe0:raise ValueError('Wrapper overlaps play trampoline')
  data[0x8000:0x8000+len(code)]=code
  play=bankcode+b'\xc3'+struct.pack('<H',c['frame'])
  data[0x80e0:0x80e0+len(play)]=play
  data[0x8100:0x8100+len(c['tracks'])]=bytes(x[0] for x in c['tracks'])
  header=bytearray(16);header[:4]=b'KSCC';struct.pack_into('<HHHH',header,4,0x4000,len(data),0xc000,0xc0e0)
  if c['scc']:header[12:14]=bytes([5,0x82]);data+=rom[5*8192:7*8192]
  else:header[15]=4
  out=ROOT/'audio/msx_reference'/slug;out.mkdir(parents=True,exist_ok=True)
  f=out/(slug+'_original_driver.kss');f.write_bytes(header+data)
  info={'source':s,'kind':'MSX_original_driver_reference','nes_conversion':False,'not_an_nsf':True,'scc':c['scc'],'entrypoints':{k:c[k] for k in ['frame','request','init']},'tracks':[{'index':i,'command':n,'title':t,'title_status':'contextual_not_official'}for i,(n,t)in enumerate(c['tracks'])]}
  (out/'tracks.json').write_text(json.dumps(info,indent=2));outputs.append(f);print(f)
 return outputs
if __name__=='__main__':generate()
