#!/usr/bin/env python3
"""Reproducible, read-only audit of the supplied MSX/NES ZIP files.
No filename is trusted as an identification. No emulator or game is implied.
Python 3.10+, standard library only. Paths containing spaces are supported.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, io, json, pathlib, re, sys, zipfile, zlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
CANONICAL = {
    'nemesis3_msx': ('fb4f66bcc3eabaf7eea6b91d1e2f5a15aa2f80a31a056af41d948b32646877a9',262144),
    'nemesis_msx': ('3210f8a0f2309dd4b9a89fc2b24d0f178ce4393a0a1f2854fbce545c361261bc',131072),
    'nemesis2_msx': ('227113f94d9900cb48d2f9e88627224dd8cc3d9504614a01e94cf6b23ba508dc',131072),
    'salamander_msx': ('edbbba820ac67d6a55b9dc5da9309e45979936d5620c07d09793efaf077e86b9',131072),
}
N3_SHA1='7393f677e0fae5fc83071c6b74756117b7d75e2d'
NES_NAMES={
 'Gradius (Japan).nes':'gradius_nes_jp','Gradius (USA).nes':'gradius_nes_us',
 'Gradius II (Japan).nes':'gradius2_fc','Salamander (Japan).nes':'salamander_fc',
 'Life Force (USA).nes':'lifeforce_nes_us','Life Force (USA) (Rev 1).nes':'lifeforce_nes_us_rev1'}

def digest(b:bytes)->dict:
    return {'size':len(b),'crc32':f'{zlib.crc32(b)&0xffffffff:08x}',
            'sha1':hashlib.sha1(b).hexdigest(),'sha256':hashlib.sha256(b).hexdigest()}

def parse_ines(b:bytes)->dict:
    if len(b)<16 or b[:4]!=b'NES\x1a': raise ValueError('Not an iNES image')
    nes2=(b[7]&12)==8
    prg=b[4]*16384; chrsize=b[5]*8192
    mapper=(b[6]>>4)|(b[7]&240)
    if nes2:
        if (b[9]&15)==15 or (b[9]>>4)==15: raise ValueError('Exponent-sized NES2 input requires explicit support')
        prg|=(b[9]&15)<<22; chrsize|=(b[9]>>4)<<21
        mapper|=(b[8]&15)<<8
    offset=16+(512 if b[6]&4 else 0)
    if len(b)<offset+prg+chrsize:raise ValueError('Truncated iNES image')
    return dict(mapper=mapper,nes2=nes2,prg_bytes=prg,chr_bytes=chrsize,prg_offset=offset,
                chr_offset=offset+prg,extra_bytes=len(b)-offset-prg-chrsize,
                header_hex=b[:16].hex(),prg_sha256=hashlib.sha256(b[offset:offset+prg]).hexdigest(),
                chr_sha256=hashlib.sha256(b[offset+prg:offset+prg+chrsize]).hexdigest())

def entries(paths):
    for path in paths:
        path=pathlib.Path(path)
        if path.suffix.lower()=='.zip':
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    if info.is_dir() or pathlib.Path(info.filename).suffix.lower() not in ('.nes','.rom','.mx1','.mx2','.bin'):continue
                    if info.file_size>16*1024*1024:raise ValueError('Unexpected ROM over 16 MiB')
                    yield path.name, info.filename, z.read(info)
        elif path.suffix.lower() in ('.nes','.rom','.mx1','.mx2','.bin'):
            yield path.name,path.name,path.read_bytes()

def audit(paths,root=ROOT):
    for d in ['manifests','reports','assets/nes','private_sources','logs']:(root/d).mkdir(parents=True,exist_ok=True)
    rows=[];selected={}; tiles=collections.defaultdict(list); bankgroups=collections.defaultdict(list)
    for archive,name,b in entries(paths):
        r={'archive':archive,'member':name,**digest(b)}
        suffix=pathlib.Path(name).suffix.lower()
        rel='private_sources/'+r['sha256']+suffix
        (root/rel).write_bytes(b); r['path']=rel
        if b[:4]==b'NES\x1a':
            r['platform']='NES'; r.update(parse_ines(b)); slug=NES_NAMES.get(pathlib.Path(name).name)
            if slug:selected[slug]=dict(r,selection='supplied_named_variant_with_recorded_hash')
            prg=b[r['prg_offset']:r['prg_offset']+r['prg_bytes']]
            chrdata=b[r['chr_offset']:r['chr_offset']+r['chr_bytes']]
            folder=root/'assets/nes'/(slug or r['sha256'][:12]);folder.mkdir(exist_ok=True)
            (folder/'prg.bin').write_bytes(prg)
            if chrdata:
                (folder/'chr.bin').write_bytes(chrdata)
                for k in range(0,len(chrdata),16):tiles[chrdata[k:k+16]].append({'source':slug,'tile':k//16})
            r['chr_note']='raw_CHR_ROM_extracted' if chrdata else 'CHR_RAM_graphics_in_PRG_requires_game_decoder'
            raw=prg
        else:
            r['platform']='MSX';raw=b
            for slug,(sha,size) in CANONICAL.items():
                if r['sha256']==sha and len(b)==size:selected[slug]=dict(r,selection='exact_upstream_sha256')
            if r['sha1']==N3_SHA1 and len(b)==262144:
                selected['nemesis3_msx']=dict(r,selection='exact_upstream_sha1_and_verified_sha256')
        if r['platform']=='MSX':
            r['family_hint']='nemesis3' if ('Gofer no Yabou' in name or 'Nemesis 3' in name) else 'nemesis2' if 'Gradius 2' in name else 'nemesis' if 'Gradius -' in name else 'salamander' if 'Salamander -' in name else 'unknown'
            r['repeated_halves']=len(b)%2==0 and b[:len(b)//2]==b[len(b)//2:]
            r['canonical_prefix']=next((slug for slug,(h,n) in CANONICAL.items() if len(b)>n and hashlib.sha256(b[:n]).hexdigest()==h),None)
        for k in range(0,len(raw)-8191,8192):
            bank=raw[k:k+8192];bankgroups[bank].append({'sha256':r['sha256'],'bank':k//8192,'source':name})
        rows.append(r)
    missing=[x for x in ['nemesis_msx','nemesis2_msx','salamander_msx','nemesis3_msx'] if x not in selected]
    data={'schema':1,'inventory_count':len(rows),'unique_roms':len({r['sha256'] for r in rows}),
          'msx_count':sum(r['platform']=='MSX' for r in rows),'nes_count':sum(r['platform']=='NES' for r in rows),
          'msx_family_counts':dict(collections.Counter(r['family_hint'] for r in rows if r['platform']=='MSX')),
          'selected':selected,'missing':missing,'expected_nemesis3_sha1':N3_SHA1,
          'source_total_bytes':sum(r['size'] for r in rows),
          'native_nes_raw_chr_tiles':sum(len(v) for v in tiles.values()),'native_nes_unique_raw_chr_tiles':len(tiles),
          'raw_chr_dictionary_bytes':16*len(tiles),
          'raw_chr_dedup_limit':'Raw pixels only: no palettes, collision or animation equivalence is implied.',
          'banks8k_total':sum(len(v) for v in bankgroups.values()),'banks8k_unique':len(bankgroups)}
    (root/'manifests/input_inventory.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    (root/'manifests/selected_sources.json').write_text(json.dumps(selected,indent=2,ensure_ascii=False),encoding='utf-8')
    (root/'reports/source_audit.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    columns=['archive','member','platform','size','crc32','sha1','sha256','mapper','prg_bytes','chr_bytes','path','repeated_halves','canonical_prefix']
    with (root/'reports/source_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
    duplicate_tiles=[{'sha256':hashlib.sha256(k).hexdigest(),'occurrences':v} for k,v in tiles.items() if len(v)>1]
    (root/'reports/nes_raw_tile_duplicates.json').write_text(json.dumps(duplicate_tiles,indent=2))
    (root/'assets/nes/global_raw_chr_dictionary.bin').write_bytes(b''.join(tiles.keys()))
    print(json.dumps({k:v for k,v in data.items() if k!='selected'},indent=2))
    return data
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('inputs',nargs='+',type=pathlib.Path);p.add_argument('--root',type=pathlib.Path,default=ROOT)
    args=p.parse_args()
    try:audit(args.inputs,args.root)
    except (OSError,ValueError,zipfile.BadZipFile) as e:p.exit(1,str(e)+'\n')
