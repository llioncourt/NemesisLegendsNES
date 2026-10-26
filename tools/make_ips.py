#!/usr/bin/env python3
"""Create and byte-verify a standard IPS patch without renaming the source ROM."""
from __future__ import annotations
import argparse, hashlib, pathlib

def create(old: bytes, new: bytes) -> bytes:
    if len(old)!=len(new):raise ValueError('This IPS generator requires equal input/output sizes')
    if len(old)>0xffffff:raise ValueError('IPS 24-bit offset limit exceeded')
    out=bytearray(b'PATCH');n=len(new);pos=0
    while pos<n:
        if old[pos]==new[pos]:pos+=1;continue
        start=pos
        while pos<n and old[pos]!=new[pos] and pos-start<0xffff:
            pos+=1
        run=new[start:pos]
        out+=start.to_bytes(3,'big')+len(run).to_bytes(2,'big')+run
    return bytes(out)+b'EOF'

def apply(original:bytes,patch:bytes)->bytes:
    if not patch.startswith(b'PATCH'):raise ValueError('Not IPS')
    out=bytearray(original);i=5
    while i<len(patch):
        if patch[i:i+3]==b'EOF':
            if i+3!=len(patch):raise ValueError('Unexpected IPS tail')
            return bytes(out)
        if i+5>len(patch):raise ValueError('Truncated record')
        offset=int.from_bytes(patch[i:i+3],'big')
        size=int.from_bytes(patch[i+3:i+5],'big');i+=5
        if size==0:
            if i+3>len(patch):raise ValueError('Truncated RLE record')
            length=int.from_bytes(patch[i:i+2],'big');value=patch[i+2];i+=3
            if offset+length>len(out):raise ValueError('RLE record outside original')
            out[offset:offset+length]=bytes([value])*length
        else:
            if offset+size>len(out) or i+size>len(patch):raise ValueError('Data outside original/patch')
            out[offset:offset+size]=patch[i:i+size];i+=size
    raise ValueError('Missing EOF')

def main():
    p=argparse.ArgumentParser();p.add_argument('old',type=pathlib.Path);p.add_argument('new',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
    orig=a.old.read_bytes();target=a.new.read_bytes();patch=create(orig,target)
    if apply(orig,patch)!=target:raise AssertionError('IPS roundtrip differs from new ROM')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(patch)
    print('IPS verified',len(patch),'bytes',hashlib.sha256(target).hexdigest())
if __name__=='__main__':main()
