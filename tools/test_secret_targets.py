#!/usr/bin/env python3
"""Real FCEUmm controller routes for inter-stage secret targets; assisted invulnerability.
Counts recorded in source MSX E06C/E06D semantics; no forced phase/stage/target state.
"""
import argparse,json,pathlib,hashlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
ROM=ROOT/'build/native/Nemesis_Legends_CP0014.nes'
CORE=ROOT/'toolchain/linux-x64/bin/fceumm_libretro.so'
OUT=ROOT/'reports/cp0014';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--core',default=str(CORE));args=parser.parse_args()
labels={}
for l in (ROOT/'build/native/native.lbl').read_text().splitlines():
 p=l.split()
 if len(p)==3 and p[0]=='al':labels[p[2].lstrip('.')]=int(p[1],16)
A=labels['Target_State']
results={}
for route in ('all_three','none'):
 with NES(args.core,ROM.read_bytes(),False) as n:
  n.run(180);n.buttons[0]={3};n.run(1);n.buttons[0]=set();n.run(40)
  for _ in range(2):n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
  n.write(0x53,b'\x01')
  stage4=None;bonus11=None;stage5=None;hit_events=[];stops=0;seen=set();last_hits=0;maxmiss=0
  for f in range(28000):
   st=n.read(0x1d,1)[0];phase=n.read(0x3b,1)[0];world=int.from_bytes(n.read(7,2),'little')
   tg=n.read(A,14)
   if tg[6]!=last_hits:
    hit_events.append(dict(frame=f,stage=st,type=tg[4],count=tg[5],hits=tg[6],world=world))
    last_hits=tg[6]
   if tg[0]:seen.add((st,tg[0]))
   if st==4 and stage4 is None:stage4=f
   if st==11 and bonus11 is None:bonus11=f
   if st==5:
    stage5=f;break
   y=n.read(0x21,1)[0]
   # Align by ordinary directional controller inputs, no RAM teleports.
   if route=='all_three' and st==1:dest=136
   elif route=='all_three' and st==4:dest=16
   else:dest=76
   vertical=({4} if y>dest+1 else {5} if y<dest-1 else set())
   # Aim/firing through existing enemy routes as in ordinary QA.
   n.buttons[0]=vertical|({0} if st in (1,2,3,4) else set())
   n.run(1)
  results[route]=dict(stage4_frame=stage4,stage5_frame=stage5,bonus11_frame=bonus11,
                      events=hit_events,seen=list(map(list,sorted(seen))),phase=phase,world=world,
                      stopped=stops,frame=f,target=list(tg))
  print(route,results[route],flush=True)
  if route=='all_three':
   assert stage4 is not None and bonus11 is not None and stage5 is not None,(stage4,bonus11,stage5,hit_events)
   assert [e['type'] for e in hit_events]==[2,3,4],hit_events
  else:
   # Without the three touches the normal stage-4 end sequence (CP0012) leads to stage 5.
   assert stage4 is not None and bonus11 is None and stage5 is not None,(stage4,bonus11,stage5)
report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),
            assisted='QA invulnerability only',results=results)
(OUT/'secret_targets.json').write_text(json.dumps(report,indent=2)+'\n')
