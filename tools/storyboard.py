#!/usr/bin/env python3
"""Master storyboard and stage matrix for the continuous campaign (Frente D).

TITLE -> INTRO -> NEMESIS -> TRANSITION -> NEMESIS 2 -> TRANSITION -> SALAMANDER
-> TRANSITION -> NEMESIS 3 -> FINAL ENDING -> CREDITS.
Sources: reports/<game>_structure.json (from the disassemblies), the campaign
module contract (src/campaign.s, docs/CAMPAIGN_FLOW.md), manifests/content_coverage.json
and the native test reports. Writes manifests/storyboard.json and docs/STORYBOARD.md.
Stage states follow the brief: NOT_STARTED, ASSETS_READY, INTEGRATED, PARTIAL,
PLAYABLE, VERIFIED. VERIFIED is never assigned by this tool.
"""
from __future__ import annotations
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p,d=None):
    p=ROOT/p;return json.loads(p.read_text()) if p.exists() else d
cov=load('manifests/content_coverage.json');n1=load('reports/nemesis_structure.json',{})
n2=load('reports/nemesis2_structure.json',{});sal=load('reports/salamander_structure.json',{});n3=load('reports/nemesis3_structure.json',{})
n2_native=(ROOT/'build/native/n2_assets.json').exists()
n3_native=(ROOT/'build/native/n3_assets.json').exists()
has_assets={'nemesis':True,'nemesis2':(ROOT/'assets/msx/nemesis2/stage_manifest.json').exists(),'salamander':(ROOT/'reports/salamander_extraction.json').exists(),'nemesis3':(ROOT/'reports/nemesis3_extraction.json').exists()}
seq=[];n=[0]
def add(sid,kind,game,title,**k):
    n[0]+=1;row=dict(order=n[0],id=sid,kind=kind,game=game,title=title,state=k.pop('state','NOT_STARTED'),resources=k.pop('resources',[]),music=k.pop('music',None),
                     entry=k.pop('entry',None),exit_condition=k.pop('exit',None),next=k.pop('next',None),dependencies=k.pop('dependencies',[]),notes=k.pop('notes',''))
    row.update(k);seq.append(row);return row
# --- frame
add('TITLE','screen','nemesis_legends','Nemesis Legends title and menu',state='PLAYABLE',resources=['nl.custom_title_artwork_and_menu'],entry='power on',exit='START GAME',notes='native; 56 title checks')
add('INTRO','cutscene','nemesis_legends','Opening narration (new, bridges the four games)',state='NOT_STARTED',notes='text to be authored from the four originals; renderer not written')
# --- Nemesis
N1_STATE={1:'PARTIAL',2:'PARTIAL',3:'PARTIAL',4:'PARTIAL',9:'PARTIAL',10:'PARTIAL',11:'PARTIAL'}
for st in n1.get('campaign_order',[1,2,9,3,10,4,11,5,6,7,12,8]):
    s=next((x for x in n1.get('stages',[]) if x['stage']==st),{})
    music=[r['track_command'] for r in s.get('music',{}).get('rows',[])]
    add(f'N1.S{st:02d}','stage','nemesis',f"Nemesis stage {st}: {s.get('name','')}",state=N1_STATE.get(st,'ASSETS_READY' if has_assets['nemesis'] else 'NOT_STARTED'),
        resources=[f'n1.stage{st:02d}.terrain',f'n1.stage{st:02d}.tiles',f'n1.stage{st:02d}.sprites',f'n1.stage{st:02d}.script'],music=music,
        entry='distance $20 or checkpoint %s'%(hex(s['checkpoint_distance']) if s.get('checkpoint_distance') else 'n/a'),exit=s.get('end_sequence',''),
        notes='assisted route tested, visuals provisional' if st in N1_STATE else 'descriptor in ROM; no stage logic, bosses or waves beyond the shared engine')
add('N1.ENDING','cutscene','nemesis','Nemesis ending (after stage 8 boss kind 4)',resources=['n1.ending'],notes='location/format UNRESOLVED in the structure inventory')
add('T1','transition','nemesis_legends','Transition Nemesis -> Nemesis 2 (new)',notes='keeps the Nemesis ending, adds the bridge; no original rule')
# --- Nemesis 2
def generic(game,label,struct,prefix,fallback_ids):
    stages=struct.get('stages') or struct.get('maps') or []
    if stages:
        for s in stages:
            sid=s.get('id',s.get('map_id',s.get('stage')));add(f'{prefix}.{str(sid).upper()}','stage',game,f"{label} {s.get('role',s.get('name',sid))}",state=('INTEGRATED' if ((game=='nemesis2' and n2_native) or (game=='nemesis3' and n3_native)) else 'ASSETS_READY') if has_assets[game] else 'NOT_STARTED',
                resources=[f'{game}.map{int(s.get("map_id",s.get("id",0)) or 0):02d}.terrain'] if str(s.get('map_id',s.get('id',''))).isdigit() else [],music=[e.get('tune',e.get('track')) for e in (s.get('music') or {}).get('entries',(s.get('music') or {}).get('records',[]))] if isinstance(s.get('music'),dict) else s.get('music'),exit=s.get('end_sequence',s.get('end_routine')),notes=s.get('unresolved','') if isinstance(s.get('unresolved',''),str) else '; '.join(map(str,s.get('unresolved',[]))))
    else:
        for sid in fallback_ids:add(f'{prefix}.{sid}','stage',game,f'{label} {sid}',state='ASSETS_READY' if has_assets[game] else 'NOT_STARTED',notes='structure inventory pending')
    for it in struct.get('interludes',[]):
        add(f'{prefix}.INTERLUDE.AFTER{it.get("after_stage")}','cutscene',game,f'{label} interlude after stage {it.get("after_stage")}: {it.get("kind")}',music=[it.get('music')] if isinstance(it.get('music'),int) else None,notes=str(it.get('code','')))
    cuts=struct.get('cutscenes',[])
    items=list(cuts.items()) if isinstance(cuts,dict) else [((c.get('name',str(c)) if isinstance(c,dict) else str(c)),c) for c in cuts]
    for name,c in items:
        info=c if isinstance(c,dict) else {}
        add(f'{prefix}.CUT.'+''.join(ch for ch in str(name).upper() if ch.isalnum())[:16],'cutscene',game,f'{label} cutscene: {name}',notes=str(info.get('notes',info.get('code',info.get('drawing',''))))[:160])
generic('nemesis2','Nemesis 2',n2,'N2',['S1','S2','S3','S4','S5','S6','S7','HALFWAY_ENDING','R6','R5','R4','R3','R2','R1','R0','INTERIOR8','SECRET9','SECRET10','SECRET11','ENDING'])
add('T2','transition','nemesis_legends','Transition Nemesis 2 -> Salamander (new)')
generic('salamander','Salamander',sal,'SAL',['S1','S2','S3','S4','S5','S7_OPERATION_X','S6','ENDING_GOOD','ENDING_BAD'])
add('T3','transition','nemesis_legends','Transition Salamander -> Nemesis 3 (new)')
generic('nemesis3','Nemesis 3',n3,'N3',['S1','S2','S3','COMPUTER_A','S4','COMPUTER_B','S5','S6','S7','S8','S9','MAP_CHECK','S10','S11','ENDING_NORMAL','ENDING_SECRET'])
add('FINAL','cutscene','nemesis_legends','Final ending of the anthology (new, after Nemesis 3)')
add('CREDITS','screen','nemesis_legends','Credits (new)')
for i,row in enumerate(seq):row['next']=seq[i+1]['id'] if i+1<len(seq) else None
counts={}
for r in seq:counts[r['state']]=counts.get(r['state'],0)+1
out=dict(schema=1,order='TITLE, INTRO, NEMESIS, T1, NEMESIS 2, T2, SALAMANDER, T3, NEMESIS 3, FINAL, CREDITS',sequence=seq,state_counts=counts,
         policy=['Original endings are kept and played before each transition.','Nemesis 2 halfway ending is not completion; the return trip follows.','Salamander bad ending offers a chapter retry (anthology policy).','Both Nemesis 3 endings are valid finals; the anthology FINAL follows either.'])
(ROOT/'manifests/storyboard.json').write_text(json.dumps(out,indent=1)+'\n')
lines=['# Master storyboard (generated by tools/storyboard.py; do not edit)','',out['order'],'','| # | id | kind | game | title | state | music |','|---|---|---|---|---|---|---|']
for r in seq:lines.append(f"| {r['order']} | {r['id']} | {r['kind']} | {r['game']} | {r['title']} | {r['state']} | {','.join(hex(m) if isinstance(m,int) else str(m) for m in (r['music'] or [])) if r['music'] else ''} |")
lines+=['','State counts: '+', '.join(f'{k} {v}' for k,v in sorted(counts.items())),'']+['- '+p for p in out['policy']]
(ROOT/'docs/STORYBOARD.md').write_text('\n'.join(lines)+'\n');print(counts,len(seq),'sequences')
