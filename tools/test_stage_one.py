#!/usr/bin/env python3
"""Controller-driven first-stage integration runs on the unmodified FCEUmm core.
Invulnerability is explicitly injected. No stage, world-distance, boss-health,
spawn, timer, or clear event is injected. Separate post-kill power-state fixture
checks transfer to stage two. This does NOT establish four-game completion.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);a=p.parse_args()
 rom=(ROOT/'build/native/Nemesis_Legends_CP0014.nes').read_bytes();out=ROOT/'reports/cp0014';out.mkdir(parents=True,exist_ok=True)
 runs=[]
 for kind in ('destroy_core','source_timeout'):
  trace=[];closed_hp=[];hits=[];cleared=False;lastphase=-1;lastmiss=0;missed=0;injected=False;carry=None;seen_mid=False;volcano=0;stage2frame=None
  with NES(a.core,rom,True) as n:
   n.run(100);n.buttons[0]={3};n.run(1);n.buttons[0]={0};n.run(40)
   # Source-speed QA: select 60Hz via two physical SELECT presses.
   for _ in range(2):
    n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
   assert n.read(0x520,1)==b'\x02'
   n.buttons[0]={0}  # preserve the original first-stage fire-through input
   n.write(0x53,b'\x01');lastmiss=n.read(0x1c,1)[0]
   for tick in range(7000):
    phase=n.read(0x3b,1)[0];stage=n.read(0x1d,1)[0];hp=n.read(0x54,1)[0];opening=n.read(0x58,1)[0]
    m=n.read(0x1c,1)[0];missed+=(m-lastmiss)&255;lastmiss=m
    bs=n.read(0x760,17);seen_mid|=bool(bs[9]);volcano=max(volcano,int.from_bytes(bs[10:12],'little'))
    if stage==2 and n.read(0x18,1)==b'\x01':
     stage2frame=tick;carry=list(n.read(0x28,5));n.buttons[0]=set();n.run(30);n.png(out/(kind+'_stage_two.png'));cleared=True;break
    if phase!=lastphase:
     state=dict(frame=tick,phase=phase,world=int.from_bytes(n.read(7,2),'little'),boss_hp=hp,face=opening)
     trace.append(state);print(kind,state,flush=True);lastphase=phase
     if phase in (2,3,6,7):n.png(out/(kind+f'_phase_{phase}.png'))
    if phase>=5:
     if kind=='destroy_core':
      target=n.read(0x55,1)[0]+24;y=n.read(0x21,1)[0]
      n.buttons[0]=({0} if tick&1 else set()) | ({7} if n.read(0x20,1)[0]<136 else set()) | ({4} if y>target+1 else {5} if y<target-1 else set())
     else:n.buttons[0]=set()
    if phase==6:
     if opening and hp==22:closed_hp.append(tick)
     if not opening and hp<22:hits.append((tick,hp))
    if kind=='destroy_core' and phase==7 and not injected:
     assert hp==0,'Destruction route reached aftermath without a destroyed core'
     # This separate fixture happens only AFTER the boss is actually defeated.
     n.write(0x28,bytes([2,1,0,2,10]));n.write(0x22,b'\x03');injected=True
    n.run(1)
   phase6=next((s['frame'] for s in trace if s['phase']==6),None)
   phase7=next((s for s in trace if s['phase']==7),None)
   checks=dict(reached_stage_two=cleared,mid_encounter_spawned=seen_mid,volcano_emitted_source_particles=volcano>0,
               core_entered_with_22_hp=any(s['phase']==6 and s['boss_hp']==22 for s in trace),
               initially_closed_core_did_not_take_damage=bool(closed_hp))
   if kind=='destroy_core':
    checks.update(core_defeated_by_projectile_damage=bool(hits) and phase7 is not None and phase7['boss_hp']==0,
                  powerups_survive_chapter_one_stage_transition=carry==[2,1,0,2,10])
   else:
    checks.update(no_shooting_keeps_full_core_hp=phase7 is not None and phase7['boss_hp']==22,
                  original_720_frame_timeout_is_preserved=phase7 is not None and phase6 is not None and phase7['frame']-phase6==720)
   run=dict(name=kind,qa=['invulnerability']+(['post-kill powerup transfer fixture'] if injected else []),trace=trace,
            stage_two_frame=stage2frame,volcano_particles_created=volcano,missed_NMIs=missed,checks=checks,passed=all(checks.values()))
   runs.append(run)
   print('RUN',kind,'PASS',run['passed'],'LAG',missed,'CHECKS',checks,flush=True)
 report=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__,runs=runs,passed=all(x['passed'] for x in runs))
 (out/'stage_one_integration.json').write_text(json.dumps(report,indent=2)+'\n')
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
