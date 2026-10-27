#!/usr/bin/env python3
"""Controller-level native integration checks. QA injection is labeled per case.
Not a proof of full campaign completion or hardware equivalence.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,sys
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);a=p.parse_args()
 rom=(ROOT/'build/native/Nemesis_Legends_CP0016.nes').read_bytes();out=ROOT/'reports/cp0016';out.mkdir(parents=True,exist_ok=True)
 checks=[]
 def check(name,ok,**info):
  checks.append(dict(name=name,passed=bool(ok),**info));print(name,ok,info)
  if not ok:raise AssertionError(name)
 def tap(n,button):n.buttons[0]={button};n.run(1);n.buttons[0]=set();n.run(1)
 with NES(a.core,rom,True) as n:
  n.run(180);check('title_boot',n.read(2,1)==b'\0');n.png(out/'title.png')
  tap(n,3);n.run(60);check('start_enters_gameplay',n.read(2,1)==b'\1')
  x=n.read(0x20,1)[0];n.buttons[0]={7};n.run(10);n.buttons[0]=set();check('right_moves_ship',n.read(0x20,1)[0]>x)
  world=n.read(6,3);tap(n,3);n.run(60);check('pause_freezes_world',n.read(2,1)==b'\2' and n.read(6,3)==world)
  tap(n,3);n.run(10);check('resume_advances_world',n.read(2,1)==b'\1' and n.read(6,3)!=world)
  # Separate assisted load case to reach dense encounters deterministically.
 with NES(a.core,rom,True) as n:
  n.run(180);tap(n,3);n.run(60)
  # Select original 60Hz gameplay via controller for all existing combat tests.
  tap(n,2);tap(n,2)
  check('original_60hz_mode_for_stress',n.read(0x520,1)==b'\x02')
  n.write(0x53,b'\1');n.buttons[0]={0} 
  n.run(600);kills=n.read(0x72e,2);check('native_shots_destroy_source_wave_enemies',int.from_bytes(kills,'little')>0,qa='invulnerability only',kills=int.from_bytes(kills,'little'))
  capsules=n.read(0x730,1)[0];check('whole_wave_drops_collectible_capsule',capsules>0,qa='invulnerability only',collected=capsules)
  n.png(out/'opening_combat.png')
  # Deliberate state injection tests upgrade control, not acquisition coverage.
  n.write(0x27,b'\1');tap(n,8);check('speed_powerup_requires_A_and_consumes_slot',n.read(0x22,1)[0]==1 and n.read(0x27,1)==b'\0',qa='one selected powerup slot')
  n.write(0x28,bytes([1,1,0,2,5]));n.buttons[0]={0,5};n.run(16);n.buttons[0]={0}
  lost=0;logic=0;worst=0
  for k in range(20):
   before=n.read(0x1b,2);n.run(100);after=n.read(0x1b,2)
   lost+=(after[1]-before[1])&255;logic+=(after[0]-before[0])&255;worst=max(worst,(after[1]-before[1])&255)
  check('double_missile_two_options_stress_remains_live',n.read(2,1)==b'\1' and logic==2000 and lost==0,qa='powerups and invulnerability injected',logic_frames=logic,missed_NMIs=lost,worst_100_frames=worst)
  n.png(out/'weapons_stress.png')
 with NES(a.core,rom,True) as n:
  n.run(180);tap(n,3);n.run(100);n.buttons[0]={5}
  initial=n.read(0x24,1)[0];dead=False;restarted=False
  for k in range(80):
   n.run(30);dead |= n.read(2,1)==b'\3'
   if n.read(0x24,1)[0]<initial:restarted=True;break
  check('ordinary_gameplay_can_die_and_respawn',dead and restarted,qa='none',lives_before=initial,lives_after=n.read(0x24,1)[0])
  n.png(out/'respawn.png')
 report=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,scope='Native Nemesis integration; not full campaign validation')
 (out/'native_integration_tests.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS',len(checks))
if __name__=='__main__':main()
