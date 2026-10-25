#!/usr/bin/env python3
"""Render extracted NSF/KSS drivers to named MP3 with QA metadata.
Requires Python 3.10+, numpy, libgme and ffmpeg. No web access.
MP3s are listening renders, not sequence data or automatic NES conversions.
"""
from __future__ import annotations
import argparse,concurrent.futures,ctypes as C,ctypes.util,hashlib,json,pathlib,re,shutil,subprocess,tempfile,wave
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
def lib():
 name=ctypes.util.find_library('gme')
 if not name:raise RuntimeError('libgme not found. Install libgme or place gme.dll on PATH.')
 x=C.CDLL(name)
 for name,args,res in [('gme_open_file',[C.c_char_p,C.POINTER(C.c_void_p),C.c_int],C.c_char_p),('gme_start_track',[C.c_void_p,C.c_int],C.c_char_p),('gme_play',[C.c_void_p,C.c_int,C.POINTER(C.c_short)],C.c_char_p),('gme_warning',[C.c_void_p],C.c_char_p),('gme_delete',[C.c_void_p],None),('gme_ignore_silence',[C.c_void_p,C.c_int],None)]:
  f=getattr(x,name);f.argtypes=args;f.restype=res
 return x

def check(err):
 if err:raise RuntimeError(err.decode(errors='replace'))
def slug(s):return re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',s).strip(' .')[:160]
def render(task):
 p,t,seconds,rate=task;p=pathlib.Path(p);x=lib();e=C.c_void_p();warnings=[];blocks=[]
 try:
  check(x.gme_open_file(str(p).encode(),C.byref(e),rate));x.gme_ignore_silence(e,1);check(x.gme_start_track(e,t['index']))
  for _ in range(seconds):
   b=(C.c_short*(2*rate))();check(x.gme_play(e,2*rate,b));blocks.append(np.ctypeslib.as_array(b).copy().reshape(-1,2))
   w=x.gme_warning(e)
   if w and w.decode(errors='replace') not in warnings:warnings.append(w.decode(errors='replace'))
 finally:
  if e:x.gme_delete(e)
 a=np.concatenate(blocks);peak=int(np.max(np.abs(a.astype(np.int32))));rms=float(np.sqrt(np.mean(a.astype(np.float64)**2)));clipped=int(np.sum((a==32767)|(a==-32768)))
 activity=np.flatnonzero(np.max(np.abs(a.astype(np.int32)),axis=1)>8)
 if len(activity)==0 or rms<1:raise RuntimeError('Silent source command %02X in %s'%(t['command'],p))
 natural_end=int(activity[-1])+1
 terminal_quiet=(len(a)-natural_end)/rate
 if terminal_quiet>=3:
  a=a[:min(len(a),natural_end+rate)];fade=0.0;end_policy='terminal_quiet_trim_plus_1_second'
 else:
  fade=min(5.0,len(a)/rate/5);n=round(fade*rate);a=a.astype(np.float64);a[-n:]*=np.linspace(1,0,n)[:,None];end_policy='fixed_capture_with_5_second_fade_loop_count_unverified'
 gain=min(0.85,26000/max(1,peak));a=np.rint(a.astype(np.float64)*gain).astype('<i2')
 out=p.parent/'mp3';out.mkdir(exist_ok=True);target=out/('%02d - %s.mp3'%(t['index']+1,slug(t['title'])))
 with tempfile.TemporaryDirectory(prefix='nemesis_audio_') as tmp:
  wav=pathlib.Path(tmp)/'render.wav'
  with wave.open(str(wav),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(a.tobytes())
  result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wav),'-codec:a','libmp3lame','-b:a','192k','-metadata','title='+t['title'],'-metadata','artist=Konami','-metadata','album=Nemesis Legends - '+p.parent.name+' - Source Reference','-metadata','track='+str(t['index']+1),'-metadata','comment=Private source-ROM extraction. Not a completed Nemesis Legends soundtrack conversion.',str(target)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 info=dict(t,driver=str(p.relative_to(ROOT)),mp3=str(target.relative_to(ROOT)),driver_format=p.suffix[1:].upper(),sample_rate=rate,channels=2,rendered_seconds=len(a)/rate,tested_seconds=seconds,fade_seconds=fade,end_policy=end_policy,source_pcm_peak=peak,source_pcm_rms=round(rms,4),source_clipped_samples=clipped,output_gain=gain,warnings=warnings,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='rendered_source_reference',nes_conversion=False)
 target.with_suffix('.json').write_text(json.dumps(info,indent=2)+'\n')
 print('%s %02d %6.2fs %s'%(p.parent.name,t['index']+1,len(a)/rate,'WARN' if warnings else 'OK'),flush=True);return info

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=120);ap.add_argument('--rate',type=int,default=44100);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int,default=12);ap.add_argument('--group',default='all',choices=['all','native_nes','msx_reference']);a=ap.parse_args()
 if not 10<=a.seconds<=600:ap.error('--seconds must be 10..600')
 if not shutil.which('ffmpeg'):raise SystemExit('ffmpeg must be on PATH')
 tasks=[]
 for p in sorted((ROOT/'audio').glob('*/*/tracks.json')):
  if a.group!='all' and p.parent.parent.name!=a.group:continue
  driver=next(iter(sorted(p.parent.glob('*.nsf'))+sorted(p.parent.glob('*.kss'))))
  for t in json.loads(p.read_text())['tracks']:
   side=p.parent/'mp3'/('%02d - %s.json'%(t['index']+1,slug(t['title'])))
   if not side.exists():tasks.append((str(driver),t,a.seconds,a.rate))
 tasks=tasks[:a.limit] if a.limit else tasks
 results=[];errors=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
  pending={ex.submit(render,t):t for t in tasks}
  for fut in concurrent.futures.as_completed(pending):
   task=pending[fut]
   try:results.append(fut.result())
   except Exception as e:errors.append(dict(driver=task[0],track=task[1],error=str(e)));print('ERROR',errors[-1],flush=True)
 results=[json.loads(p.read_text()) for p in sorted((ROOT/'audio').glob('*/*/mp3/*.json'))]
 results.sort(key=lambda r:(r['driver'],r['index']))
 report=dict(format_version=1,render_policy='Bounded capture unless terminal silence; no loop-count claim; original sequence files retained',tracks=results,errors=errors,counts={'rendered':len(results),'requested':len(tasks),'errors':len(errors)})
 (ROOT/'reports'/('audio_render_'+a.group+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 for folder in sorted({(ROOT/r['mp3']).parent for r in results}):
  rows=[r for r in results if (ROOT/r['mp3']).parent==folder]
  (folder.parent/'listen.m3u8').write_text('#EXTM3U\n'+''.join('#EXTINF:%d,%s\nmp3/%s\n'%(round(r['rendered_seconds']),r['title'],pathlib.Path(r['mp3']).name) for r in rows))
 print(json.dumps(report['counts']))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
