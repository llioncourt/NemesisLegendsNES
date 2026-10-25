#!/usr/bin/env python3
"""Fetch pinned public disassemblies; never execute downloaded code.
Network is required for this optional acquisition step. Local sources are not
silently advertised as downloaded when an HTTP/DNS operation fails.
"""
from __future__ import annotations
import argparse,hashlib,io,json,pathlib,stat,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def fetch(repo):
 commit=repo.get('commit')
 if not commit:raise ValueError('Unpinned supplemental reference: '+repo['repo'])
 dest=ROOT/'third_party'/repo['repo'].replace('/','__')
 if dest.exists():raise FileExistsError('Refusing to overwrite existing checkout: '+str(dest))
 url='https://codeload.github.com/'+repo['repo']+'/zip/'+commit
 req=urllib.request.Request(url,headers={'User-Agent':'NemesisLegends-Evidence/1'})
 with urllib.request.urlopen(req,timeout=90) as response:
  data=response.read(256*1024*1024+1)
 if len(data)>256*1024*1024:raise ValueError('Archive too large')
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  if sum(i.file_size for i in z.infolist())>512*1024*1024:raise ValueError('Expanded archive too large')
  checked=[]
  for info in z.infolist():
   path=pathlib.PurePosixPath(info.filename)
   if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe archive path')
   if stat.S_ISLNK(info.external_attr>>16):raise ValueError('Archive symlink refused')
   rel=pathlib.Path(*path.parts[1:]);checked.append((info,rel))
  dest.mkdir(parents=True)
  for info,rel in checked:
   if not rel.parts:continue
   p=dest/rel
   if info.is_dir():p.mkdir(parents=True,exist_ok=True)
   else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
  (dest/'SOURCE_PIN.json').write_text(json.dumps(dict(repo=repo['repo'],commit=commit,url=url,archive_sha256=hashlib.sha256(data).hexdigest(),local_reassembly_verified=False),indent=2)+'\n')
 return str(dest)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',help='Exact owner/name; default fetches four pinned MSX disassemblies');a=ap.parse_args();results=[]
 catalog=json.loads((ROOT/'evidence/source_catalog.json').read_text())['repositories']
 for r in catalog:
  if not r.get('commit') or (a.repo and r['repo']!=a.repo):continue
  try:results.append(dict(repo=r['repo'],ok=True,path=fetch(r)));print('FETCHED',r['repo'])
  except Exception as e:results.append(dict(repo=r['repo'],ok=False,error=str(e)));print('FAILED',r['repo'],str(e))
 (ROOT/'logs').mkdir(parents=True,exist_ok=True)
 (ROOT/'logs/source_fetch.json').write_text(json.dumps(results,indent=2)+'\n')
 if not results or any(not r['ok']for r in results):raise SystemExit(1)
if __name__=='__main__':main()
