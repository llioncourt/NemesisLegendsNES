#!/usr/bin/env python3
"""KSS rip of Nemesis 3 (MSX, Konami RC-764, 1988) with the cartridge's own sound engine and scores.
Standalone (no project imports). Same KSS conventions as the project's tools/rip_msx_kss.py ('KSCC' header,
8 KiB banks, init wrapper at 0xC000, play trampoline at 0xC0E0, track table at 0xC100, RAM 0xE000-0xEFFF cleared
by the init), extended for what the Nemesis 3 engine needs:

  load image 0x6000-0xC1FF: bank 10 at 0x6000 (engine p10:6000/6003/6006, header table p10:7504, waveforms
      p10:7904, drum scripts), bank 11 at 0x8000 (effect scores, stage scores), bank 12 at 0xA000 (scores of codes
      0x01-0x0E), then the wrapper code
  extra 8 KiB banks numbered 9 to 0x3F (first bank 9, 55 banks): the engine writes literal bank numbers
      0x9000 = 0x3F (SCC registers) / 0x0B and 0xB000 = 0x09 / 0x0D / 0x19 (score banks, p10:62DE), so every value
      it writes is a bank of the file: 9, 11, 12, 13 and 25 hold the ROM banks, 10 too, the rest are zero.
      Bank 0x3F being in range keeps the 0x9800-0x988F writes going to the SCC in players that only route
      writes of ROM-mapped pages to the SCC (libgme), and is the real Konami SCC select value
  init (A = track): clear 0xE000-0xEFFF and 0xFDA2 (the engine's frame copy), put WRTPSG/RDPSG at 0x0001/0x0009
      with their vectors at 0x0093/0x0096 (A = register, E = value, registers kept), 0x9000 = 11, 0xB000 = 12 as
      p00:404A does, call p10:6000 (reset: sound 0x01 with priority 255, PSG mixer 0xBF), one engine frame (p10:6006)
      so that the 0x01 channels end as they do in the game the frame after a reset, then the code of the track from
      0xC100 to p10:6003, as p00:589A pide_sonido does in the game
  play (60 Hz): 0x9000 = 11, 0xB000 = 12, jp p10:6006, as the game's interrupt handler (p00:404A-p00:4057)

One track per sound code with a header in p10:7504 (0x01-0x53). Titles and kinds from music.json (catalogue).
usage: rip_n3_kss.py ROM OUT   (writes OUT/nemesis3_msx_original_driver.kss and OUT/tracks.json)"""
import hashlib, json, os, struct, sys

SHA = 'fb4f66bcc3eabaf7eea6b91d1e2f5a15aa2f80a31a056af41d948b32646877a9'
BANK = 0x2000
FIRST_BANK, LAST_BANK = 0x09, 0x3F
ROM_BANKS = (9, 10, 11, 12, 13, 25)          # engine (10), scores (11, 12, 13, 9, 25)
INIT, PLAY, TABLE = 0xC000, 0xC0E0, 0xC100
LOAD, LOAD_END = 0x6000, 0xC200


def asm_init(nt):
    c = bytearray()
    c += bytes.fromhex('f5')                                        # push af (track)
    c += bytes.fromhex('af 21 00 e0 11 01 e0 01 ff 0f 77 ed b0')    # 0xE000-0xEFFF = 0
    c += bytes.fromhex('32 a2 fd')                                  # ld (0xFDA2),a
    bios_at = INIT + 0x60
    c += b'\x21' + struct.pack('<H', bios_at) + bytes.fromhex('11 01 00 01 0d 00 ed b0')       # BIOS bodies -> 0x0001
    c += b'\x21' + struct.pack('<H', bios_at + 13) + bytes.fromhex('11 93 00 01 06 00 ed b0')  # vectors -> 0x0093
    c += bytes.fromhex('3e 0b 32 00 90 3e 0c 32 00 b0')             # 0x9000 = 11, 0xB000 = 12
    c += bytes.fromhex('cd 00 60')                                  # call p10:6000 (reset: requests 0x01, priority 255)
    c += bytes.fromhex('cd 06 60')                                  # call p10:6006: one engine frame ends the 0x01 channels (p10:6AFC),
                                                                    # else every request would lose against priority 255 (p10:6122)
    c += bytes.fromhex('f1 6f 26 00 11') + struct.pack('<H', TABLE) + bytes.fromhex('19 7e')   # A = table[track]
    c += bytes.fromhex('cd 03 60 c9')                               # call p10:6003 ; ret
    assert len(c) <= 0x60
    c += bytes(0x60 - len(c))
    c += bytes.fromhex('d3 a0 f5 7b d3 a1 f1 c9')                   # 0x0001 WRTPSG: out (a0),a; push af; ld a,e; out (a1),a; pop af; ret
    c += bytes.fromhex('d3 a0 db a2 c9')                            # 0x0009 RDPSG: out (a0),a; in a,(a2); ret
    c += bytes.fromhex('c3 01 00 c3 09 00')                         # 0x0093 jp 0x0001 ; 0x0096 jp 0x0009
    assert len(c) <= PLAY - INIT
    return c


def asm_play():
    return bytes.fromhex('3e 0b 32 00 90 3e 0c 32 00 b0 c3 06 60')   # banks 11/12 ; jp p10:6006


def codes_with_header(rom):
    """p10:7504 + 2 x code: words inside the engine window 0x6000-0xBFFF (code 0x00 = 0xFF01 and 0x54 = 0xFFFF are not)"""
    out = []
    for c in range(0x55):
        a = rom[10 * BANK + 0x1504 + 2 * c] | rom[10 * BANK + 0x1505 + 2 * c] << 8
        if 0x6000 <= a < 0xC000: out.append(c)
    return out


def build(rom, titles):
    codes = codes_with_header(rom)
    img = bytearray(LOAD_END - LOAD)
    for addr, b in ((0x6000, 10), (0x8000, 11), (0xA000, 12)):
        img[addr - LOAD:addr - LOAD + BANK] = rom[b * BANK:(b + 1) * BANK]
    init = asm_init(len(codes)); play = asm_play()
    img[INIT - LOAD:INIT - LOAD + len(init)] = init
    img[PLAY - LOAD:PLAY - LOAD + len(play)] = play
    img[TABLE - LOAD:TABLE - LOAD + len(codes)] = bytes(codes)
    extra = bytearray()
    for b in range(FIRST_BANK, LAST_BANK + 1):
        extra += rom[b * BANK:(b + 1) * BANK] if b in ROM_BANKS else bytes(BANK)
    nb = LAST_BANK - FIRST_BANK + 1
    hdr = bytearray(16); hdr[:4] = b'KSCC'
    struct.pack_into('<HHHH', hdr, 4, LOAD, len(img), INIT, PLAY)
    hdr[12] = FIRST_BANK; hdr[13] = 0x80 | nb                       # 8 KiB banks
    hdr[14] = 0; hdr[15] = 0                                        # PSG + SCC, no FM, no RAM mode
    tracks = [dict(index=i, command=c, title=titles.get(c, {}).get('name', 'Sound 0x%02X' % c),
                   kind=titles.get(c, {}).get('kind')) for i, c in enumerate(codes)]
    return bytes(hdr) + bytes(img) + bytes(extra), tracks


def main():
    rom_path, out = sys.argv[1], sys.argv[2]
    rom = open(rom_path, 'rb').read()
    if hashlib.sha256(rom).hexdigest() != SHA: raise SystemExit('unexpected ROM (sha256)')
    titles = {}
    cat = os.path.join(os.path.dirname(os.path.abspath(out)), 'music.json')
    if os.path.exists(cat):
        for e in json.load(open(cat)): titles[int(e['code'], 16)] = e
    kss, tracks = build(rom, titles)
    os.makedirs(out, exist_ok=True)
    f = os.path.join(out, 'nemesis3_msx_original_driver.kss')
    open(f, 'wb').write(kss)
    json.dump(tracks, open(os.path.join(out, 'tracks.json'), 'w'), indent=1)
    print(f, len(kss), 'bytes,', len(tracks), 'tracks, sha256', hashlib.sha256(kss).hexdigest())


if __name__ == '__main__':
    main()
