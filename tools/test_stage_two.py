#!/usr/bin/env python3
"""Native stage-two MSX route regression on the unmodified FCEUmm libretro core.
Two controller-driven paths run through stage one; only the player's
invulnerability is injected (and documented). No phase, boss health, distance,
rock, timer, target, route, or stage transition is injected. Does NOT validate
the incomplete stage-three onward campaign or full source sprite fidelity.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
S2=0x510

def u16(v,a):return v[a]|(v[a+1]<<8)

def run(core,rom,kind,out):
 trace=[];stage2=False;seen_target=False;rain_started=None;rain_ended=None
 first_bonus=None;boss_started=None;boss_over=None;missed=0;lastmiss=0
 stage_two_entry=None;stage3=None;stage9=None;state_exit=None;max_spawn=0;max_bonus_world=0;secret_at_entry=None
 snapshots={};s2_at_rain=None;state_boss=None;initial_world=None
 with NES(core,rom,True) as n:
  n.run(180);n.buttons[0]={3};n.run(1);n.buttons[0]={0};n.run(40)
  # Original source cadence for source-duration regression, selected with
  # real controller inputs. The default 30Hz accessibility mode is separate.
  for _ in range(2):
   n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
  assert n.read(0x520,1)==b'\x02'
  n.write(0x53,b'\x01') # explicit assisted invulnerability, NOT gameplay proof
  n.buttons[0]={0}     # shoot actual first-stage boss to unlock stage two
  last_state=None
  for tick in range(15000):
   stage=n.read(0x1d,1)[0];phase=n.read(0x3b,1)[0]
   world=int.from_bytes(n.read(7,2),'little')
   state=n.read(S2,16)
   m=n.read(0x1c,1)[0];missed+=(m-lastmiss)&255;lastmiss=m
   if stage==2 and not stage2:
    stage2=True;stage_two_entry=tick;initial_world=world;n.png(out/(kind+'_stage2_entry.png'))
   if stage==2:
    if kind=='secret':
     y=n.read(0x21,1)[0]
     n.buttons[0]={5} if y<136 else {4} if y>136 else set()
    else:n.buttons[0]={0} # Keep clearing ordinary enemy slots with normal weapon fire
    if state[2]==1:seen_target=True
    if phase==9 and rain_started is None:
     rain_started=tick;s2_at_rain=state.hex();n.png(out/'normal_rock_rain_start.png')
    if rain_started is not None and phase==1 and rain_ended is None:rain_ended=tick
    if phase==10 and first_bonus is None:
     first_bonus=tick;n.png(out/'secret_target_contact.png')
    if phase==5 and boss_started is None:
     boss_started=tick;state_boss=state.hex();n.png(out/'normal_big_core_entry.png')
    if phase==7 and boss_over is None:boss_over=tick
    if kind=='normal' and world==0x170 and 'rock_wall' not in snapshots:
     n.png(out/'normal_rock_wall.png');snapshots['rock_wall']=tick
   if stage==9:
    if stage9 is None:
     stage9=tick;secret_at_entry=state.hex();n.png(out/'secret_bonus_stage9.png')
    max_bonus_world=max(max_bonus_world,world)
    n.buttons[0]=set()
    if world>=0x80 and 'bonus_terrain' not in snapshots:
     n.png(out/'secret_bonus_terrain.png');snapshots['bonus_terrain']=tick
   if (stage,phase)!=last_state:
    if stage in (2,3,9):trace.append(dict(frame=tick,stage=stage,phase=phase,world=world,
                rock_attempts=u16(state,8),rock_spawned=u16(state,10),wall_events=state[12],
                target_hits=state[13],rain_finished=state[15]))
    last_state=(stage,phase)
   max_spawn=max(max_spawn,u16(state,10))
   if stage==3:stage3=tick;state_exit=state.hex();break
   n.run(1)
  checks=dict(first_stage_reached_second=stage_two_entry is not None,
              second_stage_ran_for_source_content=stage_two_entry is not None and tick-stage_two_entry>500,
              no_missed_NMI_during_the_assisted_path=missed==0,
              source_target_spawned=seen_target,
)
  if kind=='normal':
   end=bytes.fromhex(state_boss) if state_boss else bytes(16)
   checks.update(at_least_one_source_rock_materialized=max_spawn>0,
     six_source_rock_wall_events=end[12]==6,
     wall_and_rain_attempts_source_counter=u16(end,8)==74,
     rock_pool_did_not_reject_every_request=u16(end,10)>=12,
     natural_rain_phase_reached=rain_started is not None,
     original_900_frame_rain_duration=rain_started is not None and rain_ended is not None and rain_ended-rain_started==900,
     normal_boss_entered=boss_started is not None and boss_over is not None,
     natural_boss_sequence_reached_third_stage=stage3 is not None and stage9 is None,
     original_target_not_collected=end[13]==0)
  else:
   end=bytes.fromhex(secret_at_entry) if secret_at_entry else bytes(16)
   checks.update(source_bonus9_terrain_reaches_original_event_distance=max_bonus_world>=0x11f,
     secret_stage9_returns_to_stage3_without_injection=stage3 is not None and stage9 is not None and stage3-stage9>1800,
     contact_causes_64_frame_bonus_freeze=first_bonus is not None and stage9 is not None and stage9-first_bonus==64,
     source_target_collided=end[13]==1,
     transition_to_original_bonus_stage9=stage9 is not None,
     no_rain_after_secret_interruption=rain_started is None)
  return dict(name=kind,qa='Player invulnerability enabled at stage one; no other state injection',
              rom_sha256=hashlib.sha256(rom).hexdigest(),phase_transitions=trace,
              stage_two_entry=stage_two_entry,stage_three_entry=stage3,stage_nine_entry=stage9,
              rain_started=rain_started,rain_ended=rain_ended,
              first_bonus=first_bonus,boss_started=boss_started,boss_over=boss_over,
              rock_counter_at_boss=state_boss,rock_counter_at_exit=state_exit,
              secret_rock_counter_at_entry=secret_at_entry,bonus9_max_world=max_bonus_world,
              max_spawned_rock_count=max_spawn,missed_NMIs=missed,
              checks=checks,passed=all(checks.values()))

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);a=p.parse_args()
 rom=(ROOT/'build/native/Nemesis_Legends_CP0012.nes').read_bytes()
 out=ROOT/'reports/cp0012';out.mkdir(parents=True,exist_ok=True)
 runs=[run(a.core,rom,name,out) for name in ('normal','secret')]
 report=dict(checkpoint='CP0008',scope=__doc__,rom_sha256=hashlib.sha256(rom).hexdigest(),
             runs=runs,passed=all(r['passed'] for r in runs))
 (out/'stage_two_integration.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in runs:print(r['name'],'PASS' if r['passed'] else 'FAIL',r['checks'],'missed',r['missed_NMIs'],flush=True)
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
