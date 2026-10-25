#!/usr/bin/env python3
"""Rebuild the audited CP0001 source assets; this is not a game-ROM builder.
Use --render-audio to generate the optional 98 reference MP3s. Source archives
are never modified. Rebuilding derived assets does not reset progress ledgers.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,subprocess,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(name,*args):
    subprocess.run([sys.executable,str(ROOT/'tools'/name),*map(str,args)],cwd=ROOT,check=True)
def input_reports(archives):
    rows=[]
    for path in archives:
        data=path.read_bytes()
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:raise ValueError('Corrupt archive: '+path.name)
        rows.append(dict(name=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (ROOT/'manifests/input_archives.json').write_text(json.dumps(rows,indent=2)+'\n')
    selected=json.loads((ROOT/'manifests/selected_sources.json').read_text())
    source=selected['nemesis3_msx'];canonical=(ROOT/source['path']).read_bytes()
    inventory=json.loads((ROOT/'manifests/input_inventory.json').read_text())
    variants=[]
    for item in inventory:
        if item['archive']!=source['archive']:continue
        data=(ROOT/item['path']).read_bytes();n=min(len(data),len(canonical))
        variants.append(dict(member=item['member'],sha256=item['sha256'],size=len(data),
            selected_canonical=item['sha256']==source['sha256'],
            differing_bytes_in_common_prefix=sum(a!=b for a,b in zip(data[:n],canonical[:n])),
            size_delta_from_canonical=len(data)-len(canonical)))
    report=dict(status='all_four_msx_source_images_verified',archive_integrity='PASS',
        upload_archive=source['archive'],selected_rom=source,rom_entries_in_upload=len(variants),
        variant_comparisons=variants,nemesis3_gameplay_ported=False,nemesis3_audio_ripped=False,
        scope='Input identity and modified-variant comparison only; not implementation status.')
    (ROOT/'reports/nemesis3_input_validation.json').write_text(json.dumps(report,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--render-audio',action='store_true');a=p.parse_args()
    archives=sorted((ROOT/'inputs').glob('*.zip'))
    if not archives:p.error('Place the eight original supplied ZIPs in inputs/. Do not rename the project directory.')
    run('source_audit.py',*archives);input_reports(archives)
    for tool in ['extract_nemesis_msx.py','extract_nemesis2_msx.py','rip_gradius_nsf.py',
                 'rip_konami_nsf.py','rip_msx_kss.py','name_audio.py','create_title_asset.py']:
        run(tool)
    if a.render_audio:run('render_audio.py','--limit','0')
    run('finalize_evidence.py')
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_evidence.py','-v'],cwd=ROOT,check=True)
    if a.render_audio:run('validate_audio_files.py')
    print('Source evidence rebuilt. No complete Nemesis Legends game ROM is produced by this command.')
if __name__=='__main__':main()
