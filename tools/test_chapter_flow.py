#!/usr/bin/env python3
"""Structural campaign progression for chapters without ported stage logic:
reaching a map's source scroll end hands the clear event to the campaign
module, which loads the next map. Driven through the cheat menu (GAME, STAGE,
WARP TO END) with QA invincibility; no RAM writes.
"""
import argparse,hashlib,json,pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
ROM=ROOT/'build/native/Nemesis_Legends_CP0016.nes'
CORE=ROOT/'toolchain/linux-x64/bin/fceumm_libretro.so'
OUT=ROOT/'reports/cp0016';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--core',default=str(CORE));args=parser.parse_args()
B=NES.BUTTONS
def tap(n,btn,hold=2,gap=3):
 n.buttons[0]={B[btn]};n.run(hold);n.buttons[0]=set();n.run(gap)
def code(n):
 for k in ['UP','UP','DOWN','DOWN','LEFT','RIGHT','LEFT','RIGHT','B','A']:tap(n,k)
def st(n):return dict(mode=n.read(2,1)[0],chapter=n.read(0x7f,1)[0],stage=n.read(0x1d,1)[0],world=int.from_bytes(n.read(7,2),'little'),flow=list(n.read(n.label('Flow_State'),16)) if hasattr(n,'label') else None)
def hop(n,game_taps,stage_taps,label):
 # from the title: menu, invincible, GAME, STAGE, then WARP TO END; wait for the clear
 n.run(300);code(n);n.run(40);tap(n,'RIGHT')
 tap(n,'DOWN');tap(n,'DOWN')
 for _ in range(game_taps):tap(n,'RIGHT')
 tap(n,'DOWN')
 for _ in range(stage_taps):tap(n,'RIGHT')
 for _ in range(11):tap(n,'DOWN')      # item 14 WARP TO END
 tap(n,'A');n.run(30);a=st(n);trace=[a]
 for f in range(3000):
  n.run(1);b=st(n)
  if b['stage']!=a['stage'] or b['chapter']!=a['chapter'] or b['mode']==4:trace.append(b);break
 n.png(OUT/f'flow_{label}.png');return a,trace[-1]
def scene_then_start(n,label):
 # placeholder scene screen: wait for the text rows, screenshot, START, then watch for the load
 n.run(120);n.png(OUT/f'flow_{label}_scene.png');s=st(n)
 tap(n,'START',hold=3,gap=3);a=st(n)
 for f in range(600):
  n.run(1);b=st(n)
  if b['mode']!=4:break
 n.run(60);return s,st(n)
checks={}
with NES(args.core,ROM.read_bytes(),True) as n:
 a,b=hop(n,1,1,'n2_map1_to_next')       # GAME NEMESIS2, STAGE 2 -> map 1
 checks['n2_map1_warp_lands_near_end']=a['chapter']==2 and a['stage']==1 and a['world']>=0x180
 checks['n2_map1_end_advances_to_map2']=b['chapter']==2 and b['stage']==2 and b['mode']==1
with NES(args.core,ROM.read_bytes(),True) as n:
 a,b=hop(n,3,0,'n3_map1_to_next')       # GAME NEMESIS3, STAGE 1 (sky stage)
 checks['n3_map1_warp_lands_near_end']=a['chapter']==4 and a['stage']==1
 checks['n3_map1_end_advances_to_map2']=b['chapter']==4 and b['stage']==2 and b['mode']==1
with NES(args.core,ROM.read_bytes(),True) as n:
 a,b=hop(n,3,2,'n3_map3_to_scene')      # GAME NEMESIS3, STAGE 3 -> AFTER3 cutscene placeholder
 checks['n3_map3_end_opens_scene']=b['mode']==4 and b['chapter']==4 and b['stage']==3
 sc,c=scene_then_start(n,'n3_map3')
 checks['n3_scene_start_loads_map4']=c['mode']==1 and c['chapter']==4 and c['stage']==4
with NES(args.core,ROM.read_bytes(),True) as n:
 a,b=hop(n,1,7,'n2_map7_to_turn')       # GAME NEMESIS2, STAGE 8 -> map 7 (halfway) -> turn scene
 checks['n2_map7_end_opens_turn_scene']=b['mode']==4 and b['chapter']==2 and b['stage']==7
 sc,c=scene_then_start(n,'n2_map7')
 checks['n2_turn_start_loads_map6_back']=c['mode']==1 and c['chapter']==2 and c['stage']==6
report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),checks=checks,scope='structural map-end progression through the campaign module; no gameplay')
(OUT/'chapter_flow.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(checks,indent=1))
failed=[k for k,v in checks.items() if not v];assert not failed,failed
print('PASS chapter flow',len(checks),'checks')
