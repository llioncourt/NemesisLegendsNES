#!/usr/bin/env python3
"""Execute the BUILT NMI's supported 6502 instruction subset to count its cycles.
This is a bounded instruction-level timing check, NOT a replacement NES emulator.
Only the production NMI path is executed. Unknown opcodes fail. DMA is charged
514 cycles, and 14 cycles cover interrupt entry + worst interrupted instruction.
Audio is disabled here because it runs after the final video-register write.
Gameplay checks independently run the unmodified FCEUmm core.
"""
from __future__ import annotations
import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Counter6502:
 def __init__(self,rom):
  self.m=bytearray(65536);n=rom[4]*16384;self.m[0xc000:]=rom[16+n-16384:16+n]
  self.pc=self.word(0xfffa);self.a=self.x=self.y=0;self.sp=0xfa;self.p=0x24
  self.cycles=14;self.video=[];self.stopped=False;self.steps=0
 def word(self,a):return self.m[a]|self.m[(a+1)&65535]<<8
 def fetch(self):v=self.m[self.pc];self.pc=(self.pc+1)&65535;return v
 def fword(self):a=self.fetch();return a|self.fetch()<<8
 def flag(self,mask,value):self.p=(self.p|mask) if value else (self.p&~mask)
 def nz(self,v):v&=255;self.flag(2,v==0);self.flag(128,v&128);return v
 def push(self,v):self.m[0x100+self.sp]=v&255;self.sp=(self.sp-1)&255
 def pop(self):self.sp=(self.sp+1)&255;return self.m[0x100+self.sp]
 def read(self,a):return 0x80 if a==0x2002 else self.m[a]
 def write(self,a,v):
  self.m[a]=v&255
  if a==0x4014:self.cycles+=514
  if a in (0x2000,0x2001,0x2003,0x2005,0x2006,0x2007,0x4014) or 0x5c00<=a<=0x5fff:self.video.append((a,self.cycles))
 def step(self):
  origin=self.pc;o=self.fetch();self.steps+=1
  if o==0x40:self.cycles+=6;self.stopped=True;return
  if o in (0x48,0x68,0x08,0x28):
   if o==0x48:self.push(self.a);self.cycles+=3
   elif o==0x68:self.a=self.nz(self.pop());self.cycles+=4
   elif o==0x08:self.push(self.p|0x30);self.cycles+=3
   else:self.p=self.pop();self.cycles+=4
   return
  if o in (0x8a,0x98,0xaa,0xa8):
   if o==0x8a:self.a=self.nz(self.x)
   elif o==0x98:self.a=self.nz(self.y)
   elif o==0xaa:self.x=self.nz(self.a)
   else:self.y=self.nz(self.a)
   self.cycles+=2;return
  if o in (0xe8,0xca,0xc8,0x88):
   if o==0xe8:self.x=self.nz(self.x+1)
   elif o==0xca:self.x=self.nz(self.x-1)
   elif o==0xc8:self.y=self.nz(self.y+1)
   else:self.y=self.nz(self.y-1)
   self.cycles+=2;return
  if o in (0x18,0x38):self.flag(1,o==0x38);self.cycles+=2;return
  if o in (0xd0,0xf0,0x90,0xb0,0x10,0x30):
   offset=self.fetch();mask={0xd0:2,0xf0:2,0x90:1,0xb0:1,0x10:128,0x30:128}[o]
   take=bool(self.p&mask)==(o in (0xf0,0xb0,0x30));self.cycles+=2
   if take:
    dest=(self.pc+(offset if offset<128 else offset-256))&65535
    self.cycles+=1+((dest^self.pc)&0xff00!=0);self.pc=dest
   return
  if o in (0x4c,0x6c):
   a=self.fword();self.pc=a if o==0x4c else self.m[a]|self.m[(a&0xff00)|((a+1)&255)]<<8
   self.cycles+=3 if o==0x4c else 5;return
  if o==0x20:
   a=self.fword();ret=self.pc-1;self.push(ret>>8);self.push(ret);self.pc=a;self.cycles+=6;return
  if o==0x60:self.pc=((self.pop()|self.pop()<<8)+1)&65535;self.cycles+=6;return
  if o in (0xa9,0xa2,0xa0):
   v=self.nz(self.fetch());self.cycles+=2
   if o==0xa9:self.a=v
   elif o==0xa2:self.x=v
   else:self.y=v
   return
  # Opcode -> addressing form, base cycles. Page penalties apply to reads only.
  forms={
   0xa5:('zp',3),0xad:('abs',4),0xbd:('ax',4),0xb9:('ay',4),0xb1:('iy',5),
   0xa6:('zp',3),0xae:('abs',4),0xa4:('zp',3),0xac:('abs',4),
   0x85:('zp',3),0x8d:('abs',4),0x9d:('ax',5),0x99:('ay',5),0x91:('iy',6),
   0x86:('zp',3),0x8e:('abs',4),0x84:('zp',3),0x8c:('abs',4),
   0xe6:('zp',5),0xee:('abs',6),0xc6:('zp',5),0xce:('abs',6),
   0x2c:('abs',4),0x24:('zp',3),0xc5:('zp',3),0xcd:('abs',4),0xe4:('zp',3),0xec:('abs',4),
   0x65:('zp',3),0x6d:('abs',4)}
  store=o in (0x85,0x8d,0x9d,0x99,0x91,0x86,0x8e,0x84,0x8c)
  if o in forms:
   form,cycles=forms[o];base=self.fetch() if form in ('zp','iy') else self.fword()
   if form=='iy':base=self.m[base]|self.m[(base+1)&255]<<8
   a=(base+(self.x if form=='ax' else self.y if form in ('ay','iy') else 0))&65535
   self.cycles+=cycles+(not store and form in ('ax','ay','iy') and (a^base)&0xff00!=0)
   if store:self.write(a,self.x if o in (0x86,0x8e) else self.y if o in (0x84,0x8c) else self.a);return
   v=self.read(a)
   if o in (0xa5,0xad,0xbd,0xb9,0xb1):self.a=self.nz(v);return
   if o in (0xa6,0xae):self.x=self.nz(v);return
   if o in (0xa4,0xac):self.y=self.nz(v);return
   if o in (0xe6,0xee,0xc6,0xce):self.write(a,self.nz(v+(1 if o in (0xe6,0xee) else -1)));return
   if o in (0x2c,0x24):self.flag(2,self.a&v==0);self.flag(128,v&128);self.flag(64,v&64);return
   if o in (0xc5,0xcd,0xe4,0xec):
    n=self.x if o in (0xe4,0xec) else self.a;self.nz(n-v);self.flag(1,n>=v);return
   if o in (0x65,0x6d):self.add(v);return
  if o in (0x69,0x29,0x09,0x49,0xc9,0xe0,0xc0):
   v=self.fetch();self.cycles+=2
   if o==0x69:self.add(v)
   elif o==0x29:self.a=self.nz(self.a&v)
   elif o==0x09:self.a=self.nz(self.a|v)
   elif o==0x49:self.a=self.nz(self.a^v)
   else:
    n=self.a if o==0xc9 else self.x if o==0xe0 else self.y;self.nz(n-v);self.flag(1,n>=v)
   return
  raise AssertionError(f'Unsupported opcode {o:02X} at {origin:04X}; extend bounded checker explicitly')
 def add(self,v):
  n=self.a+v+(self.p&1);self.flag(64,~(self.a^v)&(self.a^n)&128);self.flag(1,n>255);self.a=self.nz(n)
 def run(self):
  while not self.stopped and self.steps<20000:self.step()
  if not self.stopped:raise AssertionError('NMI did not return')
  return self.cycles

def main():
 rom=(ROOT/'build/native/Nemesis_Legends_CP0012.nes').read_bytes();results=[]
 cases=[('idle',0,0,0,0),('hud',0,1,0,0),('column_and_deferred_hud',1,1,0,0),
        ('boss_vertical_and_deferred_hud',0,1,11,9),('boss_horizontal_and_deferred_hud',0,1,12,8)]
 for name,col,hud,w,h in cases:
  c=Counter6502(rom);m=c.m;m[1]=1;m[2]=1;m[0x18]=1;m[0x19]=0;m[0x1a]=0;m[9]=col;m[0xa]=31;m[0x5a]=hud
  m[0x76]=int(w>0);m[0x6aa0]=w;m[0x6aa1]=h
  for i in range(h):m[0x6a80+i]=(32*i)&255;m[0x6a90+i]=0x21+((32*i)>>8)
  cycles=c.run();last=max((n for a,n in c.video),default=0)
  row=dict(case=name,cycles_including_entry_and_max_dma=cycles,last_video_write_cycle=last,
           ntsc_vblank_budget_cycles=2273,margin_cycles=2273-last,video_writes=len(c.video),passed=last<=2273)
  print(row);results.append(row)
 c=Counter6502(rom);m=c.m;m[1]=m[2]=m[0x18]=1;m[0x76]=1;m[0x6aa0]=11;m[0x6aa1]=12
 for i in range(12):m[0x6a80+i]=(32*i)&255;m[0x6a90+i]=0x21+((32*i)>>8)
 c.run();negative_last=max((n for _,n in c.video),default=0)
 negative=dict(change='oversized twelve-row boss update, outside the production bound',last_video_write_cycle=negative_last,rejected=negative_last>2273)
 assert negative['rejected'], 'Timing negative control was not rejected'
 out=dict(negative_control=negative,assumptions=['NTSC timing','No DMC sample DMA during the measured video transfer','Worst-case OAM DMA charged at 514 cycles'],rom_sha256=hashlib.sha256(rom).hexdigest(),method=__doc__,cases=results,passed=all(x['passed'] for x in results))
 (ROOT/'reports/cp0012/vblank_budget.json').write_text(json.dumps(out,indent=2)+'\n')
 if not out['passed']:raise SystemExit('Video writes exceed NTSC vblank budget')
if __name__=='__main__':main()
