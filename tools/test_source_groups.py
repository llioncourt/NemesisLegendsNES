#!/usr/bin/env python3
"""NES/FCEUmm source wave groups 4/5, with separate scoped test fixture.
Natural type-9 flock observed in stage 3; mixed group from stage 4 sampled
at an original group-bits segment using explicit *fixture-only* scroll override.
The latter is NOT a natural stage4 playthrough or source fidelity approval.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
ROM=ROOT/'build/native/Nemesis_Legends_CP0014.nes'
OUT=ROOT/'reports/cp0014';OUT.mkdir(exist_ok=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',default=str(ROOT/'toolchain/linux-x64/bin/fceumm_libretro.so'));a=p.parse_args()
 rom=ROM.read_bytes();r={'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':__doc__}
 with NES(a.core,rom,False) as n:
  n.run(180);n.buttons[0]={3};n.run(1);n.buttons[0]=set();n.run(40)
  for _ in range(2):n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
  n.write(0x53,b'\x01')  # QA invulnerability only
  n.buttons[0]={0}
  seen_flock=0;seen_type9=0;stage4=False
  for f in range(17500):
   st=n.read(0x1d,1)[0]
   if st==3:
    seen_flock=max(seen_flock,n.read(0x7c4,1)[0])
    if n.read(0x740,1)==b'\x09':seen_type9+=1
   if st==4:
    stage4=True;break
   n.run(1)
  assert stage4 and seen_flock>0,(stage4,seen_flock)
  r['natural_stage3']={'type9_spawned_at_least':seen_flock,'type9_first_slot_snapshot_frames':seen_type9,'stage4_reached':stage4,'assistance':'QA invulnerability'}
  # Unit-only fixture: source p03 A3E8 stage 4 group mask is $20 in
  # segment $180-$19F. Stage4's normal boss is still missing, so reach
  # this segment only by changing world/phase/camera while preserving the
  # production SpawnWaves/SpawnActor/ActorsFrame code. This is NOT gameplay.
  n.write(0x07,b'\x80\x01');n.write(0x3b,b'\x00')
  mixed=0
  for j in range(660):
   n.write(0x07,b'\x80\x01') # QA fixture pins original stage4 bit-5 segment
   n.write(0x3b,b'\x00') # fixture forces active state; bypass missing boss only here
   n.write(0x06,b'\x02') # no new column: avoid skipped unimplemented boss gate
   n.buttons[0]={0}
   n.run(1)
   mixed=max(mixed,n.read(0x7c5,1)[0])
  assert mixed>0,mixed
  r['fixture_stage4']={'mixed_spawned_at_least':mixed,'world_pinned':'$0180/frame','phase_pinned':0,
                       'camera_pinned':'$02/frame','is_full_stage_playthrough':False}
 (OUT/'source_group_tests.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
if __name__=='__main__':main()
