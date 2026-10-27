#!/usr/bin/env python3
"""Rebuild derived resource/audio manifests without resetting project progress.
The source catalogue, campaign contract and content-coverage ledger are reviewed
project state. This generator deliberately does NOT overwrite those documents.
"""
from __future__ import annotations
import csv,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def js(path,data):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def main():
    unique={};count=0
    for slug,filename in [('nemesis','source_indexed_tile_dictionary.bin'),('nemesis2','source_tile_dictionary.bin')]:
        data=(ROOT/'assets/msx'/slug/filename).read_bytes()
        if len(data)%64:raise ValueError('Malformed source tile dictionary')
        for offset in range(0,len(data),64):
            unique.setdefault(data[offset:offset+64],[]).append(dict(game=slug,local_index=offset//64));count+=1
    (ROOT/'assets/msx/global_source_indexed_tiles.bin').write_bytes(b''.join(unique))
    js('assets/msx/global_source_indexed_tile_refs.json',[
        dict(index=i,sha256=hashlib.sha256(tile).hexdigest(),references=refs)
        for i,(tile,refs) in enumerate(unique.items())])
    js('reports/global_dedup.json',dict(domain='Decoded MSX indexed 8x8 pixels; palette indices preserved',
        input_tiles=count,unique_tiles=len(unique),duplicate_tiles=count-len(unique),
        bytes_per_source_tile=64,unique_bytes=len(unique)*64,nes_conversion=False,
        semantic_equivalence='Exact pixels only; collision, timing and events remain separate.'))
    tracks=[]
    for p in sorted((ROOT/'audio').glob('*/*/mp3/*.json')):
        row=json.loads(p.read_text());driver=ROOT/row['driver'];mp3=ROOT/row['mp3']
        if not driver.is_file() or not mp3.is_file():raise ValueError('Stale audio metadata: '+str(p))
        if hashlib.sha256(mp3.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('MP3 changed since rendering: '+str(mp3))
        row['driver_sha256']=hashlib.sha256(driver.read_bytes()).hexdigest()
        row['native_nes_source']=row['driver_format']=='NSF'
        p.write_text(json.dumps(row,indent=2)+'\n');tracks.append(row)
    tracks.sort(key=lambda r:(r['driver'],r['index']))
    drivers=[]
    for p in sorted(list((ROOT/'audio').glob('*/*/*.nsf'))+list((ROOT/'audio').glob('*/*/*.kss'))):
        data=p.read_bytes();drivers.append(dict(path=str(p.relative_to(ROOT/'audio')),
            format=p.suffix[1:].upper(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    reference_tracks=[]
    for entry in drivers:
        index_path=ROOT/'audio'/pathlib.Path(entry['path']).parent/'tracks.json'
        for row in json.loads(index_path.read_text())['tracks']:
            reference_tracks.append(dict(row,driver='audio/'+entry['path'],driver_format=entry['format']))
    native=sum(r['driver_format']=='NSF'for r in tracks)
    msx=sum(r['driver_format']=='KSS'for r in tracks)
    duration=sum(r['rendered_seconds']for r in tracks)
    js('audio/metadata.json',dict(album='Nemesis Legends - Source Music Evidence',
        complete_project_soundtrack=False,msx_to_nes_conversion_complete=False,
        missing_game='Nemesis 3',tracks=tracks,drivers=drivers,track_count=len(tracks),
        native_nes_sequences=native,msx_reference_sequences=msx,duration_seconds=duration,
        driver_track_count=len(reference_tracks),mp3_included=bool(tracks),
        native_nes_driver_sequences=sum(t['driver_format']=='NSF' for t in reference_tracks),
        msx_reference_driver_sequences=sum(t['driver_format']=='KSS' for t in reference_tracks)))
    columns=['driver','index','source_command_hex','title','title_status',
             'command_mapping_status','driver_format','rendered_seconds','bytes','sha256','mp3']
    with (ROOT/'audio/tracklist.csv').open('w',newline='',encoding='utf-8-sig')as f:
        writer=csv.DictWriter(f,columns,extrasaction='ignore');writer.writeheader();writer.writerows(tracks if tracks else reference_tracks)
    for folder in sorted({(ROOT/r['mp3']).parent for r in tracks}):
        rows=[r for r in tracks if (ROOT/r['mp3']).parent==folder]
        (folder.parent/'listen.m3u8').write_text('#EXTM3U\n'+''.join(
            '#EXTINF:%d,%s\nmp3/%s\n'%(round(r['rendered_seconds']),r['title'],pathlib.Path(r['mp3']).name)for r in rows))
    if tracks:(ROOT/'audio/listen_all.m3u8').write_text('#EXTM3U\n'+''.join(
        '#EXTINF:%d,%s - %s\n%s\n'%(round(r['rendered_seconds']),pathlib.Path(r['driver']).parent.name,
            r['title'],str(pathlib.Path(r['mp3']).relative_to('audio')))for r in tracks))
    if not tracks:
        for playlist in (ROOT/'audio').rglob('*.m3u8'):playlist.unlink()
    prompt=(ROOT/'audio/SUNO_STYLE.txt').read_text().strip()
    if not 0<len(prompt)<=1000:raise ValueError('Suno prompt outside 1..1000 characters')
    js('audio/suno_prompt_metadata.json',dict(characters=len(prompt),maximum=1000,language='English'))
    js('reports/audio_summary.json',dict(rendered=len(tracks),driver_files=len(drivers),
        mp3_bytes=sum(r['bytes']for r in tracks),duration_seconds=duration,
        warnings=sum(bool(r['warnings'])for r in tracks),
        pcm_clipping_metrics_missing=sum(r['source_clipped_samples']is None for r in tracks),
        tracks_with_observed_pcm_clipping=sum(bool(r['source_clipped_samples'])for r in tracks),
        silence_check='Rendered source references only; not console parity or arrangement validation.',
        native_nes_sequences=native,msx_reference_sequences=msx))
    print('Derived evidence rebuilt:',count,'tiles ->',len(unique),'unique;',len(tracks),'MP3s.')
if __name__=='__main__':main()
