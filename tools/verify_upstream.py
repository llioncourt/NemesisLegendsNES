#!/usr/bin/env python3
"""Reassemble all four pinned Z80 sources and compare every original byte.
No downloaded script is executed: only explicitly named ASM banks go to Pasmo.
This proves source reproducibility, not that a NES port exists or is complete.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
GAMES = [
    ('nemesis_msx','Nemesis-disassembly','nemesis',16),
    ('nemesis2_msx','Nemesis2-disassembly','nemesis2',16),
    ('salamander_msx','Salamander-disassembly','salamander',16),
    ('nemesis3_msx','Nemesis3-disassembly','nemesis3',32),
]
def sha(data): return hashlib.sha256(data).hexdigest()
def verify(root, pasmo):
    selected = json.loads((root/'manifests/selected_sources.json').read_text())
    acquisition = root/'third_party/ACQUISITION.json'
    acquired = json.loads(acquisition.read_text()) if acquisition.exists() else []
    catalog = json.loads((root/'evidence/source_catalog.json').read_text())['repositories']
    pins = {r['repo']:r['commit'] for r in catalog if r.get('commit')}
    games=[]
    for slug,repo,stem,count in GAMES:
        base=root/'third_party'/('antxiko__'+repo)
        source=selected[slug];original=(root/source['path']).read_bytes()
        if sha(original)!=source['sha256'] or len(original)!=count*8192:
            raise ValueError('Wrong original: '+slug)
        full_repo='antxiko/'+repo
        record=next((r for r in acquired if r['repo']==full_repo),None)
        if record:
            if record['commit']!=pins[full_repo]:raise ValueError('Unexpected source pin')
            for item in record['files']:
                data=(base/item['path']).read_bytes()
                if sha(data)!=item['sha256'] or len(data)!=item['bytes']:
                    raise ValueError('Source snapshot changed: '+item['path'])
        elif (base/'SOURCE_PIN.json').is_file():
            if json.loads((base/'SOURCE_PIN.json').read_text())['commit']!=pins[full_repo]:
                raise ValueError('Unexpected downloaded source pin')
        else:
            raise ValueError('No verified acquisition manifest for '+full_repo)
        output=root/'build/upstream'/slug;output.mkdir(parents=True,exist_ok=True)
        start=time.monotonic();banks=[];rebuilt=bytearray()
        for bank in range(count):
            asm=base/'src'/f'{stem}_p{bank:02d}.asm'
            target=output/f'p{bank:02d}.bin'
            result=subprocess.run([str(pasmo),'--bin',str(asm),str(target)],
                cwd=base,capture_output=True,text=True,timeout=30)
            if result.returncode:
                raise RuntimeError(f'{slug} bank {bank}: {result.stdout}{result.stderr}')
            data=target.read_bytes();expected=original[bank*8192:(bank+1)*8192]
            if data!=expected:raise ValueError(f'Byte mismatch: {slug} bank {bank}')
            banks.append(dict(bank=bank,bytes=len(data),sha256=sha(data),
                source_sha256=sha(asm.read_bytes()),equal=True))
            rebuilt.extend(data)
        (output/'reassembled.rom').write_bytes(rebuilt)
        games.append(dict(source=slug,repository=full_repo,commit=pins[full_repo],
            bytes=len(rebuilt),banks=banks,sha256=sha(rebuilt),
            identical_to_supplied_original=bytes(rebuilt)==original,
            seconds=round(time.monotonic()-start,3),
            method='Pasmo --bin each source bank; exact byte comparison; concatenation',
            game_port_complete=False))
        print(slug,count,'banks:',len(rebuilt),'bytes identical',flush=True)
    report=dict(all_identical=True,total_banks=sum(len(g['banks'])for g in games),
                total_bytes=sum(g['bytes']for g in games),games=games)
    (root/'reports').mkdir(exist_ok=True)
    (root/'reports/upstream_reassembly.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=pathlib.Path,default=ROOT)
    p.add_argument('--pasmo',default=shutil.which('pasmo'))
    a=p.parse_args()
    if not a.pasmo:p.error('Pass --pasmo or install Pasmo on PATH')
    verify(a.root,pathlib.Path(a.pasmo))
