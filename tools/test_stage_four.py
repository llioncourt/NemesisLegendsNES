#!/usr/bin/env python3
"""Controller-driven FCEUmm route through the native Nemesis stage-4 end sequence.
QA invulnerability only: no stage, world, phase, boss or actor state is injected.
Checks the source order p01:$6E15: eruption at $0128, five-piece tower at $0171,
boss 5 once the scroll stops at $019F, scroll to $01C0, Big Core, stage 5.
Does not claim visual parity or an unassisted clear.
"""
import argparse,hashlib,json,pathlib
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
A=labels['S4_State']
def state(n):
 s=n.read(A,15)
 return dict(step=s[0],tanda=s[1],crater=s[2],tower=s[5],b5=s[7],rocks=s[12],spawned=s[13],killed=s[14])
def pieces_alive(n):
 p=n.read(A+15,32);return sum(1 for i in range(8) if p[i*4+3])
events=[];shots={}
with NES(args.core,ROM.read_bytes(),True) as n:
 n.run(180);n.buttons[0]={3};n.run(1);n.buttons[0]=set();n.run(40)
 for _ in range(2):n.buttons[0]={2};n.run(1);n.buttons[0]=set();n.run(2)
 n.write(0x53,b'\x01')  # explicit QA invulnerability
 stage4=None;stage5=None;missed_at_entry=None;last=None;max_alive=0;phases=[];tower_actors=0;rock_actors=0;ten_seen=0
 for f in range(30000):
  st=n.read(0x1d,1)[0];phase=n.read(0x3b,1)[0];w=int.from_bytes(n.read(7,2),'little');missed=n.read(0x1c,1)[0]
  if st==4:
   if stage4 is None:stage4=f;missed_at_entry=missed
   s=state(n);alive=pieces_alive(n);max_alive=max(max_alive,alive)
   key=(s['step'],s['tanda'],s['tower'],s['b5'],phase)
   if key!=last:
    events.append(dict(frame=f,world=w,phase=phase,alive=alive,**s));last=key
    if phase not in phases:phases.append(phase)
   mirror=n.read(0x0780,68)
   types=[mirror[i*4] for i in range(17)]
   if s['tanda']:rock_actors=max(rock_actors,types[:12].count(0x0f))
   tower_actors=max(tower_actors,types[12:].count(0x20))
   ten_seen=max(ten_seen,types[:12].count(0x0a))
   for tag,cond in (('eruption',s['tanda']==2 and s['rocks']>=20),('tower',s['tower']==1 and tower_actors>=5 and w>=0x180),
                    ('boss5',alive>=3),('core',phase==6)):
    if cond and tag not in shots:n.png(OUT/f'stage4_{tag}.png');shots[tag]=f
   y=n.read(0x21,1)[0]
   pad={0} if (f//8)%2 else set()
   pad|={4} if y>0x48 else {5} if y<0x40 else set()
   n.buttons[0]=pad
  elif st==5:
   stage5=f;n.png(OUT/'stage5_entry.png');break
  else:n.buttons[0]={0} if (f//8)%2 else set()
  n.run(1)
 missed_delta=n.read(0x1c,1)[0]-(missed_at_entry or 0)
by_step={e['step']:e for e in events}
checks={
 'reached_stage_four':stage4 is not None,
 'eruption_starts_at_source_0128':any(e['tanda']==2 and e['world']==0x128 for e in events),
 'eruption_emitted_type_0F_rocks':rock_actors>0,
 'tower_starts_at_source_0171':any(e['tower']==1 and e['world']==0x171 for e in events),
 'tower_has_five_source_pieces':tower_actors==5,
 'boss5_starts_when_scroll_stops_at_019F':any(e['phase']==15 and e['world']==0x19f for e in events),
 'boss5_spawned_eight_pieces':max(e['spawned'] for e in events)==8,
 'boss5_pieces_overlapped_on_screen':max_alive>=3,
 'scroll_resumed_after_boss5':any(e['step']==3 and e['phase']==0 for e in events),
 'big_core_wait_at_source_01C0':any(e['phase']==4 and e['world']==0x1c0 for e in events),
 'big_core_fought':6 in phases and 8 in phases,
 'source_type_0A_waves_seen':ten_seen>0,
 'reached_stage_five':stage5 is not None,
 'no_missed_nmi_inside_stage_four':missed_delta==0,
}
result=dict(rom_sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),assisted='QA invulnerability only',
            source='p01:6E15 final_de_la_fase_4; p01:70D6 tanda; p02:8E77 five pieces; p02:8CE4 boss 5',
            stage4_frame=stage4,stage5_frame=stage5,missed_nmi_delta=missed_delta,max_pieces_alive=max_alive,
            screenshots={k:v for k,v in shots.items()},events=events,checks=checks)
(OUT/'stage_four_integration.json').write_text(json.dumps(result,indent=1)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='events'},indent=1))
failed=[k for k,v in checks.items() if not v]
assert not failed,failed
print('PASS stage four route',len(checks),'checks')
