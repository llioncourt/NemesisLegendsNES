#!/usr/bin/env python3
"""Build the current native integration, fail hard on missing tools or assets."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--tools',type=pathlib.Path);p.add_argument('--assets',action='store_true');a=p.parse_args()
    # Recompile the high-resolution approved art BEFORE the full graphics bank
    # generator, which embeds its background.chr in banks 19..22. Otherwise an
    # --assets rebuild could silently restore the previously blacked-out title.
    if a.assets:
        subprocess.run([sys.executable,str(ROOT/'tools/compile_title_art.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/build_n2_assets.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/build_n3_assets.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/build_native_assets.py')],cwd=ROOT,check=True)
    import hashlib
    bg=(ROOT/'assets/title_art/background.chr').read_bytes()
    full=(ROOT/'build/native/graphics.chr').read_bytes()
    if len(bg)!=16384 or len(full)!=262144 or full[19*4096:23*4096]!=bg:
        raise SystemExit('Title background CHR bank mismatch; run --assets to regenerate the approved art')
    subprocess.run([sys.executable,str(ROOT/'tools/build_title_panel.py')],cwd=ROOT,check=True)
    def tool(name):
        found=str(a.tools/(name+('.exe' if os.name=='nt' else ''))) if a.tools else shutil.which(name)
        if not found or not pathlib.Path(found).is_file():raise SystemExit(f'Missing {name}; provide --tools DIRECTORY')
        return found
    out=ROOT/'build/native';out.mkdir(parents=True,exist_ok=True)
    names=['native_boot','native_title','native_kernel','native_actors','native_projectiles','native_boss','native_laser','campaign','native_stage2','native_pacing','native_stage3','native_stage_targets','native_stage4','native_cheat']
    for n in names:subprocess.run([tool('ca65'),'-g','-I','src','src/'+n+'.s','-o',str(out/(n+'.o'))],cwd=ROOT,check=True)
    rom=out/'Nemesis_Legends_CP0015.nes'
    subprocess.run([tool('ld65'),'-C','cfg/native.cfg','-o',str(rom),'-m',str(out/'native.map'),'-Ln',str(out/'native.lbl'),*[str(out/(n+'.o')) for n in names]],cwd=ROOT,check=True)
    data=rom.read_bytes();r=dict(file=rom.name,size=len(data),sha256=hashlib.sha256(data).hexdigest(),mapper=5,
                               status='native integration under development; not the complete four-game campaign')
    (out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
