#!/usr/bin/env python3
"""Silicon Forge cheat menu: controller-driven FCEUmm checks. Konami Code on the
title and while paused; stage select, flags, resume restore, warp, infinite
lives and the debug row all go through the real loaders.
"""
import argparse,hashlib,json,pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
ROM=ROOT/'build/native/Nemesis_Legends_CP0013.nes'
CORE=ROOT/'toolchain/linux-x64/bin/fceumm_libretro.so'
OUT=ROOT/'reports/cp0013';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--core',default=str(CORE));args=parser.parse_args()
labels={}
for l in (ROOT/'build/native/native.lbl').read_text().splitlines():
 p=l.split()
 if len(p)==3 and p[0]=='al':labels[p[2].lstrip('.')]=int(p[1],16)
CS=labels['Cheat_State']
B=NES.BUTTONS
KONAMI=['UP','UP','DOWN','DOWN','LEFT','RIGHT','LEFT','RIGHT','B','A']
def tap(n,btn,hold=2,gap=3):
 n.buttons[0]={B[btn]};n.run(hold);n.buttons[0]=set();n.run(gap)
def code(n):
 for k in KONAMI:tap(n,k)
def st(n):return dict(mode=n.read(2,1)[0],stage=n.read(0x1d,1)[0],world=int.from_bytes(n.read(7,2),'little'),qa=n.read(0x53,1)[0],cheat=n.read(0x7d,1)[0],lives=n.read(0x24,1)[0],
                      cursor=n.read(CS+2,1)[0],opened=n.read(CS+5+17,1)[0],phase=n.read(0x3b,1)[0],hud2=bytes(n.read(0x3a0,32)).decode('latin1'))
checks={};shots={}
with NES(args.core,ROM.read_bytes(),True) as n:
 n.run(300)
 code(n);n.run(60);s=st(n)
 checks['title_konami_opens_menu']=s['mode']==5 and s['opened']==1
 n.png(OUT/'cheat_menu_title.png')
 # INVINCIBLE on, LIVES infinite, STAGE 4, then START
 tap(n,'RIGHT');tap(n,'DOWN');tap(n,'RIGHT');tap(n,'DOWN');tap(n,'DOWN');tap(n,'RIGHT');tap(n,'RIGHT');tap(n,'RIGHT');n.run(40)
 n.png(OUT/'cheat_menu_edited.png');s=st(n);checks['menu_cursor_on_stage']=s['cursor']==3
 tap(n,'START');n.run(30);s=st(n)
 checks['start_from_menu_loads_selected_stage']=s['mode']==1 and s['stage']==4
 checks['invincible_and_infinite_lives_applied']=(s['qa']&1)==1 and (s['cheat']&1)==1
 n.run(200);w0=st(n)['world'];checks['stage_four_scrolls']=w0>0x20
 # pause, menu, plain resume keeps the world
 tap(n,'START');n.run(5);s=st(n);checks['pause_before_code']=s['mode']==2
 code(n);n.run(40);s=st(n);checks['pause_konami_opens_menu']=s['mode']==5 and s['opened']==2
 n.png(OUT/'cheat_menu_pause.png')
 # DEBUG HUD on: cursor 0 -> item 13 (DOWN x13), RIGHT
 for _ in range(13):tap(n,'DOWN')
 tap(n,'RIGHT');n.run(30);s=st(n);checks['cursor_reached_debug_item']=s['cursor']==13
 w_before=s['world']
 tap(n,'START');n.run(5);s=st(n)
 checks['resume_returns_to_pause_with_world_kept']=s['mode']==2 and s['stage']==4 and abs(s['world']-w_before)<=1
 tap(n,'START');n.run(120);s=st(n)
 checks['game_continues_after_resume']=s['mode']==1 and s['world']>w_before
 checks['debug_row_live']=s['hud2'].startswith('W:') and (s['cheat']&2)==2
 n.png(OUT/'cheat_debug_hud.png')
 # warp to end zone from the pause menu: cursor 0 -> item 14
 tap(n,'START');n.run(5);code(n);n.run(30)
 for _ in range(14):tap(n,'DOWN')
 tap(n,'A');n.run(30);s=st(n)
 checks['warp_to_end_zone']=s['mode']==1 and s['stage']==4 and 0x160<=s['world']<=0x180
 n.png(OUT/'cheat_warp.png')
 # infinite lives: invincible OFF (item 0), stay in stage 4 end zone and get killed
 tap(n,'START');n.run(5);code(n);n.run(30);tap(n,'LEFT');tap(n,'START');n.run(5);tap(n,'START');n.run(5)
 s=st(n);checks['invincible_cleared_from_menu']=(s['qa']&1)==0
 lives0=s['lives'];died=False
 for f in range(4000):
  if n.read(2,1)[0]==3:died=True;break
  n.run(1)
 n.run(200);s=st(n)
 checks['death_observed_without_invincibility']=died
 checks['infinite_lives_keep_count']=died and s['lives']==lives0
report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),checks=checks,qa='menu-driven only; no RAM writes')
(OUT/'cheat_menu_tests.json').write_text(json.dumps(report,indent=1)+'\n')
print(json.dumps(checks,indent=1))
failed=[k for k,v in checks.items() if not v];assert not failed,failed
print('PASS cheat menu',len(checks),'checks')
