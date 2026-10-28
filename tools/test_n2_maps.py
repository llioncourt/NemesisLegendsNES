#!/usr/bin/env python3
"""Chapter 2 structural integration: every Nemesis 2 map descriptor loads through
the cheat menu (GAME NEMESIS2 + STAGE n + START), scrolls its converted terrain
and keeps the NMI schedule. Terrain and sprites only: no Nemesis 2 gameplay is
claimed. Captures one screenshot per map.
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
results=[]
with NES(args.core,ROM.read_bytes(),True) as n:
 n.run(300);code(n);n.run(40)
 tap(n,'RIGHT')                                      # INVINCIBLE on (QA only: terrain contact must not end the scroll test)
 tap(n,'DOWN');tap(n,'DOWN');tap(n,'RIGHT')          # GAME -> NEMESIS2
 tap(n,'DOWN')                                       # STAGE
 for m in range(12):
  if m:tap(n,'RIGHT')
  n.run(20);tap(n,'START');n.run(30)
  stage=n.read(0x1d,1)[0];chapter=n.read(0x7f,1)[0];mode=n.read(2,1)[0];bank=n.read(0x1e,1)[0]
  w0=int.from_bytes(n.read(7,2),'little');miss0=n.read(0x1c,1)[0]
  n.buttons[0]=set();n.run(600)
  w1=int.from_bytes(n.read(7,2),'little');miss1=n.read(0x1c,1)[0]
  n.png(OUT/f'n2_map_{m:02d}.png')
  results.append(dict(map=m,mode=mode,chapter=chapter,stage_id=stage,stage_bank=bank,world_start=w0,world_after_600=w1,missed_nmi=miss1-miss0,
                      ok=mode==1 and chapter==2 and stage==m and bank==14+m and w1>=w0+30 and miss1==miss0))
  print(results[-1],flush=True)
  # back to the menu for the next map
  tap(n,'START');n.run(5);code(n);n.run(40)
  for _ in range(3):tap(n,'DOWN')
report=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),scope='chapter-2 map descriptors load and scroll; terrain/sprite conversion only',maps=results)
(OUT/'n2_maps_structural.json').write_text(json.dumps(report,indent=1)+'\n')
failed=[r['map'] for r in results if not r['ok']];assert not failed,failed
print('PASS chapter-2 map load',len(results),'maps')
