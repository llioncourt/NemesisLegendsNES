#!/usr/bin/env python3
"""Whole-game memory budget (Frente E): measured current usage from the linker
map and asset report, plus a projection for the four-game campaign from the
extraction inventories. Projections are arithmetic on extracted data sizes, not
proof of fit. Writes reports/budget.json and docs/BUDGET.md.
"""
from __future__ import annotations
import json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p,d=None):
    p=ROOT/p;return json.loads(p.read_text()) if p.exists() else d
segs={}
m=(ROOT/'build/native/native.map').read_text()
for line in m.split('Segment list:')[1].split('Exports list')[0].splitlines():
    r=re.match(r'^(\w+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})',line)
    if r:segs[r.group(1)]=dict(start=int(r.group(2),16),end=int(r.group(3),16),size=int(r.group(4),16))
cfg=(ROOT/'cfg/native.cfg').read_text()
mem={}
for r in re.finditer(r'^\s*(\w+):\s*start=\$([0-9a-f]+),size=\$([0-9a-f]+)',cfg,re.M):mem[r.group(1)]=dict(start=int(r.group(2),16),size=int(r.group(3),16))
prg_banks=dict(P0_P5_stage_descriptors=6*8192,P6_maps=8192,P7_actors=8192,P8_bossdata=8192,P9_title=8192,RES_reserved=mem['RES']['size'],K_kernel=8192,fixed_E000=8192)
prg_total=sum(prg_banks.values());assert prg_total==128*1024,prg_total
used=dict(STAGE_descriptors=6*8192,MAPS=segs['MAPS']['size'],ACTORS=segs['ACTORS']['size'],BOSSDATA=segs['BOSSDATA']['size'],TITLE=segs['TITLE']['size'],
          CODE=segs['CODE']['size']+segs['RODATA']['size'],BOOT=segs['BOOT']['size'],SOUND=segs['SOUND']['size'],VECTORS=6,RESERVED=segs.get('RESERVED',{}).get('size',0))
assets=load('build/native/assets_report.json',{})
ram=dict(zero_page_bytes=0x80,bss_bytes=segs['BSS']['size'],stack_oam_pages=0x300,qa_mirror_bytes=0x50,work_ram_8k_used=dict(objects=17*32,shots=9*16,enemy_shots=10*16,history=128,boss_queue=0x200,collision_ring=0x400,actor_globals=0x100))
# ---- projections from extraction inventories (bytes as NES-side representations)
def tiles_2bpp(n):return n*16
n1=load('reports/nemesis_extraction.json',{});n2=load('reports/nemesis2_extraction.json',{});sal=load('reports/salamander_extraction.json',{});n3=load('reports/nemesis3_extraction.json',{})
n2m=load('assets/msx/nemesis2/stage_manifest.json',[]);n1m=load('assets/msx/nemesis/stage_manifest.json',[])
proj={}
proj['nemesis']=dict(terrain_scripts=sum(s.get('script_bytes',0) for s in n1m),metatiles=0x97de-0x8000,unique_tiles=n1.get('unique_pixel_tiles'),tiles_2bpp_upper_bound=tiles_2bpp(n1.get('unique_pixel_tiles',0)),
                     sprite_sheets=12*8192,sprite_sheets_dedup_1k_banks=assets.get('sprite_unique_1k_banks'),measured_chr_useful=assets.get('chr_useful_bytes'),stage_logic_code_estimate=12*1536,note='measured: current ROM holds all 12 descriptors and CHR for Nemesis')
proj['nemesis2']=dict(terrain_scripts=sum(s.get('column_script_bytes',0) for s in n2m),metatile_tables='per map, 16/8-byte blocks (not summed)',unique_tiles=n2.get('unique_source_pixel_tiles'),
                      tiles_2bpp_upper_bound=tiles_2bpp(n2.get('unique_source_pixel_tiles',0)),sprite_sets=n2.get('sprite_sets'),sprite_sets_bytes=(n2.get('sprite_sets') or 0)*2048,stage_logic_code_estimate=12*2048,note='static data extracted; no code ported')
for game,rep in (('salamander',sal),('nemesis3',n3)):
    proj[game]=dict(unique_tiles=rep.get('unique_source_pixel_tiles',rep.get('unique_pixel_tiles')),tiles_2bpp_upper_bound=tiles_2bpp(rep.get('unique_source_pixel_tiles',rep.get('unique_pixel_tiles',0)) or 0),
                    terrain_columns=rep.get('terrain_columns'),sprite_sets=rep.get('sprite_sets'),note='from extractor report' if rep else 'extractor pending')
chr_upper=sum(v.get('tiles_2bpp_upper_bound',0) or 0 for v in proj.values())+sum((v.get('sprite_sets_bytes') or v.get('sprite_sheets') or 0) for v in proj.values())
summary=dict(current_board=dict(mapper=5,prg_kib=128,chr_kib=128,wram_kib=8,prg_used_bytes=sum(used.values()),prg_free_bytes=prg_total-sum(used.values()),chr_used_bytes=assets.get('chr_useful_bytes'),chr_padding_bytes=assets.get('chr_allocated_bytes',0)-(assets.get('chr_useful_bytes') or 0)),
             mmc5_ceiling=dict(prg_kib=1024,chr_kib=1024,exram_bytes=1024,wram_kib=64),
             four_game_chr_upper_bound_bytes=chr_upper,four_game_chr_upper_bound_kib=round(chr_upper/1024),
             reading='Upper bound counts every unique MSX tile as one 2bpp NES tile and every sprite set uncompressed; global deduplication (reports/global_dedup.json) and palette merging reduce it. Code, music, cutscenes and tables are not in this bound.',
             decision_points=['CHR-ROM (current) vs CHR-RAM with compressed CHR in PRG: CHR-RAM frees PRG banks for graphics and allows compression; CHR-ROM keeps zero-cost bank switching.','PRG must grow beyond 128 KiB for chapters 2-4; 512 KiB PRG is the working assumption, 1 MiB the ceiling.'])
out=dict(schema=1,segments=segs,prg_bank_roles=prg_banks,prg_used=used,ram=ram,projection=proj,summary=summary)
(ROOT/'reports/budget.json').write_text(json.dumps(out,indent=1)+'\n')
L=['# Memory budget (generated by tools/budget.py; do not edit)','','## Current ROM (MMC5, 128 KiB PRG, 128 KiB CHR)','','| segment | bytes |','|---|---|']+[f'| {k} | {v} |' for k,v in used.items()]
L+=['',f"PRG used {summary['current_board']['prg_used_bytes']} of {prg_total}; CHR useful {summary['current_board']['chr_used_bytes']} (padding {summary['current_board']['chr_padding_bytes']}).",'','## Four-game projection (upper bounds from extraction)','','| game | unique MSX tiles | 2bpp upper bound | sprite bytes | note |','|---|---|---|---|---|']
for g,v in proj.items():L.append(f"| {g} | {v.get('unique_tiles')} | {v.get('tiles_2bpp_upper_bound')} | {v.get('sprite_sets_bytes') or v.get('sprite_sheets') or ''} | {v.get('note','')} |")
L+=['',f"CHR upper bound for all four games: {summary['four_game_chr_upper_bound_kib']} KiB before deduplication.",'',summary['reading'],'']+['- '+d for d in summary['decision_points']]
(ROOT/'docs/BUDGET.md').write_text('\n'.join(L)+'\n');print(json.dumps(summary,indent=1))
