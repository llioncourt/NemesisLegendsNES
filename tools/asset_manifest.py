#!/usr/bin/env python3
"""Universal asset manifest for the four-game campaign.

Reads the extraction outputs and reports already in the tree (Nemesis, Nemesis 2,
Salamander, Nemesis 3 MSX; six NES references; audio drivers and tracks), the
native integration state recorded in manifests/content_coverage.json and the
source code, and writes:
  manifests/asset_manifest.json   one record per resource, six independent states
  manifests/asset_coverage.json   totals per game / category / state
  docs/ASSET_COVERAGE.md          generated summary (do not edit by hand)
States: identified, extracted, converted, integrated, tested, validated.
Reuse classes: REUSE, ADAPT, CONVERT, REDRAW, NEW, UNKNOWN. Nothing here claims
completion: a resource is only `validated` when compared against the original.
"""
from __future__ import annotations
import collections,csv,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p,default=None):
    p=ROOT/p
    return json.loads(p.read_text()) if p.exists() else default
SOURCES=load('manifests/selected_sources.json')
COVERAGE=load('manifests/content_coverage.json')
def sha_of(slug):return SOURCES.get(slug,{}).get('sha256')
R=[]
def add(**k):
    r=dict(id=k.pop('id'),name=k.pop('name'),game=k.pop('game'),platform=k.pop('platform'),rom=k.pop('rom',None),
           rom_sha256=sha_of(k.get('rom_slug')) if k.get('rom_slug') else k.pop('rom_sha256',None),
           bank=k.pop('bank',None),offset=k.pop('offset',None),category=k.pop('category'),format=k.pop('format','unknown'),
           size_bytes=k.pop('size_bytes',None),content_sha256=k.pop('content_sha256',None),dependencies=k.pop('dependencies',[]),
           nes_match=k.pop('nes_match',None),reuse_class=k.pop('reuse_class','UNKNOWN'),
           states=dict(identified=True,extracted=k.pop('extracted',False),converted=k.pop('converted',False),
                       integrated=k.pop('integrated',False),tested=k.pop('tested',False),validated=k.pop('validated',False)),
           path=k.pop('path',None),notes=k.pop('notes',''))
    k.pop('rom_slug',None)
    if k:raise ValueError('unknown fields %r'%sorted(k))
    R.append(r);return r

# ---------------------------------------------------------------- Nemesis (MSX)
N1=COVERAGE['chapters'][0]
N1_ROUTES=set(N1.get('native_stage_event_routes_integrated',[]))      # stages with ported end-sequence logic
N1_TESTED=set(N1.get('native_stage_entries_tested',[]))
N1_TYPES=set(N1.get('native_enemy_types_ported',[]))
n1_manifest=load('assets/msx/nemesis/stage_manifest.json',[])
n1_streams=load('assets/msx/nemesis/compressed_streams.json',[])
n1_mirrors=load('assets/msx/nemesis/mirror_records.json',[])
n1_tiles=load('reports/nemesis_extraction.json',{})
STAGE_NAMES={1:'Volcano',2:'Stonehenge',3:'Moai (sky)',4:'Inverted volcano',5:'Tentacles',6:'Cells (sky)',7:'Fortress approach',8:'Fortress',9:'Bonus 9',10:'Bonus 10',11:'Bonus 11',12:'Bonus 12'}
for m in n1_manifest:
    st=m['stage'];conv=True;integ=True  # all twelve compact descriptors are in the ROM (build_native_assets)
    add(id=f'n1.stage{st:02d}.terrain',name=f'Nemesis stage {st} terrain column script ({STAGE_NAMES.get(st,"")})',game='nemesis',platform='msx',
        rom_slug='nemesis_msx',bank=11 if m['script_address']<0xa000 else 12,offset=m.get('script_rom_offset'),category='terrain_map',format='msx_column_script',
        size_bytes=m.get('script_bytes',0),content_sha256=hashlib.sha256(bytes.fromhex(m['script_hex'])).hexdigest() if m.get('script_hex') else None,
        reuse_class='CONVERT',extracted=True,converted=conv,integrated=integ,tested=st in N1_TESTED,path=f'assets/msx/nemesis/stage_{st:02d}/',
        notes='static terrain only' if m.get('script_bytes') else 'no terrain (sky stage)')
    add(id=f'n1.stage{st:02d}.tiles',name=f'Nemesis stage {st} character set (3 thirds)',game='nemesis',platform='msx',rom_slug='nemesis_msx',
        category='tile_set',format='tms9918_pattern+colour',reuse_class='CONVERT',extracted=True,converted=True,integrated=True,tested=st in N1_TESTED,
        path=f'assets/msx/nemesis/stage_{st:02d}/source_vram.bin',notes='converted to 2bpp with four per-stage palettes; palette reduction provisional')
    add(id=f'n1.stage{st:02d}.sprites',name=f'Nemesis stage {st} sprite set (64 hardware + 56 software frames)',game='nemesis',platform='msx',rom_slug='nemesis_msx',
        category='sprite_set',format='tms9918_16x16+char_blocks',reuse_class='CONVERT',extracted=True,converted=True,integrated=True,tested=st in N1_TESTED,
        path='build/native/stage_%02d.bin'%st,notes='monochrome frames + fixed NES sprite palettes')
    add(id=f'n1.stage{st:02d}.script',name=f'Nemesis stage {st} end sequence / stage logic (final_de_la_fase_{st})' if st<=8 else f'Nemesis bonus stage {st} logic',
        game='nemesis',platform='msx',rom_slug='nemesis_msx',bank=1,category='stage_script',format='z80_code',reuse_class='CONVERT',extracted=True,
        converted=st in N1_ROUTES or st in (9,10,11),integrated=st in N1_ROUTES or st in (9,10,11),tested=st in N1_TESTED,
        notes={1:'volcano, five pieces, Big Core',2:'rock walls, rain, target, Big Core',3:'two Big Cores, target',4:'eruption, tower, boss 5, Big Core'}.get(st,'not ported'))
for i,s in enumerate(n1_streams):
    add(id=f'n1.rle.{i:03d}',name=f'Nemesis RLE graphics stream @{s["cpu_address"]:04X} bank {s["bank"]}',game='nemesis',platform='msx',rom_slug='nemesis_msx',
        bank=s['bank'],offset=s['rom_offset'],category='compressed_stream',format='konami_rle',size_bytes=s['compressed_bytes'],content_sha256=s['sha256'],
        reuse_class='CONVERT',extracted=True,converted=True,integrated=True,notes='decoded into per-stage character sets')
add(id='n1.tiles.dictionary',name='Nemesis unique indexed 8x8 tiles',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='tile_dictionary',format='indexed_8x8',
    size_bytes=(ROOT/'assets/msx/nemesis/source_indexed_tile_dictionary.bin').stat().st_size if (ROOT/'assets/msx/nemesis/source_indexed_tile_dictionary.bin').exists() else None,
    reuse_class='CONVERT',extracted=True,converted=True,integrated=True,path='assets/msx/nemesis/source_indexed_tile_dictionary.bin',notes=f'{n1_tiles.get("unique_pixel_tiles")} unique tiles, {len(n1_mirrors)} mirror records')
add(id='n1.metatiles',name='Nemesis compact metatile table (bank 11)',game='nemesis',platform='msx',rom_slug='nemesis_msx',bank=11,offset=11*8192,category='metatile_table',format='msx_metatiles',
    size_bytes=0x97de-0x8000,reuse_class='CONVERT',extracted=True,converted=True,integrated=True,tested=True,path='build/native/metatiles.bin')
BIGCORE=dict(id='n1.boss.bigcore',name='Nemesis Big Core (boss kind 0, p01:7C8D) background graphics + logic',game='nemesis',platform='msx',rom_slug='nemesis_msx',bank=1,
    category='boss',format='z80_code+chars',reuse_class='CONVERT',extracted=True,converted=True,integrated=True,tested=True,path='build/native/boss.bin')
add(**BIGCORE)
for kind,addr,where,state in [(1,'p01:839F','stage ? (E06A second loop: kind 6 replaces 1)',False),(2,'p01:7F74','stage 5/6 boss',False),(3,'p01:8719','stage 7 boss',False),
                              (4,'p01:87F3','stage 8 final boss',False),(5,'p02:8CE4','stage 4 piece spawner',True),(6,'p01:83A5','second-loop replacement of kind 1',False)]:
    add(id=f'n1.boss.kind{kind}',name=f'Nemesis boss kind {kind} ({addr}): {where}',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='boss',format='z80_code',
        reuse_class='CONVERT',extracted=True,converted=state,integrated=state,tested=state,notes='ported in CP0012' if state else 'not ported')
for enc,addr,state in [('eruption (tanda) modes 1 and 2','p01:70D6',True),('five-piece tower','p02:8E77',True),('secret targets / bonus routing','p03:B06A',True),
                       ('stage-2 rock walls and rain','p03:AB86',True),('stage-5 bank-3 encounters','p03:B946/BB95',False),('stage-8 ending explosion','p01:6F43',False)]:
    add(id='n1.encounter.'+re.sub(r'[^a-z0-9]+','_',enc.lower()).strip('_'),name=f'Nemesis encounter: {enc} ({addr})',game='nemesis',platform='msx',rom_slug='nemesis_msx',
        category='encounter',format='z80_code',reuse_class='CONVERT',extracted=True,converted=state,integrated=state,tested=state)
MOVERS=[0x9119,0xa8b2,0xa836,0xa863,0xa9fb,0xa95a,0x5ee7,0xacbd,0xad33,0xad92,0xade5,0xae1b,0xafbd,0x5f4f,0x71ad,0x71b0,0x5e3b,0x5e3b,0x5e3b,0x5ec8,0x5e3e,0x5e3b,0xa7d9,0xa7d9,0x5e3b,0xa7df,0xb915,0x5f4f,0xb9ff,0xbce3,0xbd7d]
for t in range(1,32):
    add(id=f'n1.enemy.type{t:02x}',name=f'Nemesis object type ${t:02X} mover @{MOVERS[t-1]:04X}',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='enemy_type',
        format='z80_code',reuse_class='CONVERT',extracted=True,converted=t in N1_TYPES,integrated=t in N1_TYPES,tested=t in N1_TYPES,
        notes='ported' if t in N1_TYPES else ('explosion/capsule/system type' if t in (0x11,0x12,0x13,0x14,0x15,0x16) else 'not ported'))
add(id='n1.player',name='Nemesis player ship, options, weapons, power meter',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='player',format='z80_code+sprites',
    reuse_class='CONVERT',extracted=True,converted=True,integrated=True,tested=True,notes='60 combat assertions; shield/laser/missile/double/options')
add(id='n1.cheats',name='Nemesis pause-keyboard cheats (HYPER, stage names)',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='system',format='z80_code',reuse_class='ADAPT',extracted=True,
    notes='to be folded into the Silicon Forge cheat menu')
add(id='n1.ending',name='Nemesis ending sequence',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='cutscene',format='unknown',reuse_class='UNKNOWN',extracted=False,
    notes='location and format not yet identified')
add(id='n1.title',name='Nemesis / Gradius title screen (region logo)',game='nemesis',platform='msx',rom_slug='nemesis_msx',category='title_screen',format='chars',reuse_class='NEW',extracted=True,
    notes='replaced by the Nemesis Legends title; original kept as reference only')

# ---------------------------------------------------------------- Nemesis 2 (MSX)
N2_NATIVE=(ROOT/'build/native/n2_assets.json').exists()
N3_NATIVE=(ROOT/'build/native/n3_assets.json').exists()
n2=load('assets/msx/nemesis2/stage_manifest.json',[]);n2s=load('assets/msx/nemesis2/compressed_streams.json',[]);n2r=load('reports/nemesis2_extraction.json',{})
N2_ROLE={0:'stage 1',1:'stage 2',2:'stage 3',3:'stage 4',4:'stage 5',5:'stage 6',6:'stage 7',7:'interior 8',8:'secret 9',9:'secret 10',10:'secret 11',11:'return / final'}
for m in n2:
    st=m['stage_id']
    add(id=f'n2.map{st:02d}.terrain',name=f'Nemesis 2 map {st} terrain ({N2_ROLE.get(st,"?")}, {m["columns"]} columns)',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',
        bank=13+(m['column_script_address']-0x4000)//8192-1 if m['column_script_address']>=0x6000 else 13,offset=m['column_script_rom_offset'],category='terrain_map',format='msx_column_script_6',
        size_bytes=m['column_script_bytes'],reuse_class='CONVERT',extracted=True,converted=N2_NATIVE,integrated=N2_NATIVE,tested=N2_NATIVE,path=f'assets/msx/nemesis2/map_{st:02d}/',notes='map ids are not campaign order; see reports/nemesis2_structure.json; native descriptor n2_map_%02d.bin (CP0014)'%st if N2_NATIVE else 'map ids are not campaign order')
    add(id=f'n2.map{st:02d}.tiles',name=f'Nemesis 2 map {st} character set',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',category='tile_set',format='tms9918_pattern+colour',reuse_class='CONVERT',extracted=True,converted=N2_NATIVE,integrated=N2_NATIVE,tested=N2_NATIVE,path=f'assets/msx/nemesis2/map_{st:02d}/source_vram.bin')
    for var in ('normal','drill','penguin','penguin_drill'):
        add(id=f'n2.map{st:02d}.sprites.{var}',name=f'Nemesis 2 map {st} sprite set ({var})',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',category='sprite_set',format='tms9918_16x16',reuse_class='CONVERT',extracted=True,converted=N2_NATIVE and var=='normal',integrated=N2_NATIVE and var=='normal',path=f'assets/msx/nemesis2/map_{st:02d}/sprites_{var}.bin')
    add(id=f'n2.map{st:02d}.script',name=f'Nemesis 2 map {st} stage logic, enemies, boss',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',category='stage_script',format='z80_code',reuse_class='CONVERT',extracted=False,notes='routing only (campaign module); no native gameplay')
for i,s in enumerate(n2s):
    add(id=f'n2.rle.{i:03d}',name='Nemesis 2 compressed graphics stream',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',offset=s['rom_offset'],category='compressed_stream',format='konami_rle2',
        size_bytes=s['compressed_bytes'],content_sha256=s['sha256'],reuse_class='CONVERT',extracted=True)
add(id='n2.tiles.dictionary',name='Nemesis 2 unique indexed 8x8 tiles',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',category='tile_dictionary',format='indexed_8x8',reuse_class='CONVERT',extracted=True,
    path='assets/msx/nemesis2/source_tile_dictionary.bin',notes=f'{n2r.get("unique_source_pixel_tiles")} unique tiles')
for name in ('weapon selection system','player ship variants (drill, penguin)','halfway ending','final ending','opening sequence','bosses (per map)','enemy object types'):
    add(id='n2.'+re.sub(r'[^a-z0-9]+','_',name).strip('_'),name=f'Nemesis 2 {name}',game='nemesis2',platform='msx',rom_slug='nemesis2_msx',category='cutscene' if 'ending' in name or 'opening' in name else 'behavior',
        format='z80_code',reuse_class='CONVERT',extracted=False,notes='identified from disassembly docs; not extracted as data')

# ---------------------------------------------------------------- Salamander / Nemesis 3 (MSX) from their extractors when present
for slug,game,label in (('salamander_msx','salamander','Salamander'),('nemesis3_msx','nemesis3','Nemesis 3')):
    rep=load(f'reports/{game}_extraction.json',{});struct=load(f'reports/{game}_structure.json',{})
    maps=struct.get('maps') or struct.get('stages') or []
    if not maps:
        # identified from campaign docs only
        ids=range(1,8) if game=='salamander' else range(1,12)
        for st in ids:
            add(id=f'{game}.stage{st:02d}',name=f'{label} stage {st} (terrain, graphics, enemies, boss)',game=game,platform='msx',rom_slug=slug,category='stage',format='unknown',reuse_class='UNKNOWN',extracted=False,notes='identified from campaign routing docs; extractor pending')
    else:
        for m in maps:
            mid=m.get('id',m.get('map_id',m.get('stage')));role=m.get('role',m.get('name',''))
            mid=int(re.sub(r'\D','',str(mid)) or 0)
            nat=(game=='nemesis3' and N3_NATIVE)
            add(id=f'{game}.map{mid:02d}.terrain',name=f'{label} map {mid} terrain ({role})',game=game,platform='msx',rom_slug=slug,offset=m.get('column_script_rom_offset'),
                category='terrain_map',format=m.get('format','msx_column_script'),size_bytes=m.get('column_script_bytes'),reuse_class='CONVERT',extracted=bool(rep),converted=nat,integrated=nat,tested=nat,path=f'assets/msx/{game}/map_{mid:02d}/',notes=(m.get('direction','') or '')+(' native descriptor n3_map_%02d.bin (CP0015)'%mid if nat else ''))
            add(id=f'{game}.map{mid:02d}.tiles',name=f'{label} map {mid} character set',game=game,platform='msx',rom_slug=slug,category='tile_set',format='tms9918_pattern+colour',reuse_class='CONVERT',extracted=bool(rep),converted=nat,integrated=nat,tested=nat)
            add(id=f'{game}.map{mid:02d}.sprites',name=f'{label} map {mid} sprite set',game=game,platform='msx',rom_slug=slug,category='sprite_set',format='tms9918_16x16',reuse_class='CONVERT',extracted=bool(rep),converted=nat,integrated=nat)
            add(id=f'{game}.map{mid:02d}.script',name=f'{label} map {mid} stage logic / boss',game=game,platform='msx',rom_slug=slug,category='stage_script',format='z80_code',reuse_class='CONVERT',extracted=False,
                notes='; '.join((b.get('wiki_name') or ('boss %s'%b.get('number',b.get('boss_id')))) if isinstance(b,dict) else str(b) for b in m.get('bosses',[])) if m.get('bosses') else 'bosses UNRESOLVED')
        for i,s in enumerate(load(f'assets/msx/{game}/compressed_streams.json',[]) or []):
            add(id=f'{game}.rle.{i:03d}',name=f'{label} compressed graphics stream',game=game,platform='msx',rom_slug=slug,offset=s.get('rom_offset'),category='compressed_stream',format=s.get('format','konami_rle'),
                size_bytes=s.get('compressed_bytes'),content_sha256=s.get('sha256'),reuse_class='CONVERT',extracted=True)
        for c in struct.get('cutscenes',[]):
            add(id=f'{game}.cutscene.'+re.sub(r'[^a-z0-9]+','_',str(c.get("name",c)).lower()).strip('_'),name=f'{label} cutscene: {c.get("name",c)}',game=game,platform='msx',rom_slug=slug,category='cutscene',format=c.get('format','unknown'),reuse_class='UNKNOWN',extracted=bool(c.get('extracted')))
    # Nemesis 3 extras: sequence pictures, screens, boss graphics sets, interludes.
    if game=='nemesis3':
        pics=load('assets/msx/nemesis3/pictures/pictures.json',{})
        if pics:
            slots=pics.get('pictures',pics.get('slots'))
            n=len(slots) if isinstance(slots,(list,dict)) else int(rep.get('sequence_pictures_rendered',0) or 0)
            for i in range(n):
                add(id=f'nemesis3.picture.{i:03d}',name=f'Nemesis 3 sequence picture {i} (table p27:8F02)',game='nemesis3',platform='msx',rom_slug=slug,category='cutscene_picture',format='msx_packed_picture',reuse_class='CONVERT',extracted=True,path='assets/msx/nemesis3/pictures/')
        for d in sorted((ROOT/'assets/msx/nemesis3/screens').glob('*/')) if (ROOT/'assets/msx/nemesis3/screens').exists() else []:
            add(id=f'nemesis3.screen.{d.name}',name=f'Nemesis 3 screen set {d.name}',game='nemesis3',platform='msx',rom_slug=slug,category='screen',format='tms9918_set',reuse_class='CONVERT',extracted=True,path=str(d.relative_to(ROOT))+'/')
        for i,b in enumerate(load('assets/msx/nemesis3/bosses/boss_sets.json',[]) or []):
            add(id=f'nemesis3.bossset.{i:02d}',name=f'Nemesis 3 boss graphics set {i} (bosses {b.get("boss_numbers")})',game='nemesis3',platform='msx',rom_slug=slug,offset=b.get('rom_offset'),category='boss',format='tms9918_set+z80_code',reuse_class='CONVERT',extracted=True,notes='code '+', '.join(f"{k}:{v.get('address')}" for k,v in (b.get('boss_code_addresses') or {}).items()))
        for it in struct.get('interludes',[]):
            add(id=f'nemesis3.interlude.after{it.get("after_stage")}',name=f'Nemesis 3 interlude after stage {it.get("after_stage")}: {it.get("kind")}',game='nemesis3',platform='msx',rom_slug=slug,category='cutscene',format='z80_code+screens',reuse_class='CONVERT',extracted=False,notes=str(it.get('code','')))
    if game=='salamander':
        for k,b in (struct.get('bosses') or {}).items():
            add(id=f'salamander.boss.{k}',name=f'Salamander boss {k} ({b.get("wiki_name","?")}) {b.get("code_address")}',game='salamander',platform='msx',rom_slug=slug,category='boss',format='z80_code+tiles',reuse_class='CONVERT',extracted=True,notes='tile set extracted; behaviour not ported')
    add(id=f'{game}.campaign_routing',name=f'{label} campaign routing (stage order, secrets, endings)',game=game,platform='msx',rom_slug=slug,category='progression',format='native_6502',reuse_class='CONVERT',
        extracted=True,converted=True,integrated=True,tested=True,path='src/campaign.s',notes='288 native route checks; no gameplay')

# ---------------------------------------------------------------- NES references
nes=load('reports/nes_extraction.json',{});audit=load('reports/source_audit.json',{})
NES_GAMES={'gradius_nes_jp':('Gradius (FC, JP)',3),'gradius_nes_us':('Gradius (NES, US)',3),'gradius2_fc':('Gradius II (FC)',25),'salamander_fc':('Salamander (FC)',73),'lifeforce_nes_us':('Life Force (NES)',2),'lifeforce_nes_us_rev1':('Life Force (NES, rev 1)',2)}
for slug,(label,mapper) in NES_GAMES.items():
    g=(nes.get('games') or {}).get(slug,{})
    regions=g.get('banks') or g.get('regions') or []
    if regions:
        for r in regions:
            rid=('bank_%02d'%int(r['bank'])) if 'region' not in r else ('region_%s'%str(r.get('region')).zfill(2))
            add(id=f'nes.{slug}.{rid}',name=f'{label} graphics {rid} ({r.get("method","chr_rom")}, {r.get("tile_occurrences")} tiles)',game=slug,platform='nes',rom_slug=slug,bank=r.get('bank'),offset=r.get('prg_offset'),category='nes_chr',format='nes_2bpp',
                size_bytes=r.get('decoded_bytes',8192 if 'region' not in r else None),content_sha256=r.get('sha256',r.get('decoded_sha256')),reuse_class='REUSE' if r.get('confidence','high')=='high' else 'UNKNOWN',extracted=True,path=f'assets/nes/{slug}/chr/{rid}.bin',notes=str(r.get('evidence',''))[:120])
    else:
        add(id=f'nes.{slug}.chr',name=f'{label} tile graphics (mapper {mapper})',game=slug,platform='nes',rom_slug=slug,category='nes_chr',format='nes_2bpp',reuse_class='UNKNOWN',extracted=False,notes='extractor pending')
    add(id=f'nes.{slug}.music',name=f'{label} music driver and sequences',game=slug,platform='nes',rom_slug=slug,category='sound_driver',format='nsf_rip',reuse_class='REUSE',
        extracted=any(d.get('path','').startswith('native_nes') and slug.split('_')[0] in d.get('path','') for d in (load('audio/metadata.json',{}) or {}).get('drivers',[])),notes='NSF rip of the original driver where present')
add(id='nes.gradius2_fc.font',name='Gradius II Famicom 8x8 font',game='gradius2_fc',platform='nes',rom_slug='gradius2_fc',category='font',format='nes_2bpp',reuse_class='REUSE',extracted=True,converted=True,integrated=True,tested=True,path='tools/gradius2_font.py')

# ---------------------------------------------------------------- Audio tracks
tl=ROOT/'audio/tracklist.csv'
if tl.exists():
    for row in csv.DictReader(tl.open(encoding='utf-8-sig')):
        drv=row['driver'];game={'nemesis2_msx':'nemesis2','nemesis_msx':'nemesis','salamander_msx':'salamander','gradius2_fc':'gradius2_fc','salamander_fc':'salamander_fc','gradius':'gradius_nes_us'}
        key=next((k for k in game if k in drv),'unknown')
        add(id=f'audio.{key}.{int(row["index"]):02d}',name=f'{row["title"]} ({key} #{row["index"]})',game=game.get(key,key),platform='nes' if row['driver_format']=='NSF' else 'msx',category='music_track',
            format=row['driver_format'],reuse_class='REUSE' if row['driver_format']=='NSF' else 'CONVERT',extracted=True,path=drv,notes=f'command {row["source_command_hex"]}; title {row["title_status"]}')
add(id='audio.nemesis3.driver',name='Nemesis 3 music driver and tracks',game='nemesis3',platform='msx',rom_slug='nemesis3_msx',category='sound_driver',format='unknown',reuse_class='CONVERT',extracted=False,notes='not ripped yet')
add(id='audio.native.apu_driver',name='Native APU driver in the current ROM (donor, SFX only)',game='nemesis_legends',platform='nes',category='sound_driver',format='nes_6502',reuse_class='ADAPT',extracted=True,converted=True,integrated=True,tested=True,path='build/native/audio.bin',notes='no converted music yet')

# ---------------------------------------------------------------- Nemesis Legends original assets
for i,(n,st) in enumerate([('custom title artwork and menu',True),('HUD text panel',True),('cheat menu (Silicon Forge)',False),('inter-game transitions',False),('final ending and credits',False)]):
    add(id='nl.'+re.sub(r'[^a-z0-9]+','_',n).strip('_'),name=f'Nemesis Legends: {n}',game='nemesis_legends',platform='nes',category='new_content',format='nes_native',reuse_class='NEW',extracted=st,converted=st,integrated=st,tested=st,
        notes='provisional' if n.startswith('HUD') else '')

# ---------------------------------------------------------------- Coverage
def agg(rows):
    out=dict(total=len(rows));
    for s in ('identified','extracted','converted','integrated','tested','validated'):out[s]=sum(1 for r in rows if r['states'][s])
    out['pending']=sum(1 for r in rows if not r['states']['integrated'])
    out['reuse']=dict(collections.Counter(r['reuse_class'] for r in rows))
    return out
cov=dict(schema=1,generated_from=['assets/msx/*','reports/*_extraction.json','reports/*_structure.json','reports/nes_extraction.json','audio/tracklist.csv','manifests/content_coverage.json'],
         totals=agg(R),by_game={g:agg([r for r in R if r['game']==g]) for g in sorted({r['game'] for r in R})},
         by_category={c:agg([r for r in R if r['category']==c]) for c in sorted({r['category'] for r in R})},
         unknown_regions=dict(statement='ROM bytes not attributed to an identified resource are not yet computed per game; extraction reports list stream/script byte sums only.',
                              nemesis_rle_bytes=sum(s['compressed_bytes'] for s in n1_streams),nemesis2_rle_bytes=sum(s['compressed_bytes'] for s in n2s)),
         caveats=['Counts are resource records, not bytes, frames or gameplay seconds.','integrated means present in the current native ROM and reachable by its code, not visually or behaviourally validated.','validated requires comparison against the original; none is claimed yet.'])
(ROOT/'manifests/asset_manifest.json').write_text(json.dumps(dict(schema=1,resources=R),indent=1)+'\n')
(ROOT/'manifests/asset_coverage.json').write_text(json.dumps(cov,indent=2)+'\n')
lines=['# Asset coverage (generated by tools/asset_manifest.py; do not edit)','','States are independent. Numbers are resource records.','','| scope | total | extracted | converted | integrated | tested | validated |','|---|---|---|---|---|---|---|']
def row(label,a):return f"| {label} | {a['total']} | {a['extracted']} | {a['converted']} | {a['integrated']} | {a['tested']} | {a['validated']} |"
lines.append(row('**all**',cov['totals']))
for g,a in cov['by_game'].items():lines.append(row(g,a))
lines+=['','| category | total | extracted | converted | integrated | tested | validated |','|---|---|---|---|---|---|---|']
for c,a in cov['by_category'].items():lines.append(row(c,a))
lines+=['','Reuse classes (all): '+', '.join(f'{k} {v}' for k,v in sorted(cov['totals']['reuse'].items())),'']+['- '+c for c in cov['caveats']]
(ROOT/'docs/ASSET_COVERAGE.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(totals=cov['totals'],games={g:(a['total'],a['extracted'],a['integrated']) for g,a in cov['by_game'].items()}),indent=1))
