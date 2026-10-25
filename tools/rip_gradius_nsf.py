#!/usr/bin/env python3
"""Extract the unmodified Gradius USA NES sound driver/data into an NSF wrapper.
This is an original NES driver rip, NOT the Nemesis Legends score or an MSX conversion.
ROM addresses and sound IDs are checked against the supplied revision.
"""
from __future__ import annotations
import hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Names are contextual until verified against a publisher track list.
TRACKS=[
 (0x93,'Pre-Stage Flight','game music selector $8381'),
 (0x96,'Stage 1 - Volcano','stage table $833F, index 0'),
 (0x59,'Stage 2 - Stonehenge','stage table $833F, index 1'),
 (0x5B,'Stage 3 - Moai','stage table $833F, index 2'),
 (0x5D,'Stage 4 - Reverse Volcano','stage table $833F, index 3'),
 (0x5F,'Stage 5 - Tentacles','stage table $833F, index 4'),
 (0x61,'Stage 6 - Cells','stage table $833F, index 5'),
 (0x63,'Stage 7 - Fortress','stage table $833F, index 6'),
 (0xA5,'Boss Encounter','game music selector $838A'),
 (0xE8,'Start Sequence','call site $98CE; exact scene title pending'),
 (0xAC,'Stage Sequence Jingle','call site $99CC; exact scene title pending'),
 (0xAF,'Game Over','call site $9820 after death handling'),
 (0xB2,'Ending','call site $CE9E'),
 (0xF7,'Final Encounter Sequence','call site $C1F7; exact scene title pending'),
 (0x90,'Short Jingle - Sound 90','call site $813D; context pending'),
]

def generate():
    selected=json.loads((ROOT/'manifests/selected_sources.json').read_text())['gradius_nes_us']
    rom=(ROOT/selected['path']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=selected['sha256']:raise ValueError('Input hash mismatch')
    prg=rom[16:16+32768]
    for addr,expected in [(0xEC1E,bytes.fromhex('85 df 8a 48 98 48')),(0xED02,bytes.fromhex('a2 b0 a0 00 86 f8')),(0x833F,bytes.fromhex('96 59 5b 5d 5f 61 63'))]:
        if prg[addr-0x8000:addr-0x8000+len(expected)]!=expected:raise ValueError('Driver signature mismatch')
    payload=bytearray(32768)
    payload[0x6C1E:]=prg[0x6C1E:]
    # Preserve caller stack: PHA/PLA balanced. Clear zero page only, not stack.
    code=bytes.fromhex('48 a9 00 a2 00 95 00 e8 d0 fb 8d 10 40 a9 40 8d 17 40 a9 0f 8d 15 40 68 aa bd 80 80 20 1e ec 60')
    payload[:len(code)]=code
    payload[0x60:0x63]=bytes.fromhex('4c 02 ed')
    payload[0x80:0x80+len(TRACKS)]=bytes(t[0] for t in TRACKS)
    h=bytearray(128);h[:5]=b'NESM\x1a';h[5]=1;h[6]=len(TRACKS);h[7]=1
    struct.pack_into('<HHH',h,8,0x8000,0x8000,0x8060)
    for offset,text in [(14,'Gradius - Native NES Driver'),(46,'Konami'),(78,'1986 Konami')]:h[offset:offset+32]=text.encode('ascii')[:31].ljust(32,b'\x00')
    struct.pack_into('<H',h,110,16639);struct.pack_into('<H',h,120,19997)
    out=ROOT/'audio/native_nes/gradius';out.mkdir(parents=True,exist_ok=True)
    f=out/'Gradius_NES_original_driver.nsf';f.write_bytes(h+payload)
    (out/'tracks.json').write_text(json.dumps({'source':selected,'source_kind':'supplied_NES_ROM','nsf_kind':'original_driver_rip','msx_conversion':False,'game_integration':False,'load':0x8000,'init':0x8000,'play':0x8060,'driver_request':0xEC1E,'driver_tick':0xED02,'tracks':[{'index':i,'command':n,'title':title,'title_status':'contextual_not_official','evidence':evidence}for i,(n,title,evidence)in enumerate(TRACKS)]},indent=2))
    print(f)
    return f
if __name__=='__main__':generate()
