#!/usr/bin/env python3
"""Correct the titles of the ripped tracks (audio/*/tracks.json and audio/tracklist.csv)
with the music catalogue of Phase 1c (manifests/catalog_music.json).

The rips were titled from album order and upstream configuration. The catalogue logs
every request of each game in play, so the role of every command (stage BGM, boss,
jingle, channel part of another tune) is now known. Rules:
- Gradius II (Famicom): titles follow the in-game sound mode labels, matched by where
  each code plays (the rip had 8 of 15 titles on the wrong code).
- Gradius and Salamander (Famicom): album titles stay where the role confirms them;
  codes whose role was wrong get a descriptive title with status contextual_not_official.
- MSX rips: the catalogue name of the code; a code that is only an extra channel of
  another tune is marked as such (the Nemesis rip listed channel parts as tracks).
"""
from __future__ import annotations
import csv, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SLUG = {'gradius': 'gradius_nes', 'gradius2_fc': 'gradius2_fc', 'salamander_fc': 'salamander_fc',
        'nemesis_msx': 'nemesis', 'nemesis2_msx': 'nemesis2', 'salamander_msx': 'salamander',
        'lifeforce': 'lifeforce_nes', 'nemesis3_msx': 'nemesis3'}
# Rips made in Phase 1c (tools/rip_lifeforce_nsf.py, tools/rip_nemesis3_kss.py): driver file per slug.
NEW_RIPS = {'lifeforce': ('audio/native_nes/lifeforce/lifeforce_nes_us_original_driver.nsf', 'NSF'),
            'nemesis3_msx': ('audio/msx_reference/nemesis3_msx/nemesis3_msx_original_driver.kss', 'KSS')}
# Album titles kept by role (Gradius stage 4/boss/ending: album order and role agree).
GRADIUS_ALBUM = {0x5D: 'Free Flyer (Stage 4)', 0xA5: 'Aircraft Carrier (Boss)', 0xB2: 'All Pattern Clear (Ending)'}
SALAMANDER_FC = {0x3A: ('Poison of Snake (Boss)', 'published_title'),
                 0x3D: ('Crystal Forever (Game Over)', 'published_title'),
                 0x43: ('Game Start Jingle', 'contextual_not_official'),
                 0x22: ('Aircraft Carrier (Stage 5 interlude)', 'published_title'),  # Life Force code 0x22 = stage-5 battleship tune; only album title left
                 0x34: ('Thunderbolt (Stage 5, resumed after the interlude)', 'published_title')}

def title_for(game, cmd, entry, old=None):
    if entry is None: return None
    pub = entry.get('published_title')
    if pub and old and old.lower().startswith(pub.lower()) and not (game == 'salamander_fc' and cmd in SALAMANDER_FC):
        return old, 'published_title'   # album title already on the right code
    if game == 'gradius2_fc' and pub: return pub, 'published_title'
    if game == 'gradius_nes':
        if cmd in GRADIUS_ALBUM: return GRADIUS_ALBUM[cmd], 'published_title'
        if pub: return '%s (%s)' % (pub, entry['name']) if pub != entry['name'] else pub, 'published_title'
        return entry['name'], 'contextual_not_official'
    if game == 'salamander_fc':
        if cmd in SALAMANDER_FC: return SALAMANDER_FC[cmd]
        if pub: return '%s (%s)' % (pub, entry['name']), 'published_title'
        return entry['name'], 'contextual_not_official'
    if entry.get('kind') == 'part':
        return 'Channel part of %s (%s)' % (entry.get('part_of') or 'another tune', entry['name']), 'channel_part_not_a_track'
    return entry['name'], 'contextual_not_official'

def main():
    cat = json.loads((ROOT / 'manifests/catalog_music.json').read_text())
    by = {g: {int(r['code'], 16): r for r in v.get('sounds', [])} for g, v in cat['games'].items()}
    changed = {}
    for p in sorted((ROOT / 'audio').glob('*/*/tracks.json')):
        slug = p.parent.name; game = SLUG.get(slug)
        if not game or game not in by: continue
        d = json.loads(p.read_text())
        tracks = d if isinstance(d, list) else d['tracks']
        for t in tracks:
            if isinstance(t['command'], str): t['command'] = int(t['command'], 16)
            cmd = t['command']; t['source_command_hex'] = '%02X' % cmd; new = title_for(game, cmd, by[game].get(cmd), t.get('title'))
            if not new: continue
            if (t.get('title'), t.get('title_status')) != new:
                changed[(slug, t['index'])] = (t.get('title'), new[0])
            t['title'], t['title_status'] = new
            t['command_mapping_status'] = 'gameplay_logged_phase1c'
            t['catalogue_ref'] = 'manifests/catalog_music.json:%s:0x%02X' % (game, cmd)
        p.write_text(json.dumps(d, indent=2) + '\n')
    tl = ROOT / 'audio/tracklist.csv'
    if tl.exists():
        rows = list(csv.DictReader(tl.open(encoding='utf-8-sig'))); fields = list(rows[0].keys()) if rows else []
        for slug, (drv, fmt) in NEW_RIPS.items():
            tj = ROOT / pathlib.Path(drv).parent / 'tracks.json'
            if not tj.is_file() or any(r['driver'] == drv for r in rows): continue
            d = json.loads(tj.read_text()); tracks = d if isinstance(d, list) else d['tracks']
            for t in tracks:
                cmd = t['command'] if isinstance(t['command'], int) else int(t['command'], 16)
                rows.append({**{k: '' for k in fields}, 'driver': drv, 'index': str(t['index']), 'source_command_hex': '%02X' % cmd,
                             'title': t.get('title', ''), 'title_status': t.get('title_status', ''), 'driver_format': fmt})
        for r in rows:
            slug = next((s for s in SLUG if '/%s/' % s in r['driver']), None)
            if not slug: continue
            game = SLUG[slug]; cmd = int(r['source_command_hex'], 16); new = title_for(game, cmd, by.get(game, {}).get(cmd), r.get('title'))
            if new:
                r['title'], r['title_status'] = new; r['command_mapping_status'] = 'gameplay_logged_phase1c'
        with tl.open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    for (slug, i), (old, new) in sorted(changed.items()):
        print('%-15s #%-2d %s  ->  %s' % (slug, i, old, new))

if __name__ == '__main__':
    main()
