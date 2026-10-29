#!/usr/bin/env python3
"""Phase 1b asset catalogue of the NES/Famicom Gradius games (docs/DECISIONS.md).

Same idea as tools/catalog_msx.py: merges the private evidence folders (objects
identified from the running game, OAM entries pixel-verified against the frame,
palettes from palette RAM, CHR from CHR-ROM banks or captured CHR-RAM) into a
public catalogue without ROM bytes: names, roles, stages, tile numbers and
layouts of sprite frames, NES palette indices, code/RAM references, confidence.

    python tools/catalog_nes.py --evidence /path/to/evidence [--sheets OUTDIR]
Outputs: manifests/catalog_nes.json, docs/CATALOG_NES.md (and private sheets).
"""
from __future__ import annotations
import argparse, collections, datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from catalog_msx import load, count_unmapped, shape, ROLES, SCREEN_KINDS, ROOT
GAMES = [('gradius_nes', 'gr', 'Gradius (NES US / Famicom JP)'), ('gradius2_fc', 'g2', 'Gradius II (Famicom)'),
         ('lifeforce_nes', 'lf', 'Life Force (NES US / Rev 1)'), ('salamander_fc', 'sfc', 'Salamander (Famicom)')]
FRAME_KEYS = ('name', 'orientation', 'stages', 'palette_index', 'palette_nes', 'chr_source', 'pixel_verified',
              'metasprite_id', 'layout')

def public_frame(f):
    out = {k: f.get(k) for k in FRAME_KEYS if f.get(k) not in (None, [], '')}
    tiles = f.get('tiles')
    if isinstance(tiles, list):
        # Sprite layouts (a few OAM entries) stay; big BG matrices are ROM tables: size only.
        if len(tiles) <= 32 and len(json.dumps(tiles)) <= 1200: out['tiles'] = tiles
        else: out['tiles_layout'] = shape(tiles) if tiles and isinstance(tiles[0], list) and not isinstance(tiles[0][0], int) else [len(tiles)]
    return out

def trim(node, limit=3000):
    """Keep stage records readable: large per-capture tables stay in the private evidence."""
    if isinstance(node, dict):
        return {k: (trim(v, limit) if len(json.dumps(v)) <= limit or isinstance(v, dict) else
                    '(large table: private evidence, %d entries)' % (len(v) if isinstance(v, (list, dict)) else 1))
                for k, v in node.items()}
    return node

def build(evidence):
    cat = dict(schema=1, generated=datetime.date.today().isoformat(), method='docs/CATALOG_METHOD.md', games={})
    problems = []
    for game, prefix, title in GAMES:
        folder = evidence / game
        objects = load(folder / 'objects.json', None)
        if objects is None:
            cat['games'][game] = dict(title=title, status='pending'); continue
        screens = load(folder / 'screens.json', []); stages = load(folder / 'stages.json', [])
        if isinstance(stages, dict): stages = stages.get('stages', [stages])
        stages = [trim(st) for st in stages]
        gaps = load(folder / 'gaps.json', []); coverage = load(folder / 'coverage.json', {})
        gap_text = json.dumps(gaps, ensure_ascii=False)
        ids = collections.Counter(o.get('id') for o in objects)
        problems += ['%s: duplicate id' % i for i, n in ids.items() if n > 1]
        pub = []
        for o in objects:
            oid = o.get('id', '?')
            if not str(oid).startswith(prefix + '.'): problems.append('%s: id must start with %s.' % (oid, prefix))
            if o.get('role') not in ROLES: problems.append('%s: unknown role %r' % (oid, o.get('role')))
            if not o.get('frames') and not (o.get('notes') or oid in gap_text):
                problems.append('%s: no frames and no explanation' % oid)
            pub.append(dict(id=oid, name=o.get('name'), series_name=o.get('series_name'), role=o.get('role'),
                            stages=o.get('stages') or [], sprite_mode=o.get('sprite_mode'), draw=o.get('draw'),
                            confidence=o.get('confidence'), frames=[public_frame(f) for f in o.get('frames') or []],
                            ram_refs=o.get('ram_refs') or [], code_refs=o.get('code_refs') or [],
                            variants=o.get('variants'), excluded=o.get('excluded'), notes=o.get('notes') or ''))
        pscreens = [dict(id=s.get('id'), name=s.get('name'), kind=s.get('kind'), how_shown=s.get('how_shown'),
                         code_refs=s.get('code_refs') or [], proven_in_emulator=bool(s.get('capture_proof') or s.get('evidence')),
                         notes=s.get('notes') or '') for s in screens]
        for s in pscreens:
            if s['kind'] not in SCREEN_KINDS: problems.append('%s: unknown screen kind %r' % (s['id'], s['kind']))
        roles = collections.Counter(o['role'] for o in pub)
        conf = collections.Counter(o['confidence'] or 'unset' for o in pub)
        frames = [f for o in pub for f in o['frames']]
        cat['games'][game] = dict(title=title, status='catalogued', objects=pub, screens=pscreens, stages=stages, gaps=gaps,
            counts=dict(objects=len(pub), by_role=dict(sorted(roles.items())), confidence=dict(sorted(conf.items())),
                        frames=len(frames), frames_pixel_verified=sum(1 for f in frames if f.get('pixel_verified') is True),
                        screens=len(pscreens), stages=len(stages), gaps=len(gaps),
                        unmapped_in_emulator=count_unmapped(coverage) if coverage else None))
    cat['problems'] = problems
    return cat

def markdown(cat):
    L = ['# NES asset catalogue (Phase 1b) - generated by tools/catalog_nes.py; do not edit', '',
         'One record per game object of the NES/Famicom Gradius games, identified in the running game',
         '(OAM entries pixel-verified against the frame, object slots and code in RAM) with tiles, layout and',
         'NES palette indices per frame. No ROM bytes: CHR and captures are private. Method: docs/CATALOG_METHOD.md.',
         '', '## Totals', '', '| game | objects | frames | pixel-verified | screens | stages | gaps |', '|---|---|---|---|---|---|---|']
    for g in cat['games'].values():
        c = g.get('counts')
        if not c: L.append('| %s | %s | | | | | |' % (g['title'], g['status'])); continue
        L.append('| %s | %d | %d | %d | %d | %d | %d |' % (g['title'], c['objects'], c['frames'], c['frames_pixel_verified'],
                                                           c['screens'], c['stages'], c['gaps']))
    order = {r: i for i, r in enumerate(ROLES)}
    for g in cat['games'].values():
        if not g.get('objects'): continue
        L += ['', '## %s' % g['title'], '', 'By role: ' + ', '.join('%s %d' % kv for kv in g['counts']['by_role'].items()) +
              '. Name confidence: ' + ', '.join('%s %d' % kv for kv in g['counts']['confidence'].items()) + '.', '',
              '| id | name | series name | role | stages | frames | confidence |', '|---|---|---|---|---|---|---|']
        for o in sorted(g['objects'], key=lambda o: (order.get(o['role'], 99), o['id'])):
            st = ', '.join(str(s) for s in o['stages'][:8])
            L.append('| %s | %s | %s | %s | %s | %d | %s |' % (o['id'], (o['name'] or '').replace('|', '/'), o['series_name'] or '-',
                     o['role'], st or '-', len(o['frames']), o['confidence'] or '-'))
        if g['screens']:
            L += ['', '### %s screens' % g['title'], '', '| id | name | kind |', '|---|---|---|']
            L += ['| %s | %s | %s |' % (s['id'], s['name'], s['kind']) for s in g['screens']]
        if g['gaps']:
            L += ['', '### %s gaps' % g['title'], '']
            L += ['- ' + (x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)) for x in g['gaps']]
    if cat['problems']: L += ['', '## Schema problems', ''] + ['- ' + p for p in cat['problems']]
    return '\n'.join(L) + '\n'

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', type=pathlib.Path, required=True)
    a = ap.parse_args()
    cat = build(a.evidence)
    (ROOT / 'manifests/catalog_nes.json').write_text(json.dumps(cat, indent=None, separators=(',', ':'), ensure_ascii=False)
                                                    .replace('{"id":', '\n{"id":') + '\n')
    (ROOT / 'docs/CATALOG_NES.md').write_text(markdown(cat))
    for g in cat['games'].values(): print(g['title'], json.dumps(g.get('counts', g.get('status'))))
    print('schema problems:', len(cat['problems']))
    return 0

if __name__ == '__main__':
    sys.exit(main())
