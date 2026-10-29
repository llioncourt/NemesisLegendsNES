#!/usr/bin/env python3
"""Phase 1 asset catalogue of the four MSX games (owner's scope, docs/DECISIONS.md).

Merges the private, code-proven evidence folders (one per game, produced from the
ROMs, the pinned disassemblies and openMSX captures; see docs/CATALOG_MSX.md for
the method) into one public catalogue that holds no ROM bytes: object names,
roles, stages, pattern/char numbers, TMS9918 colour numbers, code references and
proof status only.

    python tools/catalog_msx.py --evidence /path/to/evidence [--sheets OUTDIR]

Outputs: manifests/catalog_msx.json, docs/CATALOG_MSX.md and, with --sheets,
private contact sheets (derived graphics: never commit them).
"""
from __future__ import annotations
import argparse, collections, datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
GAMES = [('nemesis', 'n1', 'Nemesis'), ('nemesis2', 'n2', 'Nemesis 2'),
         ('salamander', 'sal', 'Salamander'), ('nemesis3', 'n3', 'Nemesis 3')]
ROLES = ['player', 'player_weapon', 'powerup', 'item', 'hud', 'enemy', 'subboss', 'boss',
         'boss_part', 'projectile', 'effect', 'scenery']
SCREEN_KINDS = ['title', 'intro', 'story', 'cutscene', 'interlude', 'ending', 'staff',
                'gameover', 'continue', 'ranking', 'demo', 'option', 'other']
FRAME_KEYS = ('name', 'layout', 'patterns', 'colour', 'sprite_offsets', 'chars', 'charset', 'source')

def load(path, default):
    try: return json.loads(path.read_text())
    except FileNotFoundError: return default

def check_object(o, prefix, problems, gap_text):
    oid = o.get('id', '?')
    if not str(oid).startswith(prefix + '.'): problems.append('%s: id must start with %s.' % (oid, prefix))
    if o.get('role') not in ROLES: problems.append('%s: unknown role %r' % (oid, o.get('role')))
    # An object without a drawing is allowed only when the evidence explains it (unused
    # type, empty code, secret with no picture): in its notes or in gaps.json.
    if not o.get('frames') and not (o.get('notes') or oid in gap_text):
        problems.append('%s: no frames and no explanation' % oid)
    if not o.get('code_refs') and not any(f.get('source') for f in o.get('frames') or []):
        problems.append('%s: no code reference' % oid)

def count_unmapped(node):
    """Sum every 'unmapped' entry in a coverage file, whatever its nesting."""
    total = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if 'unmapped' in str(k).lower():
                total += len(v) if isinstance(v, (list, dict)) else (v if isinstance(v, int) and not isinstance(v, bool) else 0)
            else:
                total += count_unmapped(v)
    elif isinstance(node, list):
        total += sum(count_unmapped(v) for v in node)
    return total

def shape(v):
    """Rows x columns of a char layout without copying the ROM table itself."""
    if isinstance(v, list) and v and all(isinstance(r, list) for r in v):
        return [len(v), max(len(r) for r in v)]
    return [1, len(v)] if isinstance(v, list) else None

def public_frame(f):
    out = {k: f.get(k) for k in FRAME_KEYS if f.get(k) is not None and k != 'chars'}
    chars = f.get('chars')
    if isinstance(chars, list) and len(json.dumps(chars)) > 64:
        # Large char-drawn layouts (bosses, scenery) are ROM tables: keep their size only;
        # the layout itself stays in the private evidence (source gives the address).
        out['chars_layout'] = shape(chars)
    elif chars is not None:
        out['chars'] = chars
    return out

def build(evidence: pathlib.Path):
    cat = dict(schema=1, generated=datetime.date.today().isoformat(),
               method='docs/CATALOG_MSX.md', games={})
    problems = []
    for game, prefix, title in GAMES:
        folder = evidence / game
        objects = load(folder / 'objects.json', None)
        if objects is None:
            cat['games'][game] = dict(title=title, status='missing'); continue
        screens = load(folder / 'screens.json', [])
        stages = load(folder / 'stages.json', [])
        gaps = load(folder / 'gaps.json', [])
        coverage = load(folder / 'coverage.json', {})
        ids = collections.Counter(o.get('id') for o in objects)
        problems += ['%s: duplicate id' % i for i, n in ids.items() if n > 1]
        gap_text = json.dumps(gaps, ensure_ascii=False)
        for o in objects: check_object(o, prefix, problems, gap_text)
        pub = []
        for o in objects:
            pub.append(dict(id=o.get('id'), name=o.get('name'), series_name=o.get('series_name'),
                            role=o.get('role'), msx_type=o.get('msx_type'), stages=o.get('stages') or [],
                            draw=o.get('draw'), hp=o.get('hp'), frames=[public_frame(f) for f in o.get('frames') or []],
                            code_refs=o.get('code_refs') or [], behaviour_ref=o.get('behaviour_ref'),
                            proven_in_emulator=bool(o.get('capture_proof')), excluded=o.get('excluded'),
                            notes=o.get('notes') or ''))
        pscreens = [dict(id=s.get('id'), name=s.get('name'), kind=s.get('kind'), how_shown=s.get('how_shown'),
                         graphics_source=s.get('graphics_source'), code_refs=s.get('code_refs') or [],
                         proven_in_emulator=bool(s.get('capture_proof')), notes=s.get('notes') or '')
                    for s in screens]
        for s in pscreens:
            if s['kind'] not in SCREEN_KINDS: problems.append('%s: unknown screen kind %r' % (s['id'], s['kind']))
        pstages = [{k: v for k, v in st.items() if not (isinstance(v, str) and re.fullmatch(r'[0-9a-f]{64,}', v))}
                   for st in stages]
        unmapped = count_unmapped(coverage) if coverage else None
        roles = collections.Counter(o['role'] for o in pub)
        cat['games'][game] = dict(
            title=title, status='catalogued', objects=pub, screens=pscreens, stages=pstages,
            gaps=gaps, counts=dict(objects=len(pub), by_role=dict(sorted(roles.items())),
                                   frames=sum(len(o['frames']) for o in pub), screens=len(pscreens),
                                   stages=len(pstages), gaps=len(gaps),
                                   excluded=sum(1 for o in pub if o['excluded']),
                                   proven_in_emulator=sum(1 for o in pub if o['proven_in_emulator']),
                                   without_drawing=sum(1 for o in pub if not o['frames']),
                                   unmapped_in_emulator=unmapped))
    cat['problems'] = problems
    return cat

def markdown(cat):
    L = ['# MSX asset catalogue (Phase 1) - generated by tools/catalog_msx.py; do not edit', '',
         'One record per game object of the four MSX games, proven from the Z80 code (pattern or',
         'character written by the code, colour as the code sets it) and checked in openMSX captures',
         'of every stage. Pattern numbers are 16x16 sprite numbers as the code uses them (multiples of',
         '4); colours are TMS9918 numbers. No ROM bytes are stored here: the graphics live in the',
         'private evidence folders and contact sheets. Owner rules: docs/DECISIONS.md.', '',
         '## Totals', '', '| game | objects | frames | screens | stages | in emulator | excluded | gaps |',
         '|---|---|---|---|---|---|---|---|']
    for game, g in cat['games'].items():
        c = g.get('counts')
        if not c: L.append('| %s | missing | | | | | | |' % g['title']); continue
        L.append('| %s | %d | %d | %d | %d | %d | %d | %d |' % (g['title'], c['objects'], c['frames'], c['screens'],
                 c['stages'], c['proven_in_emulator'], c['excluded'], c['gaps']))
    for game, g in cat['games'].items():
        if not g.get('objects'): continue
        L += ['', '## %s' % g['title'], '', 'By role: ' + ', '.join('%s %d' % kv for kv in g['counts']['by_role'].items()), '',
              '| id | name | series name | role | type | stages | draw | frames | first frame | emulator |',
              '|---|---|---|---|---|---|---|---|---|---|']
        order = {r: i for i, r in enumerate(ROLES)}
        for o in sorted(g['objects'], key=lambda o: (order.get(o['role'], 99), o['id'])):
            f = o['frames'][0] if o['frames'] else {}
            first = ('P%s C%s' % (f.get('patterns'), f.get('colour'))) if f.get('patterns') is not None else \
                    ('chars %s' % f.get('chars') if f.get('chars') is not None else '-')
            st = o['stages']; st = ', '.join(st[:6]) + (' +%d' % (len(st) - 6) if len(st) > 6 else '')
            name = o['name'] + (' (excluded: %s)' % o['excluded'] if o['excluded'] else '')
            L.append('| %s | %s | %s | %s | %s | %s | %s | %d | %s | %s |' % (
                o['id'], name, o['series_name'] or '-', o['role'], '-' if o['msx_type'] is None else o['msx_type'],
                st or '-', o['draw'], len(o['frames']), first, 'yes' if o['proven_in_emulator'] else 'no'))
        if g['screens']:
            L += ['', '### %s screens' % g['title'], '', '| id | name | kind | shown | emulator |', '|---|---|---|---|---|']
            for s in g['screens']:
                L.append('| %s | %s | %s | %s | %s |' % (s['id'], s['name'], s['kind'], (s['how_shown'] or '-').replace('|', '/'),
                                                       'yes' if s['proven_in_emulator'] else 'no'))
        if g['gaps']:
            L += ['', '### %s gaps' % g['title'], '']
            for gap in g['gaps']:
                L.append('- ' + (gap if isinstance(gap, str) else json.dumps(gap, ensure_ascii=False)))
    if cat['problems']:
        L += ['', '## Schema problems', ''] + ['- ' + p for p in cat['problems']]
    return '\n'.join(L) + '\n'

def sheets(evidence: pathlib.Path, out: pathlib.Path, cat):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    out.mkdir(parents=True, exist_ok=True); made = []
    for game, prefix, title in GAMES:
        g = cat['games'].get(game) or {}
        objs = load(evidence / game / 'objects.json', [])
        if not objs: continue
        by_role = collections.defaultdict(list)
        for o in objs: by_role[o.get('role')].append(o)
        for role in [r for r in ROLES if by_role.get(r)]:
            cards = []
            for o in by_role[role]:
                p = evidence / game / (o.get('png') or '')
                if not o.get('png') or not p.is_file(): continue
                im = Image.open(p).convert('RGB')
                if im.width > 900: im = im.resize((900, im.height * 900 // im.width), Image.NEAREST)
                cards.append((o, im))
            if not cards: continue
            W = 960; y = 50; rows = []
            for o, im in cards: rows.append((y, o, im)); y += im.height + 34
            sheet = Image.new('RGB', (W, y + 10), (16, 16, 22)); d = ImageDraw.Draw(sheet)
            d.text((14, 12), '%s - %s (%d)' % (title, role, len(cards)), fill=(255, 200, 90), font=bold)
            for yy, o, im in rows:
                label = '%s  %s%s' % (o.get('id'), o.get('name'), '  [excluded]' if o.get('excluded') else '')
                d.text((14, yy), label, fill=(235, 235, 240), font=font)
                sheet.paste(im, (14, yy + 20))
            path = out / ('%s_%s.png' % (prefix, role)); sheet.save(path); made.append(path)
    return made

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', type=pathlib.Path, required=True)
    ap.add_argument('--sheets', type=pathlib.Path)
    a = ap.parse_args()
    cat = build(a.evidence)
    (ROOT / 'manifests/catalog_msx.json').write_text(json.dumps(cat, indent=None, separators=(',', ':'), ensure_ascii=False).replace('{"id":', '\n{"id":') + '\n')
    (ROOT / 'docs/CATALOG_MSX.md').write_text(markdown(cat))
    for game, g in cat['games'].items():
        print(game, json.dumps(g.get('counts', g.get('status'))))
    print('schema problems:', len(cat['problems']))
    if a.sheets:
        for p in sheets(a.evidence, a.sheets, cat): print('sheet', p)
    return 0

if __name__ == '__main__':
    sys.exit(main())
