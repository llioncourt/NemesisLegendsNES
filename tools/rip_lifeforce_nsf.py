#!/usr/bin/env python3
"""rip_lf_nsf.py ROM OUT_DIR
Extract the unmodified Life Force (NES, USA) sound driver and data into an NSF wrapper.
This is an original NES driver rip, NOT a conversion: the image is PRG bank 3 (driver $8001-$872B, data
$872C-$A67F, request table $A680) at $8000 plus the fixed bank 7 at $C000 (request routine $FDAC, stop-all
$FEFE), unchanged except for a small init/play wrapper and the song-to-command table written into the
fixed bank's unused $FF fill at $FF40 (the game never executes there). No bank switching is needed.

Conventions follow the project's tools/rip_konami_nsf.py / rip_gradius_nsf.py: NESM header v1, load $8000,
artist "Konami", NTSC 16639 us / PAL 19997 us, INIT = PHA; clear zero page; clear the driver RAM page
($0600-$06FF); $4010 = 0, $4017 = $40, $4015 = $0F; JSR driver init (stop-all $FEFE); PLA; TAX;
LDA table,X; JSR request ($FDAC); RTS.  PLAY = JMP $8001 (the game's per-frame driver update).
Song titles are the descriptive names of the evidence catalogue's music.json (title_status contextual_not_official); no published track titles were verified.
Standalone: no project imports. Python 3.8+."""
import hashlib, json, pathlib, struct, sys

SHA256_US = 'a606c6c4c6d81b72ee783c5ad9b91cb8e1d09206c4ad2ba881698fa15fa3af57'
REQUEST, STOP, TICK = 0xFDAC, 0xFEFE, 0x8001
STUB = 0xFF40
# (command, title, kind, evidence) - order: stage themes, other music, jingles, effects
TRACKS = [
    (0x25, 'stage 1 theme', 'music', 'stage table $FB2A[0], requested at $FB24'),
    (0x28, 'stage 2 theme', 'music', 'stage table $FB2A[1]'),
    (0x2B, 'stage 3 theme', 'music', 'stage table $FB2A[2]'),
    (0x2E, 'stage 4 theme', 'music', 'stage table $FB2A[3]'),
    (0x31, 'stage 5 theme', 'music', 'stage table $FB2A[4]'),
    (0x22, 'stage 5 battleship theme', 'music', 'bank 6 $AE06 (third battleship, $07DF = 3)'),
    (0x34, 'stage 5 theme after the battleships', 'music', 'bank 6 $ADDB (battleships destroyed)'),
    (0x37, 'stage 6 theme', 'music', 'stage table $FB2A[5]'),
    (0x3A, 'boss theme', 'music', '$DE33 fade then driver $80A5 requests $06DE = $3A'),
    (0x43, 'game start', 'jingle', '$EDC2 (START on the title)'),
    (0x3D, 'game over', 'jingle', '$FC8F'),
    (0x40, 'ending theme', 'jingle', 'bank 1 $B29C'),
    (0x01, 'percussion 1 (driver drum)', 'sfx', 'driver bank 3 $84A5'),
    (0x02, 'percussion 2 (driver drum)', 'sfx', 'driver bank 3 $84A5'),
    (0x03, 'rumble (noise, periodic stage effect)', 'sfx', 'bank 6 $B996, $9117; bank 5 $83DA'),
    (0x04, 'ending beam rumble', 'sfx', 'bank 1 $B013'),
    (0x05, 'normal shot', 'sfx', '$C8CB table $C8D4[0]'),
    (0x06, 'ripple laser shot', 'sfx', '$C8CB table $C8D4[1]'),
    (0x07, 'laser shot', 'sfx', '$C8CB table $C8D4[2]'),
    (0x08, 'stage 4 effect (bank 5 $9AD9)', 'sfx', 'bank 5 $9AD9'),
    (0x09, 'stage 6 pulse (every 64 frames)', 'sfx', 'bank 0 $95B6'),
    (0x0A, 'hit on an indestructible target', 'sfx', '$D2BC'),
    (0x0B, 'hit on an armoured enemy', 'sfx', '$D2B4'),
    (0x0C, 'stage 3 explosion (noise + effect)', 'sfx', 'bank 6 $A807'),
    (0x0E, 'enemy destroyed (variant)', 'sfx', '$D6B2'),
    (0x0F, 'unused effect', 'sfx', 'table record only, never requested'),
    (0x10, 'enemy destroyed', 'sfx', '$D6AE'),
    (0x11, 'segmented enemy destroyed', 'sfx', 'bank 6 $889E, $A499'),
    (0x12, 'stage 1 explosion (noise + effect)', 'sfx', 'bank 6 $8127'),
    (0x14, 'stage 6 effect (bank 5 $A938)', 'sfx', 'bank 5 $A938'),
    (0x15, 'large enemy destroyed', 'sfx', '$D70A, $D722; bank 5 $9A3D'),
    (0x16, 'power capsule taken', 'sfx', '$D1FD'),
    (0x17, 'blue capsule (screen clear)', 'sfx', '$DAE7'),
    (0x18, 'power-up activated', 'sfx', '$C62D'),
    (0x19, 'stage 6 effect (bank 5 $A099)', 'sfx', 'bank 5 $A099'),
    (0x1A, 'player ship destroyed', 'sfx', '$C3E5'),
    (0x1C, 'ship launch (respawn / stage clear take-off)', 'sfx', '$C347, $C3AC'),
    (0x1E, 'extra life', 'sfx', '$D209, $F011'),
    (0x1F, 'big explosion (boss destroyed, planet in the ending)', 'sfx', '$D745; bank 1 $B03D'),
    (0x46, 'pause', 'sfx', '$FD97'),
]


def main(rom_path, out_dir):
    rom = pathlib.Path(rom_path).read_bytes()
    if hashlib.sha256(rom).hexdigest() != SHA256_US:
        raise SystemExit('not Life Force (USA) (sha256 mismatch)')
    prg = rom[16:16 + 131072]
    bank3 = bytearray(prg[3 * 0x4000:4 * 0x4000])
    fixed = bytearray(prg[7 * 0x4000:8 * 0x4000])
    F = lambda a, n: bytes(fixed[a - 0xC000:a - 0xC000 + n])
    B3 = lambda a, n: bytes(bank3[a - 0x8000:a - 0x8000 + n])
    # signatures (request entry, stop-all, driver tick, request table pointer, stage table, free space)
    checks = [(F(0xFDAC, 7), '8de006f004c947'), (F(0xFEFE, 6), '8a489848a900'), (B3(0x8000, 4), '03adec06'),
              (F(0xFDAA, 2), '80a6'), (F(0xFB2A, 6), '25282b2e3137'), (B3(0xA680 + 3 * 0x25, 3), '80be9f')]
    for got, want in checks:
        if got.hex() != want:
            raise SystemExit('driver signature mismatch: %s != %s' % (got.hex(), want))
    table = STUB + 0x40
    init = bytearray.fromhex('48 a9 00 aa 95 00 e8 d0 fb')          # PHA; LDA #0; TAX; clear $00-$FF
    init += bytes.fromhex('9d 00 06 e8 d0 fa')                       # clear $0600-$06FF (driver RAM)
    init += bytes.fromhex('8d 10 40 a9 40 8d 17 40 a9 0f 8d 15 40')   # $4010=0, $4017=$40, $4015=$0F
    init += b'\x20' + struct.pack('<H', STOP)                         # JSR $FEFE (driver reset / stop all)
    init += bytes.fromhex('68 aa bd') + struct.pack('<H', table)      # PLA; TAX; LDA table,X
    init += b'\x20' + struct.pack('<H', REQUEST) + b'\x60'            # JSR $FDAC; RTS
    play = STUB + 0x38
    assert len(init) <= 0x38
    region = F(STUB, 0x40 + len(TRACKS))
    if region != b'\xff' * len(region):
        raise SystemExit('wrapper area $FF40 is not free')
    o = STUB - 0xC000
    fixed[o:o + len(init)] = init
    fixed[play - 0xC000:play - 0xC000 + 3] = b'\x4c' + struct.pack('<H', TICK)
    fixed[table - 0xC000:table - 0xC000 + len(TRACKS)] = bytes(t[0] for t in TRACKS)
    h = bytearray(128); h[:5] = b'NESM\x1a'; h[5:8] = bytes([1, len(TRACKS), 1])
    struct.pack_into('<HHH', h, 8, 0x8000, STUB, play)
    for off, text in ((14, 'Life Force - Native NES Driver'), (46, 'Konami'), (78, '1988 Konami')):
        h[off:off + 32] = text.encode('ascii')[:31].ljust(32, b'\0')
    struct.pack_into('<H', h, 110, 16639); struct.pack_into('<H', h, 120, 19997)
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    nsf = out / 'lifeforce_nes_us_original_driver.nsf'
    nsf.write_bytes(bytes(h) + bytes(bank3) + bytes(fixed))
    meta = dict(source=dict(sha256=SHA256_US, title='Life Force (USA)', mapper=2, prg_bytes=131072),
                source_kind='supplied_NES_ROM', nsf_kind='original_driver_rip', msx_conversion=False, game_integration=False,
                load=0x8000, init=STUB, play=play, driver_init=STOP, driver_request=REQUEST, driver_tick=TICK, source_sound_bank=3,
                image='PRG bank 3 at $8000 + PRG bank 7 at $C000; wrapper and command table at $FF40-$FF%02X (unused $FF fill)' % ((table + len(TRACKS) - 1) & 0xFF),
                tracks=[dict(index=i, command='0x%02X' % c, title=t, kind=k, title_status='contextual_not_official', evidence=e)
                        for i, (c, t, k, e) in enumerate(TRACKS)])
    (out / 'tracks.json').write_text(json.dumps(meta['tracks'], indent=1))
    (out / 'nsf_info.json').write_text(json.dumps(meta, indent=1))
    print(nsf, len(TRACKS), 'songs')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
