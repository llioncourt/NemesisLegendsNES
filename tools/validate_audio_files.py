#!/usr/bin/env python3
"""Validate every final MP3 container; no claim of musical or hardware parity."""
from __future__ import annotations
import concurrent.futures,json,pathlib,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def check(row):
 p=ROOT/row['mp3'];proc=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,sample_rate,channels','-of','json',str(p)],capture_output=True,text=True)
 if proc.returncode:raise RuntimeError(proc.stderr)
 v=json.loads(proc.stdout);stream=v['streams'][0];duration=float(v['format']['duration'])
 if stream['codec_name']!='mp3' or int(stream['sample_rate'])!=44100 or stream['channels']!=2:raise ValueError('Wrong format: '+str(p))
 if abs(duration-row['rendered_seconds'])>0.2:raise ValueError('Duration mismatch: '+str(p))
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Hash mismatch: '+str(p))
 return dict(path=row['mp3'],duration_seconds=duration,format_ok=True,sha256_ok=True)
def main():
 data=json.loads((ROOT/'audio/metadata.json').read_text());rows=data['tracks']
 if not rows:raise SystemExit('No MP3s are included in this checkpoint. Use the separate source-music package or render audio first.')
 with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:result=list(pool.map(check,rows))
 report=dict(files=len(result),passed=len(result),failed=0,scope='MP3 header, sample rate, channels, duration and SHA-256 only',results=result)
 (ROOT/'reports/mp3_integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='results'}))
if __name__=='__main__':main()
