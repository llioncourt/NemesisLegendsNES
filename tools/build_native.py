#!/usr/bin/env python3
"""Build the current native integration, fail hard on missing tools or assets."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--tools',type=pathlib.Path);p.add_argument('--assets',action='store_true');a=p.parse_args()
    if a.assets:subprocess.run([sys.executable,str(ROOT/'tools/build_native_assets.py')],cwd=ROOT,check=True)
    def tool(name):
        found=str(a.tools/name) if a.tools else shutil.which(name)
        if not found or not pathlib.Path(found).is_file():raise SystemExit(f'Missing {name}; provide --tools DIRECTORY')
        return found
    out=ROOT/'build/native';out.mkdir(parents=True,exist_ok=True)
    names=['native_boot','native_kernel','native_actors','campaign']
    for n in names:subprocess.run([tool('ca65'),'-g','-I','src','src/'+n+'.s','-o',str(out/(n+'.o'))],cwd=ROOT,check=True)
    rom=out/'Nemesis_Legends_CP0004.nes'
    subprocess.run([tool('ld65'),'-C','cfg/native.cfg','-o',str(rom),'-m',str(out/'native.map'),'-Ln',str(out/'native.lbl'),*[str(out/(n+'.o')) for n in names]],cwd=ROOT,check=True)
    data=rom.read_bytes();r=dict(file=rom.name,size=len(data),sha256=hashlib.sha256(data).hexdigest(),mapper=5,
                               status='native integration under development; not the complete four-game campaign')
    (out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
