"""Recover metadata after a terminated render, without inventing missing QA."""
import hashlib,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from render_audio import ROOT,slug
log=(ROOT/'logs/audio_render.log').read_text()
for p in sorted((ROOT/'audio').glob('*/*/tracks.json')):
 driver=next(iter(sorted(p.parent.glob('*.nsf'))+sorted(p.parent.glob('*.kss'))))
 for t in json.loads(p.read_text())['tracks']:
  f=p.parent/'mp3'/('%02d - %s.mp3'%(t['index']+1,slug(t['title'])))
  if not f.exists() or f.with_suffix('.json').exists():continue
  match=re.search(r'^'+re.escape(p.parent.name)+r' %02d\s+([0-9.]+)s OK$'%(t['index']+1),log,re.M)
  if not match:
   print('Incomplete/unlogged render removed:',f);f.unlink();continue
  result=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=sample_rate,channels','-of','json',str(f)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
  probe=json.loads(result.stdout);duration=float(probe['format']['duration'])
  expected=float(match.group(1))
  if abs(duration-expected)>0.2:raise RuntimeError('Truncated render: '+str(f))
  row=dict(t,driver=str(driver.relative_to(ROOT)),mp3=str(f.relative_to(ROOT)),driver_format=driver.suffix[1:].upper(),sample_rate=44100,channels=2,rendered_seconds=duration,tested_seconds=120,fade_seconds=5 if expected>=119.9 else 0,end_policy='fixed_120s_capture_or_terminal_quiet_trim',source_pcm_peak=None,source_pcm_rms=None,source_clipped_samples=None,output_gain=None,warnings=[],qa_note='Completed-OK line recovered from render log; raw PCM metrics were not persisted before timeout and are not claimed.',bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),status='rendered_source_reference',nes_conversion=False)
  f.with_suffix('.json').write_text(json.dumps(row,indent=2)+'\n')
print('Recoverable completed MP3s:',len(list((ROOT/'audio').glob('*/*/mp3/*.json'))))
