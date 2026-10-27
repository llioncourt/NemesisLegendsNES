#!/usr/bin/env python3
"""Asset bible: one canonical record per GAME OBJECT (not per tile), merging
code-proven MSX evidence and OAM-proven NES-reference evidence, and stating the
official Nemesis Legends version of each object so the four chapters stay
visually consistent.

Inputs (private evidence folders, never committed; produced by the evidence
agents and regenerable with their tools):
  --msx  <folder>/objects.json  (MSX Nemesis: patterns written by code)
  --nes  <folder>/objects.json  (Gradius NES US: OAM captures + screenshots)
Outputs (public, no ROM bytes): manifests/asset_bible.json, docs/ASSET_BIBLE.md.
The cross-mapping below is the editorial part of the bible; everything else is
copied from the evidence files with their references.
"""
from __future__ import annotations
import argparse, json, pathlib, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]

# canonical id -> (display name, role, games, msx object name, nes object name or None, legends policy)
# legends policy: REUSE_NES (NES tiles as-is), ADAPT_NES (NES tiles, edited), CONVERT_MSX, REDRAW, NEW
def E(cid,name,role,games,msx,nes,policy,cand=(),note=None):
    return dict(id=cid,name=name,role=role,games=games,msx=msx,nes=nes,policy=policy,cand=list(cand),note=note)
ALL=['nemesis','nemesis2','salamander','nemesis3']; N1=['nemesis']
# nes: one NES evidence object name, a list of names merged into the same game object, or None.
# policy REUSE_NES/ADAPT_NES only when an NES reference is PROVEN; otherwise CONVERT_MSX (or REDRAW/NEW).
MAP=[
 E('player.vic_viper','Vic Viper','player',ALL,'Vic Viper',['vic_viper','vic_viper_exhaust'],'REUSE_NES',note='NES draws a separate exhaust flame (tile 223, palette 3); Legends adopts it as part of the ship.'),
 E('player.shield','Shield / force field','player',ALL,'Vic Viper shield','shield','REUSE_NES'),
 E('player.death','Vic Viper death explosion','effect',ALL,'Vic Viper death explosion','vic_viper_debris','REUSE_NES'),
 E('player.option','Option (Multiple)','player',ALL,'Option (Multiple)','option','REUSE_NES'),
 E('weapon.shot','Normal shot','player_weapon',ALL,'Normal shot','normal_shot','REUSE_NES'),
 E('weapon.double','Double shot','player_weapon',ALL,'Double shot','double_shot','REUSE_NES'),
 E('weapon.laser','Laser','player_weapon',ALL,'Laser','laser','REUSE_NES'),
 E('weapon.missile','Missile','player_weapon',ALL,'Missile',['missile','missile_ground'],'REUSE_NES'),
 E('hud.power_meter','Power-up meter','hud',ALL,'Power-up meter HUD','hud_power_meter','ADAPT_NES',note='NES reference is background (nametable) tiles, not sprites; Legends keeps its own 32-column text HUD layout and adopts the NES meter drawing.'),
 E('powerup.capsule','Power capsule (red)','powerup',ALL,'Power capsule (red)','capsule_red','REUSE_NES'),
 E('powerup.capsule_blue','Blue capsule (destroy-all)','powerup',ALL,'Blue capsule (destroy-all)','capsule_blue','REUSE_NES',note='NES identification by palette; pick-up effect capture requested.'),
 E('powerup.oneup','1UP item','powerup',N1,'1UP item (bonus stages)',None,'CONVERT_MSX'),
 E('powerup.bonus_capsule','Bonus capsule (score)','powerup',N1,'Bonus capsule (score)',None,'CONVERT_MSX'),
 E('powerup.bonus_block','Bonus block','powerup',N1,'Bonus block (becomes capsule when touched)',None,'CONVERT_MSX'),
 E('effect.score_popup','Score / 1UP popup','effect',N1,'Score / 1UP popup','one_up_popup','CONVERT_MSX',note='Partial reference: NES has only the 1UP popup; the seven capsule-chain score popups (E4..FC) have no NES frames. Legends converts the MSX set and may reuse the NES 1UP glyph.'),
 E('effect.explosion','Enemy explosion','effect',ALL,'Enemy explosion (type $15)',['explosion_medium','explosion_small'],'REUSE_NES',note='MSX uses one 16x16 explosion for every enemy. Legends adopts explosion_medium for all enemies and explosion_small for fans, as Gradius NES does.'),
 E('effect.death_flash','Turret death flash','effect',N1,'Type-0D death flash (type $14)',None,'CONVERT_MSX'),
 E('effect.bg_explosion','Background explosion','effect',N1,'Background explosion (E800 type $20)','explosion_large','REUSE_NES',note='QA: large burst is what Gradius NES draws for ground structures and the Big Core.'),
 E('enemy.shot','Enemy shot','enemy',ALL,'Enemy shot (E500)','red_pellet','REUSE_NES',note='QA verified by trajectory: aimed at the ship.'),
 E('boss.bigcore.shots','Big Core shots','boss',N1,'Big Core shots (chars)','big_core_laser','REUSE_NES'),
 E('effect.ending_debris','Ending debris','effect',N1,'Ending debris (metralla)',None,'CONVERT_MSX'),
 E('enemy.n1.cannon','Ground cannon','enemy',N1,'Ground cannon','hanger','ADAPT_NES',note='QA: static floor/ceiling turret with two barrel frames; MSX has six angle drawings, NES two: adaptation needed.'),
 E('enemy.n1.fan','Fan','enemy',N1,'Fan (turn-back fighter)','fan','REUSE_NES'),
 E('enemy.n1.falling_pair','Falling pair','enemy',N1,'Falling pair (type 3)',None,'CONVERT_MSX',note='No Gradius NES counterpart found.'),
 E('enemy.n1.row_fighter','Row fighter','enemy',N1,'Row fighter (type 4)','small_cyan_pair','REUSE_NES',note='QA: spawns every 4 frames at alternating heights and converges on the ship row; v-flip = tilt.'),
 E('enemy.n1.ducker','Ducker','enemy',N1,'Ducker (type 5)','ceiling_flyer','REUSE_NES',note='QA: enters from the left on floor or ceiling and walks right.'),
 E('enemy.n1.jumper','Jumper','enemy',N1,'Jumper (type 6)',None,'CONVERT_MSX'),
 E('enemy.n1.hatch_bug','Hatch bug','enemy',N1,'Hatch bug (type 7)','hatch_bug','REUSE_NES',note='NES tiles 241-249 (QA); catalogue requested.'),
 E('enemy.n1.rock','Rock','enemy',N1,'Rock (type 8)',None,'CONVERT_MSX',note='Gradius NES stage-2 rocks not yet labelled.'),
 E('enemy.n1.flock','Flock','enemy',N1,'Flock (type 9)','flock_fighter','REUSE_NES',note='NES stage 3 (Moai stage) line formation of four with four animation frames; MSX type 9 is the stage-3 flock.'),
 E('enemy.n1.curver','Curving fighter','enemy',N1,'Curving tanda fighter (type 0A)','cross_spinner','REUSE_NES',note='QA round 2 proved by behaviour: streams enter from the right, curve alternately and turn back at x~44-52 (MSX column $30); rotating twin-blade drawing.'),
 E('enemy.n1.ion_ring','Boss-piece rotating disc (type 0B)','enemy',N1,'Moai ion ring (type 0B)',None,'CONVERT_MSX',note='QA round 2: MSX type 0B is the large rotating disc fired by the stage-3 boss pieces, not the thin ring the heads fire. No NES counterpart proven.'),
 E('enemy.n1.figure_eight','Figure-eight flyer','enemy',N1,'Figure-eight flyer (type 0C)',None,'CONVERT_MSX'),
 E('enemy.n1.turret7','Stage-7 turret','enemy',N1,'Stage-7 stationary turret (type 0D)',None,'CONVERT_MSX'),
 E('enemy.n1.aimed_shot','Moai ion ring (aimed shot, type 0E)','enemy',N1,'Aimed shot (type 0E)','ion_ring','REUSE_NES',note='QA round 2: the MSX heads fire type 0E whose stage-3 pattern FC is the thin ring; NES ion_ring (tile 243 + flips, palette 1) is the same object.'),
 E('enemy.n1.volcano_rock','Volcano rock','enemy',N1,'Volcano rock (type 0F)','ground_bits','REUSE_NES',note='QA: ballistic arc from ground level.'),
 E('enemy.n1.boss7_spit','Boss-7 spit shot','enemy',N1,'Boss-7 spit shot (type 10)',None,'CONVERT_MSX'),
 E('boss.n1.final_object','Final-boss scripted object','boss',N1,'Final-boss scripted object (type 11)',None,'CONVERT_MSX'),
 E('enemy.n1.bouncer5','Stage-5 bouncer','enemy',N1,'Stage-5 bouncer (type 1B)',None,'CONVERT_MSX'),
 E('enemy.n1.seed5','Stage-5 pod seed','enemy',N1,'Stage-5 spawned enemy (type 1C)',None,'CONVERT_MSX'),
 E('enemy.n1.spiral5','Stage-5 spiral flyer','enemy',N1,'Stage-5 spiral flyer (type 1D)',None,'CONVERT_MSX'),
 E('enemy.n1.big5','Stage-5 three-slot enemy','enemy',N1,'Three-slot big enemy (type 1E)',None,'CONVERT_MSX'),
 E('enemy.n1.fragment5','Stage-5 fragment','enemy',N1,'Fragment (type 1F)',None,'CONVERT_MSX'),
 E('enemy.n1.hatch','Hatch','enemy',N1,'Hatch (E700 type 1/2)','tall_turret','REUSE_NES',note='QA: emits a rising object every 16 frames and dies into the large explosion.'),
 E('enemy.n1.moai','Moai head','enemy',N1,'Moai head, E700 type 3/4 (stage 3)','moai_head','ADAPT_NES',note='Both versions draw the heads as background characters/tiles; MSX piece placement partly inferred. NES heads are nametable tiles (background entry).'),
 E('enemy.n1.turret5','Stage-5 sliding turret','enemy',N1,'Stage-5 sliding turret (E880)',None,'CONVERT_MSX'),
 E('scenery.n1.volcano','Volcano vent','scenery',N1,'Volcano vent (EB00 five pieces, stages 1 and 4)',None,'CONVERT_MSX'),
 E('boss.n1.bigcore','Big Core','boss',N1,'Big Core',['big_core','big_core_core'],'REUSE_NES',note='MSX eye damage frames correspond to the NES core (palette 1, palette 3 when hit).'),
 E('boss.n1.kind1','Stage-3 boss (kind 1)','boss',N1,'Boss kind 1 - stage-3 four-height pieces',None,'CONVERT_MSX',cand=['orbiter_core','orbiter_satellite'],note='Name provisional. NES stage-3 end encounter (orbiter core + satellites) is a candidate; functional match unproven.'),
 E('boss.n1.kind5','Stage-4 boss (kind 5)','boss',N1,'Boss kind 5 - stage-4 piece spawner',None,'CONVERT_MSX'),
 E('boss.n1.kind3','Stage-7 boss (kind 3)','boss',N1,'Boss kind 3 - stage-7 spitter',None,'CONVERT_MSX'),
 E('boss.n1.kind4','Final boss (kind 4)','boss',N1,'Boss kind 4 - final boss (stage 8)',None,'CONVERT_MSX'),
 E('boss.n1.kind2','Stage-6 boss (kind 2)','boss',N1,'Boss kind 2 - stage-6 pieces with turrets',None,'CONVERT_MSX',note='MSX character set at display time unverified.'),
 E('enemy.n1.garun','Garun (NES-only sine flyer)','enemy',[],None,'garun','NOT_USED',note='Exists in Gradius NES only; no MSX Nemesis counterpart. Kept for reference, not part of Legends.'),
]
# Objects the CP0016 ROM already draws as MSX conversions (QA audit of OAM, stage 1).
NES_ONLY=[('enemy.nes.swarm_flyer','swarm_flyer'),('enemy.nes.pulsing_mine','pulsing_mine'),('scenery.nes.pod','scenery_pod'),('enemy.nes.blue_fish','blue_fish'),('boss.nes.orbiter','orbiter_core'),('boss.nes.orbiter_satellite','orbiter_satellite')]
for _cid,_n in NES_ONLY: MAP.append(E(_cid,_n+' (NES only, no MSX counterpart proven)','enemy' if 'enemy' in _cid else ('boss' if 'boss' in _cid else 'scenery'),[],None,_n,'NOT_USED',note='Gradius NES object with no proven MSX Nemesis counterpart; kept for reference.'))
ROM_INTEGRATED={'player.vic_viper','player.shield','player.option','weapon.shot','weapon.double','weapon.missile','weapon.laser','effect.explosion',
 'powerup.capsule','powerup.capsule_blue','enemy.n1.fan','enemy.n1.falling_pair','enemy.n1.row_fighter','enemy.n1.ducker','enemy.n1.jumper',
 'enemy.n1.volcano_rock','scenery.n1.volcano','enemy.n1.cannon','enemy.shot','boss.n1.bigcore'}
ROM_PALETTES=['0F 30 16 12','0F 16 30 26','0F 28 30 16','0F 30 1C 26']
# Deviations of the current ROM from the proven sources (QA audit of CP0016, stage 1). Work items for the ROM, not for the bible.
ROM_DEVIATIONS={
 'enemy.shot':'drawn with frame 27 (MSX pattern $6C, option debris) through DrawSprite8, palette 1: a 2x2 red dot; proven source is pattern $88 colour 9 (Big Core fires the same dots)',
 'powerup.capsule_blue':'drawn with the red capsule palette',
 'player.option':'no pattern $48 frame and no colour cycle (10/9/8/6)',
 'weapon.missile':'no rolling pattern $1C (slot 7 overwritten by ship records in build_native_assets.py) and no colour blink',
 'effect.explosion':'single palette for all four colour phases',
 'enemy.n1.rock':'a screen-fixed rock (pattern $C0, never BC/C4/C8) appears in stage 1 where the MSX spawns no type-8 rock',
 'powerup.bonus_capsule':'drawing $38 is outside the 56-drawing conversion',
 'enemy.n1.cannon':'drawn as a sprite only at angle step 2 while entering; no rotation',
 'enemy.n1.hatch':'no hatch sprites in the stage-1 OAM',
 'enemy.n1.hatch_bug':'no hatch-bug sprites in the stage-1 OAM',
 'hud.power_meter':'CP0016 draws a 32-column text HUD (ST/L/PWR/OP/SPD), not a power meter; nothing comparable to either source yet',
}
STATES=('identified','extracted','converted','integrated','tested','validated')

def strip_private(frame:dict)->dict:
    f={k:v for k,v in frame.items() if k not in ('png','screenshot')}
    ev=f.get('evidence')
    if isinstance(ev,dict): f['evidence']={k:v for k,v in ev.items() if k!='screenshot'}
    return f

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--msx',required=True);ap.add_argument('--nes',default=None);ap.add_argument('--qa',default=None);ap.add_argument('--rom-qa',default=None,help='QA report whose checks.rom hold the ROM observations (round 1)');a=ap.parse_args()
    msx={o['object']:o for o in json.load(open(pathlib.Path(a.msx)/'objects.json'))}
    nes={}
    if a.nes and (pathlib.Path(a.nes)/'objects.json').exists():
        for o in json.load(open(pathlib.Path(a.nes)/'objects.json')):
            nes[o['object']]=o
            for al in o.get('aliases',[]): nes.setdefault(al,o)
    qa={}
    if a.qa and pathlib.Path(a.qa).exists():
        qa={r['id']:r for r in json.load(open(a.qa))}
    romqa={r['id']:r for r in json.load(open(a.rom_qa))} if a.rom_qa and pathlib.Path(a.rom_qa).exists() else qa
    entries=[];missing_msx=[];missing_nes=[]
    for d in MAP:
        cid=d['id'];m=msx.get(d['msx']) if d['msx'] else None
        names=d['nes'] if isinstance(d['nes'],list) else ([d['nes']] if d['nes'] else [])
        found=[];seen=set()
        for x in names:
            if x in nes and id(nes[x]) not in seen: found.append(nes[x]);seen.add(id(nes[x]))
        if d['msx'] and m is None: missing_msx.append((cid,d['msx']))
        for x in names:
            if x not in nes: missing_nes.append((cid,x))
        policy=d['policy']
        if not found and policy in ('REUSE_NES','ADAPT_NES'): eff='CONVERT_MSX (NES reference not yet proven)'
        else: eff=policy
        q=qa.get(cid)
        integrated=cid in ROM_INTEGRATED
        e=dict(id=cid,name=d['name'],role=d['role'],games=d['games'],
               msx=None if m is None else dict(game='nemesis',type=m.get('msx_type'),draw=m.get('draw'),stages=m.get('stages'),
                    frames=[strip_private(f) for f in m.get('frames',[])],evidence=m.get('evidence'),notes=m.get('notes')),
               nes_reference=None if not found else dict(game='gradius_nes_us',objects=[o['object'] for o in found],
                    frames=[dict(strip_private(f),object=o['object']) for o in found for f in o.get('frames',[])],notes=' | '.join(filter(None,(o.get('notes') for o in found)))),
               nes_candidates=d['cand'],
               legends=dict(policy=policy,effective=eff,
                            current_rom=dict(source='CONVERT_MSX',sprite_palettes=ROM_PALETTES,observation=(romqa.get(cid) or {}).get('checks',{}).get('rom')) if integrated else dict(source=None,observation=(romqa.get(cid) or {}).get('checks',{}).get('rom')),
                            chr=None,palette=None,
                            states=dict(identified=True,extracted=m is not None,converted=integrated,integrated=integrated,tested=False,validated=False)),
               notes=d['note'],
               rom_deviation=ROM_DEVIATIONS.get(cid),
               qa=dict(verdict=(q or {}).get('verdict','PENDING'),reason=(q or {}).get('reason'),proposed_fix=(q or {}).get('proposed_fix'),checks=(q or {}).get('checks')))
        entries.append(e)
    bible=dict(schema=1,generated=datetime.date.today().isoformat(),
               rules=['identification by code (MSX) and OAM capture (NES) only; never by look',
                      'objects shared by the four games have one official Legends version',
                      'NES reference is the base where it exists (Gradius NES, Life Force / Salamander FC); Nemesis 2 and 3 objects without a reference are CONVERT_MSX or REDRAW',
                      'official colours are real NES palettes from captures',
                      'validated only after QA checks the entry against both evidences and the current ROM'],
               unmapped_msx_objects=[k for k in msx if k not in {x['msx'] for x in MAP}],
               unmapped_nes_objects=[k for k,o in nes.items() if k==o['object'] and k not in {y for x in MAP for y in (x['nes'] if isinstance(x['nes'],list) else [x['nes']])}],
               missing_msx=missing_msx,missing_nes=missing_nes,
               rom_deviations=ROM_DEVIATIONS,entries=entries)
    (ROOT/'manifests/asset_bible.json').write_text(json.dumps(bible,indent=1)+'\n')
    lines=['# Asset bible (generated by tools/asset_bible.py; do not edit)','',
           'One record per game object. MSX facts come from the code (pattern written into the sprite/char slot); NES facts from OAM captures correlated with screenshots. Policies: REUSE_NES, ADAPT_NES, CONVERT_MSX, REDRAW, NEW.','',
           '| id | name | games | MSX (type / draw / first frame) | NES reference (first frame) | Legends policy | effective | current ROM | QA |','|---|---|---|---|---|---|---|---|---|']
    for e in entries:
        m=e['msx'];n=e['nes_reference']
        if not e['games']: g='NES only'
        else: g=','.join({'nemesis':'N1','nemesis2':'N2','salamander':'SAL','nemesis3':'N3'}[x] for x in e['games'])
        ms='-' if not m else f"{m['type'] if m['type'] is not None else '-'} / {m['draw']} / "+(f"P{m['frames'][0]['patterns']} C{m['frames'][0]['colour']}" if m['frames'] and m['frames'][0].get('patterns') else (m['frames'][0]['name'] if m['frames'] else '-'))
        ns='-' if not n else (f"{'+'.join(n['objects'])}: bank {n['frames'][0].get('chr_bank')} tiles {[(t[0] if isinstance(t,(list,tuple)) else t) for t in n['frames'][0].get('tiles',[])][:6]} pal {n['frames'][0].get('palette_nes')}" if n['frames'] else '-')
        lines.append(f"| {e['id']} | {e['name']} | {g} | {ms} | {ns} | {e['legends']['policy']} | {e['legends']['effective']} | {'ROM: MSX conv.' if e['legends']['states']['integrated'] else 'not in ROM'} | {e['qa']['verdict']} |")
    from collections import Counter
    c=Counter(e['qa']['verdict'] for e in entries);pc=Counter(e['legends']['effective'] for e in entries)
    lines+=['',f"QA verdicts: {dict(c)}",f"Effective policies: {dict(pc)}",'','## Current ROM deviations (work items)','']+[f"- **{k}**: {v}" for k,v in ROM_DEVIATIONS.items()]
    lines+=['',f"Unmapped MSX objects: {bible['unmapped_msx_objects']}",f"Missing MSX: {missing_msx}",f"Missing NES: {missing_nes}",f"Unmapped NES objects: {bible['unmapped_nes_objects']}"]
    (ROOT/'docs/ASSET_BIBLE.md').write_text('\n'.join(lines)+'\n')
    print('entries',len(entries),'missing_msx',missing_msx,'missing_nes',len(missing_nes),'unmapped_msx',bible['unmapped_msx_objects'])
if __name__=='__main__':main()
