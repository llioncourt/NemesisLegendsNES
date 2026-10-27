#!/usr/bin/env python3
"""MSX x NES graphics correspondence matrix (Frente C).

Compares the decoded MSX source graphics (indexed 8x8 tiles and 16x16 sprite
frames from assets/msx/<game>/) against the NES reference tile dictionary
(assets/nes/nes_tile_dictionary.bin from tools/extract_nes_graphics.py).
Formats differ (TMS9918 colour per row vs NES 2bpp), so the comparison is on
shape: binarised masks, exact and flipped, with Hamming distance. Distance 0
means identical silhouette (REUSE candidate), <= LOOSE means close (ADAPT
candidate), otherwise CONVERT. This is a candidate list for human review, not a
decision, and it says nothing about animation, collision or timing parity.
Writes reports/msx_nes_matrix.json and docs/MSX_NES_MATRIX.md.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib,sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOOSE=6
def nes_tiles():
    p=ROOT/'assets/nes/nes_tile_dictionary.bin'
    if not p.exists():return None,None
    raw=p.read_bytes();n=len(raw)//16;arr=np.frombuffer(raw,dtype=np.uint8).reshape(n,16)
    lo=np.unpackbits(arr[:,:8],axis=1).reshape(n,8,8);hi=np.unpackbits(arr[:,8:],axis=1).reshape(n,8,8)
    refs=json.loads((ROOT/'assets/nes/nes_tile_references.json').read_text()) if (ROOT/'assets/nes/nes_tile_references.json').exists() else {}
    shas=[hashlib.sha256(raw[i*16:(i+1)*16]).hexdigest() for i in range(n)]
    byindex=[(refs.get(h) or [])[:3] for h in shas]
    return ((lo|hi)>0).astype(np.uint8),byindex
def mask_key(m):return np.packbits(m.reshape(-1)).tobytes()
def variants(m):
    yield 'id',m;yield 'h',m[:,::-1];yield 'v',m[::-1,:];yield 'hv',m[::-1,::-1]
def index_masks(masks):
    idx={}
    for i,m in enumerate(masks):idx.setdefault(mask_key(m),i)
    return idx
def msx_tiles(game):
    p=ROOT/f'assets/msx/{game}/source_tile_dictionary.bin'
    if not p.exists():p=ROOT/f'assets/msx/{game}/source_indexed_tile_dictionary.bin'
    if not p.exists():return None
    raw=np.frombuffer(p.read_bytes(),dtype=np.uint8);n=len(raw)//64
    return (raw.reshape(n,8,8)>0).astype(np.uint8)
def msx_sprites(game):
    out=[]
    for folder in sorted((ROOT/f'assets/msx/{game}').glob('*/')):
        for f in sorted(folder.glob('sprites*.bin'))+sorted(folder.glob('source_vram.bin')):
            data=f.read_bytes()
            if f.name=='source_vram.bin':data=data[0x1800:0x2000]
            for k in range(len(data)//32):
                blk=data[k*32:(k+1)*32];m=np.zeros((16,16),dtype=np.uint8)
                for side in (0,1):
                    col=np.unpackbits(np.frombuffer(blk[side*16:(side+1)*16],dtype=np.uint8)).reshape(16,8);m[:,side*8:(side+1)*8]=col
                if m.any():out.append((f'{folder.name}/{f.name}#{k}',m))
    seen={};uniq=[]
    for name,m in out:
        key=mask_key(m)
        if key not in seen:seen[key]=name;uniq.append((name,m))
    return uniq
def best_hamming(target,pool):
    d=(pool!=target[None]).reshape(len(pool),-1).sum(1);i=int(d.argmin());return int(d[i]),i
def main():
    nes,refs=nes_tiles()
    report=dict(schema=1,nes_dictionary_tiles=None if nes is None else int(len(nes)),loose_threshold=LOOSE,games={},
                method='binarised shape match (exact, flips, Hamming) on 8x8 tiles and 16x16 sprites; colour, animation, collision and timing are not compared')
    if nes is None:
        report['status']='NES dictionary missing: run tools/extract_nes_graphics.py first';write(report);return
    nes_idx=index_masks(nes)
    # 16x16 NES candidates: consecutive quads (8x16 pairs) in dictionary order are not meaningful across games, so sprites compare per 8x8 quadrant.
    for game in ('nemesis','nemesis2','salamander','nemesis3'):
        tiles=msx_tiles(game)
        if tiles is None:continue
        exact=flip=loose=0;per=[]
        for i,t in enumerate(tiles):
            if not t.any():continue
            hit=None
            for kind,v in variants(t):
                j=nes_idx.get(mask_key(v))
                if j is not None:hit=(kind,j,0);break
            if hit is None:
                d,j=best_hamming(t,nes);hit=('hamming',j,d)
            kind,j,d=hit
            if d==0 and kind=='id':exact+=1
            elif d==0:flip+=1
            elif d<=LOOSE:loose+=1
            per.append(dict(msx_tile=i,match=kind,nes_tile=j,distance=d,nes_refs=(refs[j] if refs and j<len(refs) else None)))
        sprites=msx_sprites(game);sp_exact=sp_loose=0;sp_rows=[]
        for name,m in sprites:
            quads=[m[0:8,0:8],m[0:8,8:16],m[8:16,0:8],m[8:16,8:16]];dist=0;ids=[]
            for q in quads:
                if not q.any():ids.append(None);continue
                j=nes_idx.get(mask_key(q))
                if j is None:d,j=best_hamming(q,nes);dist+=d
                ids.append(j)
            if dist==0:sp_exact+=1
            elif dist<=LOOSE:sp_loose+=1
            sp_rows.append(dict(frame=name,nes_quadrants=ids,distance=dist))
        n=sum(1 for t in tiles if t.any())
        report['games'][game]=dict(msx_tiles=n,tiles_exact=exact,tiles_flipped=flip,tiles_loose=loose,tiles_convert=n-exact-flip-loose,
                                   sprites=len(sprites),sprites_exact=sp_exact,sprites_loose=sp_loose,sprites_convert=len(sprites)-sp_exact-sp_loose,
                                   tile_matches=per,sprite_matches=sp_rows)
    write(report)
def write(report):
    (ROOT/'reports/msx_nes_matrix.json').write_text(json.dumps(report)+'\n')
    lines=['# MSX x NES correspondence matrix (generated by tools/compare_msx_nes.py; do not edit)','',report.get('status',report['method']),'']
    if report['games']:
        lines+=['| game | MSX tiles | exact | flipped | close | convert | sprites | exact | close | convert |','|---|---|---|---|---|---|---|---|---|---|']
        for g,a in report['games'].items():
            lines.append(f"| {g} | {a['msx_tiles']} | {a['tiles_exact']} | {a['tiles_flipped']} | {a['tiles_loose']} | {a['tiles_convert']} | {a['sprites']} | {a['sprites_exact']} | {a['sprites_loose']} | {a['sprites_convert']} |")
        lines+=['','Decision rule for the manifest: exact or flipped silhouette -> REUSE candidate (verify colour/animation by eye); close -> ADAPT candidate; otherwise CONVERT. Nemesis 3 has no NES counterpart, so its matches are coincidental shapes only.']
    (ROOT/'docs/MSX_NES_MATRIX.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({g:{k:v for k,v in a.items() if not k.endswith('_matches')} for g,a in report['games'].items()} or report.get('status'),indent=1))
if __name__=='__main__':main()
