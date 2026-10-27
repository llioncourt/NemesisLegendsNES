#!/usr/bin/env python3
"""Structural inventory of MSX Nemesis read from the hash-verified ROM.
Addresses come from the pinned antxiko/Nemesis-disassembly (p00..p03) and the
native port's own reconciliation. Writes reports/nemesis_structure.json (no raw
ROM dumps beyond small tables already documented in the disassembly).
"""
from __future__ import annotations
import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from extract_nemesis_msx import Extractor
sel=json.loads((ROOT/'manifests/selected_sources.json').read_text())['nemesis_msx']
ex=Extractor((ROOT/sel['path']).read_bytes())
ORDER=[1,2,9,3,10,4,11,5,6,7,12,8]
NAMES={1:'Volcano',2:'Stonehenge',3:'Moai (no terrain)',4:'Inverted volcano',5:'Tentacles',6:'Cells (no terrain)',7:'Mechanical base approach',8:'Fortress / final',9:'Bonus 9 (from 2)',10:'Bonus 10 (from 3)',11:'Bonus 11 (from 4)',12:'Bonus 12 (from 7)'}
END_ROUTINES={1:'final_de_la_fase_1 6CEF: p02:8E77 five pieces at $165; at limit $19F tanda mode 1 (450 rocks); E105=$1C0; Big Core kind 0; acaba_la_fase',
 2:'final_de_la_fase_2: target $190 -> stage 9 (E1C0); rock walls $144..$188 and 900-frame rain (p03:AB86); Big Core kind 0 at $1DF',
 3:'final_de_la_fase_3 6DA7: Big Core kind 0 at $60 (first step), scroll to $1AF, Big Core again; target $12A -> stage 10; second loop kind 6 instead of 1 (el_otro_jefe 6DE1)',
 4:'final_de_la_fase_4 6E15: tanda mode 2 at $128; p02:8E77 five pieces at $171; kind 5 at limit $19F; E105=$1C0; Big Core kind 0; targets 3/4 at $C0/$104 -> stage 11',
 5:'final_de_la_fase_5 6EA8: bank-3 encounter p03:B946 at the limit; after death p03:BB95 (E988/E990); E105=$1FF; Big Core kind 0',
 6:'final_de_la_fase_6 6EF0: past $A0 boss kind 2 (p01:7F74); limit stays where it dies',
 7:'final_de_la_fase_7 6F19: target $177 -> stage 12; else boss kind 3 (p01:8719)',
 8:'final_de_la_fase_8 6F43: at $16E boss kind 4 (p01:87F3); on kill the ending explosion',
 9:'bonus: six instructions, back to stage 3 (table 418F)',10:'bonus: back to stage 4',11:'bonus: back to stage 5',12:'bonus: back to stage 8'}
BOSS_KINDS={0:('Big Core nucleus','p01:7C8D','HP 22, 720-frame window, face opens/closes'),1:('kind 1','p01:839F','UNRESOLVED behaviour'),2:('stage 5/6 boss','p01:7F74','UNRESOLVED behaviour'),
 3:('stage 7 boss','p01:8719','UNRESOLVED behaviour'),4:('stage 8 final boss','p01:87F3','UNRESOLVED behaviour'),5:('piece spawner (stage 4)','p02:8CE4','8 type-6 pieces HP $28, 600-frame window'),6:('second-loop replacement of kind 1','p01:83A5','UNRESOLVED behaviour')}
TARGETS=[dict(stage=1,type=2,distance=0xfc,row=0x88,effect='counts toward the three-touch bonus 11 (E06C/E06D)'),dict(stage=2,type='single',distance=0x190,row=0x88,effect='bonus stage 9'),
 dict(stage=3,type='single',distance=0x12a,row=0x30,effect='bonus stage 10'),dict(stage=4,type=3,distance=0xc0,row=0x10,effect='three-touch counter'),dict(stage=4,type=4,distance=0x104,row=0x10,effect='three-touch counter -> bonus 11'),
 dict(stage=7,type=1,distance=0x177,row=0x38,effect='bonus stage 12')]
MOVERS=[0x9119,0xa8b2,0xa836,0xa863,0xa9fb,0xa95a,0x5ee7,0xacbd,0xad33,0xad92,0xade5,0xae1b,0xafbd,0x5f4f,0x71ad,0x71b0,0x5e3b,0x5e3b,0x5e3b,0x5ec8,0x5e3e,0x5e3b,0xa7d9,0xa7d9,0x5e3b,0xa7df,0xb915,0x5f4f,0xb9ff,0xbce3,0xbd7d]
def music(stage):
    a=ex.word(1,0x7056+2*stage);rows=[]
    for _ in range(8):
        d=ex.word(1,a);m=ex.byte(1,a+2);rows.append(dict(below_distance=d,track_command=m));a+=3
        if d==0xffff:break
    return dict(table_address=ex.word(1,0x7056+2*stage),rows=rows)
stages=[]
for st in range(1,13):
    a=0x4499+st*6;start,end,limit=(ex.word(0,a+i) for i in (0,2,4))
    script=ex.word(11,0x97de+2*st);checkpoint=ex.word(0,0x4212+st*2) if st<12 else None
    cp=ex.word(2,0x9262+2*st);cannons=0;at=cp
    while ex.word(2,at)!=0xffff and cannons<256:cannons+=1;at+=3
    waves=ex.word(3,0xa3a6+st*2) if st<=8 else None
    stages.append(dict(stage=st,name=NAMES[st],campaign_position=ORDER.index(st)+1,bonus=st>=9,terrain_script_start=start,terrain_script_end=end,initial_scroll_limit=limit,
        terrain_script_address=script,checkpoint_distance=checkpoint,cannon_record_count=cannons,cannon_table_address=cp,
        wave_group_bits_address=waves,wave_group_bits=[ex.byte(3,waves+j) for j in range(16)] if waves else None,opening_wave_types=ex.byte(3,0xa5af+st) if st<=8 else None,
        end_routine_address=ex.word(1,0x6cd7+2*(st-1)),end_sequence=END_ROUTINES[st],music=music(st),
        native_state={1:'playable (assisted)',2:'playable (assisted)',3:'playable (assisted)',4:'playable (assisted) since CP0012',9:'bonus route tested',10:'bonus route tested',11:'bonus route tested'}.get(st,'descriptor only, no stage logic')))
fichas=[dict(type=t,draw_mode=ex.byte(1,0x6ba3+4*t),pattern=ex.byte(1,0x6ba3+4*t+1),colour=ex.byte(1,0x6ba3+4*t+2),hp=ex.byte(1,0x6ba3+4*t+3),mover=('%04X'%MOVERS[t-1]) if 1<=t<=31 else None) for t in range(32)]
out=dict(source_sha256=sel['sha256'],campaign_order=ORDER,bonus_return_table_418F=[ex.byte(0,0x418f+i) for i in range(4)],stage_record_table='p00:4499 (start,end,limit) x6 bytes',checkpoint_table='p00:4212',
         end_routine_table='p01:6CD7',music_table='p01:7056 (per stage: rows of distance limit + track command, FFFF last)',stages=stages,boss_kinds={k:dict(name=n,address=a,notes=x) for k,(n,a,x) in BOSS_KINDS.items()},
         targets=TARGETS,object_types=fichas,player=dict(speed_formula='p02:9B0D base $0080 x (3+min(speed,7))',power_meter='E130..E136, capsule table 7563',shield='two states'),
         cheats=dict(pause_keyboard='p01:51BF words HYPER SHIELD LASER MISSILE DOUBLE OPTION DOWN BAKA AHO; per-stage names 5163'),
         unresolved=['boss kinds 1,2,3,4,6 behaviour not yet transcribed','ending sequence location/format','stage 5 bank-3 encounters p03:B946/BB95 content','second-loop difficulty differences beyond E06A boss swap'])
(ROOT/'reports/nemesis_structure.json').write_text(json.dumps(out,indent=1)+'\n')
print(json.dumps([(s['stage'],s['initial_scroll_limit'],s['checkpoint_distance'],s['cannon_record_count'],[r['track_command'] for r in s['music']['rows']]) for s in stages]))
