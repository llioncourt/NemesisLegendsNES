#!/usr/bin/env python3
"""Phase 2a: for every object and screen of the four MSX games, the NES version found in
Gradius, Gradius II, Life Force and Salamander (Famicom), and the version chosen.

Owner's rules (docs/DECISIONS.md): if an asset exists on the NES it is used, whatever NES
game it comes from; if several NES games have it, the most detailed one wins (Gradius II,
the art direction, breaks ties); NES vs MSX is compared first, then NES vs NES. The player
ships are always the Salamander (Famicom) ships (decision OWNER_SHIP).

Merges the private per-game evidence (`nes_match.json`: candidates with verdicts and
evidence, the decision and the reason) into a public table without graphics.

    python tools/asset_choice.py --evidence /path/to/evidence
Outputs: manifests/asset_choice.json, docs/ASSET_CHOICE.md.
"""
from __future__ import annotations
import argparse, collections, datetime, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
GAMES = [('nemesis', 'Nemesis'), ('nemesis2', 'Nemesis 2'), ('salamander', 'Salamander'), ('nemesis3', 'Nemesis 3')]
DECISIONS = ['REUSE_NES', 'ADAPT_NES', 'OWNER_SHIP', 'CONVERT_MSX', 'NOT_NEEDED']
NES_TITLES = {'gradius_nes': 'Gradius', 'gradius2_fc': 'Gradius II', 'lifeforce_nes': 'Life Force', 'salamander_fc': 'Salamander FC'}

# Phase 2, NES vs NES: assets that several MSX games share get ONE NES version for the whole
# game (the per-game comparisons sometimes picked different NES games for the same asset).
# Winner = the most detailed version; Gradius II (art direction) on equal detail. Reviewed on
# side-by-side sheets of every member (CP0021).
SHARED = [
 ('player death explosion', ['g2.player.vic_viper_explosion', 'gr.effect.vic_viper_explosion', 'sfc.player.p1_death'], 'sfc.player.p1_death',
  'the explosion of the owner-chosen Salamander FC ship; most detailed (6 drawings)'),
 ('option', ['g2.player.option', 'gr.player_weapon.option', 'lf.player.option', 'sfc.player.p1_option'], 'sfc.player.p1_option',
  'matches the Salamander FC ship set; most frames (12, two palettes); player 2 keeps sfc.player.p2_option'),
 ('normal shot', ['g2.weapon.normal_shot', 'gr.player_weapon.shot', 'lf.weapon.normal_shot', 'sfc.weapon.normal_shot'], 'sfc.weapon.normal_shot',
  'most frames, with the vertical-stage drawings the Salamander chapters need'),
 ('laser', ['g2.weapon.laser', 'gr.player_weapon.laser', 'lf.weapon.laser', 'sfc.weapon.laser'], 'lf.weapon.laser',
  'most detailed: 26 frames covering every laser length (same art as Salamander FC)'),
 ('missile', ['g2.weapon.missile', 'gr.player_weapon.missile', 'lf.weapon.missile', 'sfc.weapon.missile'], 'sfc.weapon.missile',
  'most frames (12, all directions incl. vertical stages); missile variants adapt from it'),
 ('ripple laser', ['g2.weapon.ripple', 'lf.weapon.ripple', 'sfc.weapon.ripple'], 'sfc.weapon.ripple', 'most frames (12 vs 3)'),
 ('status bar', ['g2.hud.status_bar', 'gr.hud.status_bar', 'lf.hud.status_bar', 'sfc.hud.status_bar'], 'g2.hud.status_bar',
  'art direction; the project already uses the Gradius II HUD font'),
 ('font', ['g2.font.hud', 'gr.font.hud', 'gr.font.title_us', 'lf.font.hud', 'sfc.font.hud'], 'g2.font.hud',
  'the only complete NES alphabet among them; art direction'),
 ('red capsule', ['g2.item.capsule', 'gr.powerup.capsule_red', 'lf.item.capsule_red', 'sfc.item.capsule_red'], 'sfc.item.capsule_red',
  'same design in all; Salamander FC / Life Force animate it in more frames'),
 ('blue capsule', ['gr.powerup.capsule_blue', 'lf.item.capsule_blue', 'sfc.item.capsule_blue'], 'sfc.item.capsule_blue', 'as the red capsule'),
 ('flashing capsule', ['lf.item.capsule_1up', 'sfc.item.capsule_1up'], 'sfc.item.capsule_1up', 'as the red capsule'),
 ('small explosion', ['g2.effect.explosion_small', 'gr.effect.explosion_medium', 'lf.effect.explosion_small', 'sfc.effect.explosion_small'],
  'sfc.effect.explosion_small', 'most detailed: 5 drawings with a full fireball (Gradius II has 2 small sparkles)'),
 ('large explosion', ['g2.effect.explosion_large', 'gr.effect.explosion_large', 'lf.effect.explosion_large_blue', 'sfc.effect.explosion_large'],
  'g2.effect.explosion_large', 'equal detail to Salamander FC (8-9 drawings); art direction'),
 ('ducker', ['gr.enemy.ducker', 'g2.enemy.jumper'], 'g2.enemy.jumper',
  'same swirl-walker design as the Gradius Ducker, redrawn with more frames (the Gradius II catalogue names it Jumper; its "ducker" is a different cannon walker)'),
 ('enemy bullet', ['g2.projectile.enemy_bullet', 'gr.projectile.enemy_bullet', 'lf.projectile.enemy_bullet', 'sfc.projectile.enemy_bullet'],
  'g2.projectile.enemy_bullet', 'same diamond design with rotation frames in Gradius II, Life Force and Salamander FC; art direction'),
 ('game over screen', ['g2.screen.game_over_continue', 'gr.screen.game_over', 'sfc.screen.game_over'], 'g2.screen.game_over_continue', 'art direction'),
 ('pause screen', ['g2.screen.pause', 'gr.screen.pause', 'sfc.screen.pause'], 'g2.screen.pause', 'art direction'),
]
# Per-object exceptions inside a shared group (player 2 assets, capsule colours used by Nemesis 2).
EXCEPTIONS = {'sal.player.p2_option': 'sfc.player.p2_option', 'n2.item.blue_capsule': 'sfc.item.capsule_blue',
              'n2.item.1up': 'sfc.item.capsule_1up', 'n2.item.bonus': 'sfc.item.capsule_1up',
              'n2.item.special_capsule': 'sfc.item.capsule_1up', 'n2.enemy.t36': None}
GAME_OF = {'gr': 'gradius_nes', 'g2': 'gradius2_fc', 'lf': 'lifeforce_nes', 'sfc': 'salamander_fc'}

def reconcile(row):
    ch = row['chosen'] if isinstance(row['chosen'], dict) else None
    if row['decision'] not in ('REUSE_NES', 'ADAPT_NES') or not ch: return
    if row['msx_id'] in EXCEPTIONS:
        win = EXCEPTIONS[row['msx_id']]; group = 'exception'; why = 'colour/player variant of a shared asset'
        if win is None: return
    else:
        hit = next(((g, w, r) for g, m, w, r in SHARED if ch.get('nes_id') in m), None)
        if not hit: return
        group, win, why = hit
    if ch.get('nes_id') == win: return
    row['agent_choice'] = dict(ch)
    row['chosen'] = dict(nes_game=GAME_OF[win.split('.')[0]], nes_id=win)
    row['shared_asset'] = dict(group=group, reason=why)

def entries(doc):
    if isinstance(doc, list): return doc
    for k in ('entries', 'objects', 'matches'):
        if isinstance(doc.get(k), list): return doc[k]
    return []

def build(evidence):
    out = dict(schema=1, generated=datetime.date.today().isoformat(), rules='docs/DECISIONS.md phase 2', games={})
    problems = []
    for game, title in GAMES:
        p = evidence / game / 'nes_match.json'
        if not p.is_file():
            out['games'][game] = dict(title=title, status='pending'); continue
        rows = []
        for e in entries(json.loads(p.read_text())):
            d = e.get('decision')
            if d not in DECISIONS: problems.append('%s: unknown decision %r' % (e.get('msx_id'), d))
            ch = e.get('chosen') or {}
            if d in ('REUSE_NES', 'ADAPT_NES', 'OWNER_SHIP') and not (isinstance(ch, dict) and ch.get('nes_id') or isinstance(ch, list) and ch):
                problems.append('%s: %s without a chosen NES object' % (e.get('msx_id'), d))
            cands = [dict(nes_game=c.get('nes_game'), nes_id=c.get('nes_id'), verdict=c.get('verdict'), evidence=c.get('evidence'))
                     for c in e.get('candidates') or []]
            rows.append(dict(msx_id=e.get('msx_id'), msx_name=e.get('msx_name'), kind=e.get('msx_kind', 'object'),
                             decision=d, chosen=ch, why_chosen=e.get('why_chosen'), adapt_notes=e.get('adapt_notes'),
                             confidence=e.get('confidence'), candidates=cands, notes=e.get('notes') or ''))
            reconcile(rows[-1])
        dec = collections.Counter(r['decision'] for r in rows)
        src = collections.Counter()
        for r in rows:
            chs = r['chosen'] if isinstance(r['chosen'], list) else [r['chosen']]
            for c in chs:
                if isinstance(c, dict) and c.get('nes_game') and r['decision'] in ('REUSE_NES', 'ADAPT_NES'): src[c['nes_game']] += 1
        out['games'][game] = dict(title=title, status='compared', entries=rows,
                                  counts=dict(entries=len(rows), by_decision={k: dec.get(k, 0) for k in DECISIONS},
                                              chosen_from={NES_TITLES.get(k, k): v for k, v in src.most_common()},
                                              low_confidence=sum(1 for r in rows if r['confidence'] == 'low'),
                                              changed_by_shared_rule=sum(1 for r in rows if r.get('agent_choice'))))
    out['shared_assets'] = [dict(group=g, members=m, winner=w, reason=r) for g, m, w, r in SHARED]
    out['problems'] = problems
    return out

def cell(v, n=160):
    if isinstance(v, dict): v = '%s %s' % (NES_TITLES.get(v.get('nes_game'), v.get('nes_game') or ''), v.get('nes_id') or '')
    elif isinstance(v, list): v = '; '.join(cell(x, 80) for x in v)
    s = ('-' if v in (None, '') else str(v)).replace('|', '/').replace('\n', ' ').strip()
    return s if len(s) <= n else s[:n - 1] + '...'

def markdown(c):
    L = ['# Asset choice, MSX vs NES (Phase 2a) - generated by tools/asset_choice.py; do not edit', '',
         'For every object and screen of the MSX games: the NES versions found and the one chosen.',
         'REUSE_NES = NES drawing used as is; ADAPT_NES = same object, NES drawing needs work (missing frames,',
         'angles, states); CONVERT_MSX = no NES version, the MSX drawing will be converted in the project style',
         '(phase 5); OWNER_SHIP = player ship replaced by the Salamander (Famicom) ship (owner decision);',
         'NOT_NEEDED = unused, invisible or excluded. Side-by-side images are in the private evidence.', '',
         '| game | entries | reuse | adapt | owner ship | convert | not needed | chosen from | low confidence |',
         '|---|---|---|---|---|---|---|---|---|']
    for g in c['games'].values():
        k = g.get('counts')
        if not k: L.append('| %s | %s | | | | | | | |' % (g['title'], g['status'])); continue
        b = k['by_decision']
        L.append('| %s | %d | %d | %d | %d | %d | %d | %s | %d |' % (g['title'], k['entries'], b['REUSE_NES'], b['ADAPT_NES'], b['OWNER_SHIP'],
                 b['CONVERT_MSX'], b['NOT_NEEDED'], ', '.join('%s %d' % kv for kv in k['chosen_from'].items()) or '-', k['low_confidence']))
    L += ['', '## Shared assets: one NES version for the whole game (NES vs NES)', '',
          'Assets that several MSX games share get one NES version everywhere (phase 3 consistency starts here).',
          'Winner = most detailed version, Gradius II on equal detail; every group was reviewed on side-by-side sheets.', '',
          '| asset | NES versions compared | chosen | why |', '|---|---|---|---|']
    for sa in c.get('shared_assets', []):
        L.append('| %s | %s | %s | %s |' % (sa['group'], ', '.join(sa['members']), sa['winner'], sa['reason']))
    for g in c['games'].values():
        if not g.get('entries'): continue
        L += ['', '## %s' % g['title'], '', '| MSX id | name | decision | chosen NES object | why / what to adapt | confidence |', '|---|---|---|---|---|---|']
        order = {d: i for i, d in enumerate(DECISIONS)}
        for r in sorted(g['entries'], key=lambda r: (order.get(r['decision'], 9), r['msx_id'] or '')):
            why = r['why_chosen'] or ''
            if r['adapt_notes']: why = (why + ' / adapt: ' + r['adapt_notes']).strip(' /')
            L.append('| %s | %s | %s | %s | %s | %s |' % (r['msx_id'], cell(r['msx_name'], 60), r['decision'],
                     cell(r['chosen'] if r['decision'] in ('REUSE_NES', 'ADAPT_NES', 'OWNER_SHIP') else None), cell(why or r['notes'], 220), r['confidence'] or '-'))
    if c['problems']: L += ['', '## Problems', ''] + ['- ' + p for p in c['problems']]
    return '\n'.join(L) + '\n'

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', type=pathlib.Path, required=True)
    a = ap.parse_args()
    c = build(a.evidence)
    (ROOT / 'manifests/asset_choice.json').write_text(json.dumps(c, indent=1, ensure_ascii=False) + '\n')
    (ROOT / 'docs/ASSET_CHOICE.md').write_text(markdown(c))
    for g in c['games'].values(): print(g['title'], json.dumps(g.get('counts', g['status']), ensure_ascii=False))
    print('problems:', len(c['problems']))
    return 0

if __name__ == '__main__':
    sys.exit(main())
