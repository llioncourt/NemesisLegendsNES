#!/usr/bin/env python3
"""Emulated source-target route from controller-started stage 1; QA invulnerability only.
Does not claim stage-3 boss/content fidelity. Tests stage3 -> bonus10 -> stage4.
"""
import argparse,json,hashlib,pathlib,sys
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
ROM=ROOT/'build/native/Nemesis_Legends_CP0013.nes'
CORE=ROOT/'toolchain/linux-x64/bin/fceumm_libretro.so'
OUT=ROOT/'reports/cp0013';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--core',default=str(CORE));args=parser.parse_args()
labels={}
for line in (ROOT/'build/native/native.lbl').read_text().splitlines():
 parts=line.split()
 if len(parts)==3 and parts[0]=='al':labels[parts[2].lstrip('.')]=int(parts[1],16)
assert 'S3_State' in labels, 'native stage-three state not linked'
state_addr=labels['S3_State']
results={}
for route in ('normal','secret'):
 with NES(args.core,ROM.read_bytes(),False) as n:
  n.run(180);n.buttons[0]={3};n.run(1);n.buttons[0]={0};n.run(40)
  for _ in range(2):
   n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
  n.write(0x53,b'\x01')  # Explicit QA invulnerability, not a legitimate playthrough
  stage3=None;bonus=None;contact=None;midboss=None;midboss_cleared=False;second_boss=None;end=None;seen=False;collected=False;step=0
  for step in range(24500):
   st=n.read(0x1d,1)[0]; phase=n.read(0x3b,1)[0];w=int.from_bytes(n.read(7,2),'little')
   s3=n.read(state_addr,7)
   if st==3:
    if stage3 is None:stage3=step
    seen|=s3[0]==1
    if phase==5 and midboss is None:midboss=step
    midboss_cleared|=s3[5]!=0
    if s3[6] and phase==5 and second_boss is None: second_boss=step
    collected|=s3[3]!=0
    if phase==11 and contact is None:contact=step
    if route=='secret':
     y=n.read(0x21,1)[0]
     n.buttons[0]={4} if y>48 else {5} if y<48 else set()
    else:n.buttons[0]={0}
    if route=='normal' and phase==12:
     raise AssertionError('old artificial stage-three gate still active')
   elif st==10:
    if bonus is None:bonus=step
    n.buttons[0]=set()
   elif st==4 and (bonus is not None or route=='normal'):
    end={'frame':step,'stage':st,'bonus_entry':bonus,'world':w,'target_seen':seen,'collected':collected};break
   else:n.buttons[0]={0}
   n.run(1)
  if route=='normal':
   assert stage3 is not None and end and end['stage']==4 and not collected and midboss is not None and midboss_cleared and second_boss is not None,(stage3,midboss,second_boss,end)
  else:
   assert stage3 is not None and bonus is not None and collected and end and end['stage']==4 and bonus-contact==64 and midboss is not None and midboss_cleared,(stage3,midboss,bonus,contact,end)
  results[route]={'stage3_frame':stage3,'midboss_frame':midboss,'midboss_cleared':midboss_cleared,'second_boss_frame':second_boss,'bonus_frame':bonus,'contact_frame':contact,'end':end,'frames':step}
(OUT/'stage3_emulation.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'assisted':True,'source_target':'p03 B09A/B0CB/B0DD/B123','results':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
