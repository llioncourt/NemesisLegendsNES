#!/usr/bin/env python3
"""Local entry point for the lean CP0008 package. No automatic downloads."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, platform, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]

def check_files(root: pathlib.Path, manifest: pathlib.Path) -> int:
    data=json.loads(manifest.read_text(encoding='utf-8'))
    seen=set()
    for row in data['files']:
        path=pathlib.PurePosixPath(row['path'])
        if path.is_absolute() or '..' in path.parts or row['path'] in seen:
            raise ValueError('Unsafe or repeated manifest path: '+row['path'])
        seen.add(row['path']);target=root.joinpath(*path.parts)
        if target.is_symlink() or not target.is_file():
            raise ValueError('Missing or nonregular file: '+row['path'])
        raw=target.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Integrity mismatch: '+row['path'])
    return len(seen)

def tool_dir(explicit: pathlib.Path | None) -> pathlib.Path:
    if explicit:return explicit.resolve()
    bundled=ROOT/'toolchain/linux-x64/bin'
    if platform.system()=='Linux' and platform.machine() in ('x86_64','AMD64'):
        if (bundled/'ca65').is_file():return bundled
    found=shutil.which('ca65')
    if found:return pathlib.Path(found).resolve().parent
    raise ValueError('ca65/ld65 not found. Pass --tools with platform-native executables.')

def run(script: str, *args: object) -> None:
    subprocess.run([sys.executable,str(ROOT/'tools'/script),*map(str,args)],cwd=ROOT,check=True)

def rom_check(profile: dict) -> None:
    raw=(ROOT/profile['rom']).read_bytes()
    if len(raw)!=profile['rom_bytes'] or hashlib.sha256(raw).hexdigest()!=profile['rom_sha256']:
        raise ValueError('The built ROM differs from the current checkpoint baseline')
    print('ROM byte identity: PASS',profile['rom_sha256'],flush=True)

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=('verify','build','test','sources'))
    ap.add_argument('--tools',type=pathlib.Path)
    ap.add_argument('--core',type=pathlib.Path)
    ap.add_argument('--assets',action='store_true',help='Regenerate native assets from selected originals')
    a=ap.parse_args()
    profile=json.loads((ROOT/'manifests/checkpoint.json').read_text())
    if a.action=='verify':
        count=check_files(ROOT,ROOT/'CHECKPOINT_FILES.json')
        from verify_selected_inputs import verify
        report=verify();rom_check(profile)
        print('Package integrity: PASS,',count,'files;',report['inventory_count'],'selected originals')
        return 0
    tools=tool_dir(a.tools)
    suffix='.exe' if os.name=='nt' else ''
    for name in ('ca65','ld65'):
        path=tools/(name+suffix)
        if not path.is_file():raise ValueError('Missing assembler/linker: '+str(path))
        if os.name!='nt' and not os.access(path,os.X_OK):path.chmod(path.stat().st_mode|0o100)
    if a.action=='sources':
        pasmo=tools/('pasmo'+suffix)
        if not pasmo.is_file():raise ValueError('Missing Pasmo: '+str(pasmo))
        if os.name!='nt' and not os.access(pasmo,os.X_OK):pasmo.chmod(pasmo.stat().st_mode|0o100)
        run('verify_upstream.py','--pasmo',pasmo)
        return 0
    run('verify_selected_inputs.py')
    run('build_native.py','--tools',tools,*(['--assets'] if a.assets else []))
    rom_check(profile)
    if a.action=='build':return 0
    core=a.core.resolve() if a.core else tools/'fceumm_libretro.so'
    if not core.is_file():raise ValueError('Pass --core with a platform-native FCEUmm library')
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],cwd=ROOT,check=True)
    run('test_campaign_native.py','--core',core,'--tool-dir',tools)
    run('test_combat_native.py','--core',core,'--tools',tools)
    run('test_native_integration.py','--core',core)
    run('test_stage_one.py','--core',core)
    run('test_stage_two.py','--core',core)
    run('test_pacing_native.py','--core',core)
    run('test_vblank_budget.py')
    run('test_title_native.py','--core',core)
    rom_check(profile)
    print('Scoped CP0009 tests passed. Not a complete-game or hardware certification.')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('ERROR:',exc,file=sys.stderr);raise SystemExit(1)
