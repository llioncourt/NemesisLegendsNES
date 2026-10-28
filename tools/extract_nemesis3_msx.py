#!/usr/bin/env python3
"""Nemesis 3 / Gofer no Yabou Episode II (Konami 1988, RC-764) source-resource reader.
Not a NES gameplay implementation: static graphics, terrain and inventory only.

Format evidence: antxiko/Nemesis3-disassembly (pinned copy under third_party/),
tools/vram.py, dibuja.py, sprites.py, lectores.py, and the listing itself:
  p00:4B3C  RLE to VRAM (same byte format as Nemesis 2): 0 ends, n<0x80 repeats
            the next byte n times, 0x80 brings a new destination word,
            0x81-0xFF copy n&0x7F literal bytes.
  p00:55CD  second RAM format: bits 7-6 of the control byte (00 repeat, 01 count up,
            10 count down, 11 literal), count in bits 5-0.
  p00:4CB1  graphics list: 6-byte records [flags][pattern RLE][first char][colour RLE];
            flag bits 0-2 = bottom/middle/top third; bit 3 switches banks for the
            rest of the walk (bit 4: bank 15 at 0x8000, else 16-17-18).
  p00:4D1B  mirrored character copies: [source][dest][flags][count].
  p00:5345  map column: 6 blocks of 4x4 chars per 4 scroll steps (p24:946F[stage]),
            blocks 0-3 shared (p23:6021), the rest per stage (p23:5FFE[stage],
            p23:6015[stage] of them 16 bytes, the rest 8 bytes = two rows).
  p00:4F82  stage graphics (p16:5FFE, ship p14:6000, copies p16:6014) and sprites
            (p14:7055.., lists p14:6ED4/6EDB/6EED[stage], mirrors p14:6EE2/6FAA[stage]).
  p00:51EE  mid-stage graphics changes p16:602A[stage]: [scroll][list][copies][bg char].
  p02:835A  self-animating characters p07:B1F5[stage].
  p00:511B  boss graphics sets p20:6B1F[0xE440]: list, copies, sprite list, mirrors.
  p26:6349  sequence pictures p27:8F02 (story / on-board computer / ending texts).
The cartridge is 256 KiB = 32 banks of 8 KiB; bank 0 is fixed at 0x4000 and the
other three slots take any bank (tools/paginas.py).  No raw ROM bytes are written
to reports/.
"""
from __future__ import annotations
import collections, hashlib, json, pathlib
from PIL import Image
from extract_nemesis_msx import ROOT, REV, render_map, tile_indices, indexed_image, PAL
from extract_nemesis2_msx import Window, sprite_sheet

EXPECTED = 'fb4f66bcc3eabaf7eea6b91d1e2f5a15aa2f80a31a056af41d948b32646877a9'
DISASM = 'third_party/antxiko__Nemesis3-disassembly'
BANKS_16 = (16, 17, 18)   # p00:4186 bancos_16_17_18
BANKS_14 = (14, 15, 3)    # p00:418E bancos_14_15
BANKS_MAP = (23, 24, 25)  # p00:41B4
BANKS_20 = (20, 21, 22)   # p00:41A1
BANKS_26 = (26, 27, 28)   # p00:41BC
BANKS_29 = (26, 27, 29)   # p00:41E4 bancos_29 (the 29 at 0xA000)
BANKS_22 = (1, 2, 22)     # p00:41AC bancos_22
BANKS_19 = (1, 2, 19)     # p00:41EF
BANKS_7 = (1, 2, 7)       # p00:4173
BANKS_6 = (1, 6, 7)       # p00:416B
BANKS_30 = (1, 30, 31)    # p00:41DC bancos_30_31
THIRD_BASE = {0: 0x1000, 1: 0x800, 2: 0}          # flag bit -> third base (bottom, middle, top)
STAGE_ROLE = {1: 'stage_1_no_map_sun_enemies', 2: 'stage_2', 3: 'stage_3', 4: 'stage_4_boss_rush_no_map',
              5: 'stage_5_red_map_entrance', 6: 'stage_6', 7: 'stage_7_map_entrance', 8: 'stage_8_map_entrance',
              9: 'stage_9_esp_device_then_computer', 10: 'stage_10_needs_all_three_maps', 11: 'stage_11_final'}
# docs/THE-BOSSES.md: boss number per stage (names are not in the ROM).
DOC_BOSSES = {1: [6], 2: [7], 3: [], 4: [0x0B, 1, 3, 4], 5: [8], 6: [9], 7: [0x0E], 8: [0x0C], 9: [0x0D], 10: [0x0F], 11: [0x10]}


def desc(w):
    return {'banks_6000_8000_A000': list(w.banks[1:])}


class Extractor:
    def __init__(self, rom):
        if hashlib.sha256(rom).hexdigest() != EXPECTED: raise ValueError('Wrong Nemesis 3 revision')
        if len(rom) != 32 * 8192: raise ValueError('Nemesis 3 must be 256 KiB')
        self.rom = rom; self.streams = {}; self.copy_records = []; self.lists = {}

    def win(self, banks): return Window(self.rom, banks)

    # -- compressed streams -------------------------------------------------
    def rle(self, v, w, src, dst, kind='vram', mask=0x3fff):
        """p00:4B3C (VRAM) and p00:55AD (RAM, same bytes). Returns the address after the 0."""
        start = src; writes = 0
        for _ in range(16384):
            n = w(src); src += 1
            if n == 0:
                self.record(w, start, src, writes, kind, dst); return src
            if n == 0x80: dst = w.word(src); src += 2; continue
            if n < 0x80: data = bytes([w(src)]) * n; src += 1
            else: data = w.raw(src, n & 127); src += n & 127
            for b in data: v[dst & mask] = b; dst += 1; writes += 1
        raise ValueError('Unterminated RLE at %04X' % start)

    def rle_with_address(self, v, w, src):
        """p00:4B36: the VRAM destination word precedes the RLE."""
        return self.rle(v, w, src + 2, w.word(src), 'vram_with_address')

    def rle2(self, buf, w, src, dst):
        """p00:55CD second RAM format."""
        start = src; writes = 0
        for _ in range(16384):
            x = w(src); src += 1
            if x == 0:
                self.record(w, start, src, writes, 'ram_rle2', dst); return src
            n = x & 0x3f; kind = x & 0xc0
            if kind == 0xc0: data = w.raw(src, n); src += n
            else:
                b = w(src); src += 1; step = {0: 0, 0x40: 1, 0x80: -1}[kind]
                data = bytes((b + step * i) & 0xff for i in range(n))
            for b in data: buf[dst & 0xffff] = b; dst += 1; writes += 1
        raise ValueError('Unterminated RLE2 at %04X' % start)

    def record(self, w, start, end, writes, kind, dst):
        raw = w.raw(start, end - start); key = (w.offset(start), len(raw))
        self.streams[key] = dict(rom_offset=key[0], cpu_address=start, bank=w.banks[(start - 0x4000) // 8192],
                                 compressed_bytes=key[1], decoded_writes=writes, format=kind,
                                 destination=dst, sha256=hashlib.sha256(raw).hexdigest())

    # -- graphics lists and copies ------------------------------------------
    def graphics_list(self, v, w, ix):
        """p00:4CB1. A bank-switch flag changes the window for the rest of the walk, as the Z80 does."""
        entries = []
        for _ in range(256):
            flags = w(ix)
            if not flags: self.lists[(w.offset(ix), 'graphics')] = len(entries); return entries
            if flags & 8: w = self.win((w.banks[1], 15, w.banks[3])) if flags & 0x10 else self.win(BANKS_16)
            for bit in range(3):
                if flags >> bit & 1:
                    target = THIRD_BASE[bit] + 8 * w(ix + 3)
                    self.rle(v, w, w.word(ix + 1), 0x2000 + target); self.rle(v, w, w.word(ix + 4), target)
            entries.append(dict(flags=flags, patterns=w.word(ix + 1), first_char=w(ix + 3), colours=w.word(ix + 4))); ix += 6
        raise ValueError('Unterminated graphics list at %04X' % ix)

    def copies(self, v, w, ix, owner):
        """p00:4D1B. Vertical flip (bit 7) moves patterns and colours; horizontal mirror only patterns."""
        n_rec = 0
        for _ in range(256):
            source = w(ix)
            if not source: return n_rec
            dest, flags, count = w(ix + 1), w(ix + 2), w(ix + 3); third = 0 if flags & 4 else 0x800 if flags & 2 else 0x1000
            p = bytearray(v[(0x2000 + third + 8 * source + i) & 0x3fff] for i in range(count * 8))
            c = bytearray(v[(third + 8 * source + i) & 0x3fff] for i in range(count * 8))
            if flags & 0x80:
                for i in range(0, len(p), 8): p[i:i + 8] = p[i:i + 8][::-1]; c[i:i + 8] = c[i:i + 8][::-1]
            else: p = bytearray(REV[b] for b in p)
            for bit, base in [(3, 0x1000), (4, 0x800), (5, 0)]:
                if flags >> bit & 1:
                    for i in range(len(p)): v[(0x2000 + base + dest * 8 + i) & 0x3fff] = p[i]; v[(base + dest * 8 + i) & 0x3fff] = c[i]
            self.copy_records.append(dict(owner=owner, address=ix, rom_offset=w.offset(ix), source=source, destination=dest, flags=flags, count=count))
            ix += 4; n_rec += 1
        raise ValueError('Unterminated copy list at %04X' % ix)

    def sprite_list(self, v, w, hl):
        """p00:50C2: [first sprite pattern][RLE address] until 0."""
        n = 0
        for _ in range(256):
            if not w(hl): return n
            self.rle(v, w, w.word(hl + 1), 0x1800 + 8 * w(hl)); hl += 3; n += 1
        raise ValueError('Unterminated sprite list at %04X' % hl)

    def sprite_mirrors(self, v, w, ix):
        """p00:4E5A: [kind][count][source][dest]; kind 1 flips vertically, others mirror horizontally."""
        n = 0
        for _ in range(256):
            kind = w(ix)
            if not kind: return n
            count, src, dst = w(ix + 1), w(ix + 2), w(ix + 3)
            for k in range(count):
                a = 0x1800 + 8 * src + 32 * k; data = bytes(v[a:a + 32])
                if kind == 1: data = data[:16][::-1] + data[16:][::-1]
                else: r = bytes(REV[b] for b in data); data = r[16:] + r[:16]
                b = 0x1800 + 8 * dst + 32 * k; v[b:b + 32] = data
            ix += 4; n += 1
        raise ValueError('Unterminated sprite mirror list at %04X' % ix)

    # -- stage graphics -----------------------------------------------------
    def stage_changes(self, stage):
        """p00:51EE / p16:602A[stage]: 7-byte records until scroll 0xFFFF."""
        w = self.win(BANKS_16); a = w.word(0x602a + 2 * stage); out = []
        while w.word(a) != 0xffff and len(out) < 32:
            out.append(dict(scroll=w.word(a), graphics_list=w.word(a + 2), copies=w.word(a + 4), background_char=w(a + 6), record_address=a)); a += 7
        return out

    def stage_vram(self, stage):
        """p00:4F82: returns [(from scroll, vram bytes)] - the initial set and the set after each change."""
        v = bytearray(0x4000); w = self.win(BANKS_16)
        self.graphics_list(v, w, w.word(0x5ffe + 2 * stage))
        self.graphics_list(v, self.win(BANKS_14), 0x6000)
        self.copies(v, w, w.word(0x6014 + 2 * stage), 'stage_%d' % stage)
        out = [(0, bytes(v))]
        for ch in self.stage_changes(stage):
            self.graphics_list(v, w, ch['graphics_list']); self.copies(v, w, ch['copies'], 'stage_%d_change' % stage); out.append((ch['scroll'], bytes(v)))
        return out

    def animation_list(self, stage):
        """p02:835A / p07:B1F5[stage]: [animation][scroll] words until scroll 0xFFFF."""
        w = self.win(BANKS_7); a = w.word(0xb1f5 + 2 * stage); out = []
        while len(out) < 64:
            out.append((w.word(a), w.word(a + 2)))
            if w.word(a + 2) == 0xffff: return a, out
            a += 4
        raise ValueError('Unterminated animation list')

    def animation(self, address):
        """[wait][steps][step words]; a step is 10-byte records [char][flags][8 bytes] until 0 (p02:83B9)."""
        w = self.win(BANKS_7)
        if w(address) == 0: return None
        steps = []
        for k in range(w(address + 1)):
            q = w.word(address + 2 + 2 * k); recs = []
            while w(q): recs.append((w(q), w(q + 1), w.raw(q + 2, 8))); q += 10
            steps.append(recs)
        return dict(wait=w(address), steps=steps)

    @staticmethod
    def apply_step(v, recs):
        for c, m, data in recs:
            base = 0 if m & 8 else 0x2000
            for bit in range(3):
                if m >> bit & 1: t = THIRD_BASE[bit]; v[base + t + c * 8:base + t + c * 8 + 8] = data

    def vram_at_step(self, v, anim, step=0):
        """One full cycle of steps ending at `step` (tools/vram.py con_paso)."""
        v = bytearray(v)
        if anim:
            n = len(anim['steps'])
            for k in range(step + 1, step + 1 + n): self.apply_step(v, anim['steps'][k % n])
        return v

    # -- terrain ------------------------------------------------------------
    def limits(self, stage):
        """p19:A90F + 6*stage -> 0xE421-0xE426 (map start, map end, two more words)."""
        w = self.win(BANKS_19); a = 0xa90f + 6 * stage
        return dict(record_address=a, rom_offset=w.offset(a), map_start=w.word(a), map_end=w.word(a + 2), word_e425=w.word(a + 4))

    def terrain(self, stage):
        w = self.win(BANKS_MAP); lim = self.limits(stage); start, end = lim['map_start'], lim['map_end']
        meta = dict(stage_id=stage, rows=22, scroll_limits=lim, map_pointer_table=0x946f, block_pointer_table=0x5ffe, big_block_count_table=0x6015,
                    shared_blocks_address=0x6021, runtime_integration=False, dynamic_terrain_and_enemy_events='not_extracted')
        if start == 0xffff:
            meta.update(columns=0, has_map=False); return meta, [bytearray() for _ in range(22)], b''
        mapa = w.word(0x946f + 2 * stage); base = w.word(0x5ffe + 2 * stage); n16 = w(0x6015 + stage)
        block_cols = (end - start + 3) // 4; script = w.raw(mapa, 6 * block_cols)
        rows = [bytearray() for _ in range(22)]; used = {}
        for s in range(start, end):
            k = ((s - start) >> 2) * 6; inner = s & 3
            for b in range(6):
                n = script[k + b]
                if n < 4: addr, size = 0x6021 + 16 * n, 16
                else:
                    c = n - 4
                    if c < n16: addr, size = base + 16 * c, 16
                    else: addr, size = base + 16 * n16 + 8 * (c - n16), 8
                raw = w.raw(addr, size); blk = raw + bytes(16 - size)
                used[n] = dict(id=n, address=addr, rom_offset=w.offset(addr), bytes=size, hex=raw.hex())
                for y in range(2 if b == 5 else 4): rows[4 * b + y].append(blk[4 * y + inner])
        tables = sorted({w.word(0x5ffe + 2 * f) for f in range(1, 12)}) + [0x9471]
        meta.update(has_map=True, columns=end - start, column_script_address=mapa, column_script_bank=w.banks[(mapa - 0x4000) // 8192],
                    column_script_rom_offset=w.offset(mapa), column_script_bytes=len(script), block_columns=block_cols,
                    block_table_address=base, block_table_rom_offset=w.offset(base), block_table_bytes=tables[tables.index(base) + 1] - base,
                    blocks_of_16_bytes=n16, used_blocks=sorted(used.values(), key=lambda d: d['id']))
        return meta, rows, script

    # -- sprites ------------------------------------------------------------
    SHIP = {'normal': 0x7082, 'shield_state2_hits_gt1': 0x70cb, 'shield_state2_last_hit': 0x7166,
            'shield_state3_hits_gt1': 0x71d1, 'shield_state3_last_hit': 0x72a6}   # p00:5019

    def sprites(self, stage, ship='normal', big_beam=False):
        """p00:4F82 sprite part; returns the 0x1800-0x1FFF sprite pattern table."""
        v = bytearray(0x4000); w = self.win(BANKS_14)
        self.rle(v, w, 0x7055, 0x1800); self.rle(v, w, self.SHIP[ship], 0x1840)
        self.rle(v, w, 0x7447, 0x19e0); self.rle(v, w, 0x74a4, 0x1920); self.rle(v, w, 0x74d8, 0x1980)
        if big_beam: self.rle(v, w, 0x7537, 0x1920)    # p00:506C, only with 0xE5E0
        self.sprite_list(v, w, 0x6ed4); self.sprite_list(v, w, 0x6edb); self.sprite_mirrors(v, w, 0x6ee2)
        self.sprite_list(v, w, w.word(0x6eed + 2 * stage)); self.sprite_mirrors(v, w, w.word(0x6faa + 2 * stage))
        return bytes(v[0x1800:0x2000])

    # -- boss sets (p00:511B) -----------------------------------------------
    def four_list_set(self, address, owner):
        w = self.win(BANKS_20); v = bytearray(0x4000)
        g, c, s, m = (w.word(address + 2 * k) for k in range(4))
        self.graphics_list(v, w, g); self.copies(v, w, c, owner); self.sprite_list(v, w, s); self.sprite_mirrors(v, w, m)
        self.rle(v, w, 0x6ac8, 0x1f60)   # p00:514F, loaded with every boss
        return v, dict(set_address=address, rom_offset=w.offset(address), graphics_list=g, copies=c, sprite_list=s, sprite_mirrors=m)

    # -- sequence pictures (p26:62A6 / p26:6349) -----------------------------
    def picture_colour(self, n):
        """p26:62D3: 0 for 0x2F/0x6F/0x30-34/0x70-74/0x80-88, 0x90 (chars from 0x80) for 0x25-26/0x65-66, else 0xF0."""
        if n in (0x2f, 0x6f) or 0x30 <= n < 0x35 or 0x70 <= n < 0x75 or 0x80 <= n < 0x89: colour, high = 0, 0
        elif n in (0x25, 0x26, 0x65, 0x66): colour, high = 0x90, 1
        else: colour, high = 0xf0, 0
        if n in (0x32, 0x72): high = 1
        return colour, high

    def picture(self, n):
        w = self.win(BANKS_26); a = w.word(0x8f02 + 2 * n)
        if a == 0: return None
        start = a; chunks = []
        while True:
            dest = w.word(a); x = w(a + 2); a += 3; k = x & 0x1f; third = (x >> 5) & 3; chars = []
            if n < 0x40:
                while k > 0:
                    mask = w(a); a += 1
                    for i in range(min(8, k)):
                        chars.append(w(a) | (((mask << i) & 0x80) >> 7) << 8); a += 1
                    k -= min(8, k)
            else:
                while k > 0:
                    t = min(3, k); group = w.raw(a, t); a += t; chars.extend(b & 0x3f for b in group); k -= t
                    if k > 0:
                        b0, b1, b2 = group; chars.append(((b2 >> 6) << 4) | ((b1 >> 6) << 2) | (b0 >> 6)); k -= 1
            chunks.append(dict(buffer_address=dest, third=third, chars=chars))
            if x & 0x80: break
        colour, high = self.picture_colour(n)
        return dict(picture=n, address=start, rom_offset=w.offset(start), compressed_bytes=a - start, chunks=chunks, colour=colour, first_free_char=0x80 if high else 1)

    def sequence_char(self, idx):
        """p00:4F02: 8 pattern bytes from p20:6018 + 8*idx."""
        return self.win(BANKS_20).raw(0x6018 + 8 * idx, 8)


# ----------------------------------------------------------------------------
def render_names(v, names, width, rows, third_of_row=lambda r: r // 8):
    """A 32-column name buffer drawn with SCREEN 2 patterns/colours of VRAM v."""
    im = Image.new('P', (width * 8, rows * 8)); im.putpalette([c for rgb in PAL for c in rgb] + [0] * (768 - 48))
    for y in range(rows):
        for x in range(width):
            im.paste(indexed_image(tile_indices(v, names[y * width + x], third_of_row(y)), (8, 8)), (x * 8, y * 8))
    return im


def tile_sheet(v):
    sheet = Image.new('P', (16 * 8 * 3, 16 * 8)); sheet.putpalette([c for rgb in PAL for c in rgb] + [0] * (768 - 48))
    for third in range(3):
        for tile in range(256): sheet.paste(indexed_image(tile_indices(v, tile, third), (8, 8)), (third * 128 + (tile % 16) * 8, (tile // 16) * 8))
    return sheet.resize((768, 256), Image.Resampling.NEAREST)


def render_picture(ex, pic):
    """A sequence picture on its own buffer: 0xC400 (64 wide, 22 rows) or 0xCA00 (32 wide, 24 rows)."""
    addrs = [c['buffer_address'] for c in pic['chunks']]
    if all(0xca00 <= a < 0xcd00 for a in addrs): base, stride, rows = 0xca00, 32, 24
    elif all(0xc400 <= a < 0xc980 for a in addrs): base, stride, rows = 0xc400, 64, 22
    else: return None, 'buffer_address_outside_known_buffers'
    colour = pic['colour'] or 0xf1
    im = Image.new('P', (32 * 8, rows * 8)); im.putpalette([c for rgb in PAL for c in rgb] + [0] * (768 - 48)); cells = 0
    for ch in pic['chunks']:
        for i, idx in enumerate(ch['chars']):
            off = ch['buffer_address'] - base + i; y, x = divmod(off, stride)
            if x >= 32 or y >= rows: continue
            pat = ex.sequence_char(idx); pix = bytearray()
            for row in pat: pix.extend((colour >> 4) if row & (0x80 >> b) else (colour & 15) for b in range(8))
            im.paste(indexed_image(bytes(pix), (8, 8)), (x * 8, y * 8)); cells += 1
    return im, dict(buffer=base, stride=stride, rows=rows, cells=cells, colour_used=colour)


def copy_rect(buf, src, dest, rows, cols):
    """p00:59A1 copia_rectangulo: contiguous source rows of `cols` bytes into 32-byte rows."""
    for r in range(rows): buf[dest - 0xca00 + 32 * r:dest - 0xca00 + 32 * r + cols] = src[r * cols:(r + 1) * cols]


def write_set(folder, name, v, meta, with_sprites=False):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'source_vram.bin').write_bytes(v); tile_sheet(v).save(folder / 'tiles.png')
    if with_sprites:
        data = bytes(v[0x1800:0x2000]); (folder / 'sprites.bin').write_bytes(data); sprite_sheet(data).save(folder / 'sprites.png')
    (folder / 'set.json').write_text(json.dumps(dict(name=name, **meta), indent=2) + '\n')


def count_tiles(v, owner, tiles, colours):
    for third in range(3):
        for tile in range(256):
            pix = tile_indices(v, tile, third); tiles.setdefault(pix, []).append([owner, third, tile]); colours[len(set(pix))] += 1


def extract():
    selected = json.loads((ROOT / 'manifests/selected_sources.json').read_text())['nemesis3_msx']
    ex = Extractor((ROOT / selected['path']).read_bytes()); out = ROOT / 'assets/msx/nemesis3'; out.mkdir(parents=True, exist_ok=True)
    manifest = []; tiles = {}; colours = collections.Counter(); previews = []; sprite_sets = 0; total_columns = 0
    structure = dict(source='Nemesis 3 - The Eve of Destruction (MSX, RC-764), %s' % DISASM, source_sha256=EXPECTED, stages=[])
    for stage in range(1, 12):
        folder = out / ('map_%02d' % stage); folder.mkdir(exist_ok=True)
        segments = ex.stage_vram(stage); changes = ex.stage_changes(stage); meta, rows, script = ex.terrain(stage)
        anim_table, anim_list = ex.animation_list(stage)
        anims = {addr: ex.animation(addr) for addr, _ in anim_list}
        (folder / 'source_vram.bin').write_bytes(segments[0][1])
        for i, (scroll, v) in enumerate(segments[1:], 1): (folder / ('source_vram_change_%02d.bin' % i)).write_bytes(v)
        (folder / 'terrain_rows.bin').write_bytes(b''.join(rows)); (folder / 'column_script.bin').write_bytes(script)
        # terrain preview: characters of the segment and the step-0 state of the animation in force (tools/dibuja.py)
        if meta['has_map']:
            start = meta['scroll_limits']['map_start']; width = meta['columns']; cache = {}
            img = Image.new('P', (width * 8, 176)); img.putpalette([c for rgb in PAL for c in rgb] + [0] * (768 - 48))
            # the animation in force from scroll d is the list entry whose scroll is the first above d (tools/vram.py animacion)
            anim_from = {d: anims[next(addr for addr, sc in anim_list if sc > d)] for d in [0] + [s for _, s in anim_list if s != 0xffff]}
            for x in range(width):
                s = start + x; seg = max(i for i, (d, _) in enumerate(segments) if d <= s)
                a = max([d for d, an in anim_from.items() if d <= s and an] or [0]); key = (seg, a)
                if key not in cache: cache[key] = ex.vram_at_step(segments[seg][1], anim_from[a])
                v = cache[key]
                for y in range(22): img.paste(indexed_image(tile_indices(v, rows[y][x], y // 8), (8, 8)), (x * 8, y * 8))
            img.save(folder / 'terrain.png'); previews.append(img.crop((0, 0, 256, 176)).convert('RGB'))
        else:
            previews.append(render_map(segments[0][1], [bytearray(32) for _ in range(22)]).convert('RGB'))
        tile_sheet(segments[0][1]).save(folder / 'tiles.png')
        variants = [(ship, False) for ship in Extractor.SHIP] + [('normal', True)]
        for ship, beam in variants:
            data = ex.sprites(stage, ship, beam); name = ship + ('_big_beam' if beam else '')
            (folder / ('sprites_%s.bin' % name)).write_bytes(data); sprite_sets += 1
            if name == 'normal': sprite_sheet(data).save(folder / 'sprites.png')
        for i, (_, v) in enumerate(segments): count_tiles(v, 'stage_%d_seg_%d' % (stage, i), tiles, colours)
        total_columns += meta['columns']
        w16 = ex.win(BANKS_16); w14 = ex.win(BANKS_14)
        meta.update(graphics_list_address=w16.word(0x5ffe + 2 * stage), graphics_list_rom_offset=w16.offset(w16.word(0x5ffe + 2 * stage)),
                    copies_address=w16.word(0x6014 + 2 * stage), ship_graphics_list=0x6000, mid_stage_changes=changes,
                    animation_list_address=anim_table, animation_list=[dict(animation=a, until_scroll=s, steps=len(anims[a]['steps']) if anims[a] else 0) for a, s in anim_list],
                    sprite_list_address=w14.word(0x6eed + 2 * stage), sprite_mirror_list_address=w14.word(0x6faa + 2 * stage),
                    vram_segments=[dict(from_scroll=d, file='source_vram.bin' if i == 0 else 'source_vram_change_%02d.bin' % i) for i, (d, _) in enumerate(segments)])
        (folder / 'stage.json').write_text(json.dumps(meta, indent=2) + '\n'); manifest.append(meta)
        structure['stages'].append(stage_structure(ex, stage, meta))
    # boss graphics sets p20:6B1F[0xE440] and the two extra sets of p00:515F/516F
    w20 = ex.win(BANKS_20); boss_sets = []; seen = {}
    for boss in range(1, 0x12):
        a = w20.word(0x6b1f + 2 * boss)
        if a in seen: seen[a]['boss_numbers'].append(boss); continue
        v, meta = ex.four_list_set(a, 'boss_%02X' % boss); meta['boss_numbers'] = [boss]; seen[a] = meta
        write_set(out / 'bosses' / ('set_%04X' % a), 'boss_set_%04X' % a, v, meta, True); boss_sets.append(meta); count_tiles(v, 'boss_set_%04X' % a, tiles, colours)
    for a, name in [(0x6bbc, 'p00_515F'), (0x6b7b, 'p00_516F_bit0_clear'), (0x6b83, 'p00_516F_bit0_set')]:
        v, meta = ex.four_list_set(a, name); meta['boss_numbers'] = []; meta['loader'] = name
        write_set(out / 'bosses' / ('set_%04X' % a), name, v, meta, True); boss_sets.append(meta); count_tiles(v, name, tiles, colours)
    for m in boss_sets: m['boss_code_addresses'] = {('%02X' % b): boss_code(ex, b) for b in m['boss_numbers']}
    (out / 'bosses' / 'boss_sets.json').write_text(json.dumps(boss_sets, indent=2) + '\n')
    # full-screen pictures and the graphics sets of the sequences
    pictures = extract_pictures(ex, out / 'pictures'); screens = extract_screens(ex, out / 'screens', tiles, colours)
    (out / 'source_tile_dictionary.bin').write_bytes(b''.join(tiles))
    (out / 'source_tile_references.json').write_text(json.dumps([dict(sha256=hashlib.sha256(p).hexdigest(), references=r) for p, r in tiles.items()]))
    (out / 'stage_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'compressed_streams.json').write_text(json.dumps(sorted(ex.streams.values(), key=lambda s: s['rom_offset']), indent=2) + '\n')
    (out / 'mirror_records.json').write_text(json.dumps(ex.copy_records, indent=2) + '\n')
    contact = Image.new('RGB', (1024, 3 * 176))
    for i, im in enumerate(previews): contact.paste(im, ((i % 4) * 256, (i // 4) * 176))
    contact.save(out / 'all_11_map_previews.png')
    structure.update(interludes=interludes(), secret_entrance_table=0xa3c8, notes=structure_notes())
    (ROOT / 'reports/nemesis3_structure.json').write_text(json.dumps(structure, indent=2) + '\n')
    report = dict(source_sha256=EXPECTED, maps=11, maps_with_terrain=sum(1 for m in manifest if m['has_map']), terrain_columns=total_columns,
                  vram_segments=sum(len(m['vram_segments']) for m in manifest), source_tile_occurrences=sum(len(r) for r in tiles.values()),
                  unique_source_pixel_tiles=len(tiles), sprite_sets=sprite_sets, boss_graphics_sets=len(boss_sets), sequence_pictures=pictures['decoded'],
                  sequence_picture_slots=pictures['slots'], sequence_pictures_rendered=pictures['rendered'], screens=len(screens),
                  compressed_streams=len(ex.streams), compressed_stream_bytes=sum(s['compressed_bytes'] for s in ex.streams.values()),
                  mirror_copy_records=len(ex.copy_records), color_counts_per_tile=dict(sorted(colours.items())), runtime_integration=False,
                  source_hardware_vram_comparison='pending (the upstream disassembly reports its own openMSX checks; none were run here)',
                  limitations=[
                      'Static graphics, terrain and inventory only. Enemies, bosses, collisions, scrolling events and cutscene logic are not implemented.',
                      'Stages 1 and 4 have no terrain map in the ROM (scroll limits 0xFFFF): the stage 1 sun and the stage 4 boss rush are drawn by code from enemy/boss records.',
                      'Terrain previews use the character set in force at each column (mid-stage changes p00:51EE) and step 0 of the self-animating characters (p02:835A); objects, pieces and enemies made of characters are not drawn.',
                      'Sprite sets are the stage-start state (p00:4F82) with the ship variants of p00:5019; sprites loaded later by object code are not included.',
                      'Boss graphics sets are decoded onto a blank VRAM for inspection; in the game they overlay the stage set.',
                      'Sequence pictures are rendered standalone with their p26:62D3 colour (0xF1 substituted where the code uses colour 0 and lets a fade-in routine colour them); the frames, portraits and animations around them are not composed, except the static on-board computer frame and the initial title buffer.',
                      'The title logo animation (p30:85BD-870F) and every state-machine composition of the story and ending are not replicated; the Konami logo is shown in its final faded-in state.',
                      'MSX2 palettes (p00:4B94) are ignored: the TMS9918 palette is used.',
                      'No NES palette quantisation has been applied.'])
    (ROOT / 'reports/nemesis3_extraction.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report, indent=2))


def boss_code(ex, boss):
    """p01:7D40: A = 0xE440 - 1 dispatched through the p04:9D9E table with banks 4-5 (p00:415B)."""
    w = ex.win((1, 4, 5)); a = w.word(0x9d9e + 2 * (boss - 1)); return dict(address=a, bank=w.banks[(a - 0x4000) // 8192], rom_offset=w.offset(a))


def music_entries(ex, stage):
    """p00:5759: word table p00:5792[stage]; 3-byte entries [tune][scroll]; stage 4 returns before reading."""
    w = ex.win((1, 2, 3)); a = w.word(0x5792 + 2 * stage); out = []
    while a < 0x57e9 and len(out) < 8:      # 0x57E9: end of the bytes the upstream campaign measured as read
        tune, scroll = w(a), w.word(a + 1); out.append(dict(tune=tune, until_scroll=scroll, entry_address=a)); a += 3
        if scroll >= 0x4000: break
    return a, out


def secret_entrances(ex, stage):
    """p19:A3C8 + 2*stage -> 4-byte entries [scroll][type<<4 | place][y] (p02:80ED/80BE), in scroll order,
    walked by the 0xE7F8 index; the list runs up to the next list (the lists are packed, p19:A3E0-A490)."""
    w = ex.win(BANKS_19); ptrs = [w.word(0xa3c8 + 2 * s) for s in range(1, 12)]; a = ptrs[stage - 1]
    end = min([p for p in ptrs if p > a] + [0xa490]); out = []
    for e in range(a, end - 3, 4):
        c = w(e + 2); out.append(dict(scroll=w.word(e), type=c >> 4, place=c & 15, y=w(e + 3)))
    return a, out


def appearances(ex, stage):
    """p01:6DCD: p06:8000 + 2*(stage-1) -> 3-byte records until scroll 0xFFFF."""
    w = ex.win(BANKS_6); a = w.word(0x8000 + 2 * (stage - 1)); n = 0; k = a
    while w.word(k) != 0xffff and n < 4096: k += 3; n += 1
    return a, n


def stage_structure(ex, stage, meta):
    w1 = ex.win((1, 2, 3)); end_boss = w1(0x6111 + stage) if stage <= 8 else None   # p01:6128: p01:6111 + stage on the stages 1,2,5-8 end path
    music_end, music = music_entries(ex, stage); ent_addr, ents = secret_entrances(ex, stage); app_addr, app_n = appearances(ex, stage)
    bosses = []
    for b in DOC_BOSSES[stage]:
        bosses.append(dict(number=b, name='UNRESOLVED (names are not in the ROM; docs/THE-BOSSES.md lists them by number)', code=boss_code(ex, b), source='docs/THE-BOSSES.md'))
    unresolved = ['third word of the p19:A90F record (0xE425) is copied with the limits; its use is not described in the docs']
    if stage == 4: unresolved.append('stage 4 bosses come from the p01:6243 table in order 0x0B, 1, 3, 4 (docs); the p01:6111 entry for stage 4 is not read on that path')
    if stage == 3: unresolved.append('the p01:6111 entry for stage 3 is 0 (no boss, as docs/THE-BOSSES.md says); the stage-3 end path itself was not traced here')
    if stage >= 9: unresolved.append('stages 9-11 do not use the p01:6111 table (p01:611A path is stages 1, 2, 5-8); the code that brings out their boss was not traced here, the boss number comes from docs/THE-BOSSES.md')
    return dict(map_id=stage, role=STAGE_ROLE[stage], has_terrain_map=meta['has_map'], length_columns=meta['columns'],
                scroll_limits=meta['scroll_limits'], column_script=dict(address=meta.get('column_script_address'), rom_offset=meta.get('column_script_rom_offset'), bytes=meta.get('column_script_bytes')),
                graphics_list=dict(address=meta['graphics_list_address'], rom_offset=meta['graphics_list_rom_offset'], banks=list(BANKS_16)),
                mid_stage_changes=len(meta['mid_stage_changes']), self_animating_character_sets=sum(1 for a in meta['animation_list'] if a['steps']),
                boss_table_p01_6111_entry=end_boss, bosses=bosses,
                music=dict(table=0x5792, entries=music, source='p00:5759 reads [tune][scroll]; docs/THE-STAGES.md table agrees' if stage != 4 else 'p00:5759 returns for stage 4; its tunes come from the boss code (docs/THE-MUSIC.md: 0x0A, 0x09, 0x0B)'),
                secret_entrances=dict(list_address=ent_addr, entries=ents, note='one of the four places is used per game (0xE381 = frame counter & 3, p26:6819)'),
                enemy_appearance_records=dict(list_address=app_addr, records=app_n, banks=list(BANKS_6)),
                unresolved=unresolved)


def interludes():
    return [dict(after_stage=3, kind='on_board_computer_radar', code='p27:814D (0xE321 = 1) -> p27:81F4 graphics p27:8208', music=0x3f, source='docs/THE-STAGES.md, docs/THE-SEQUENCES.md, docs/THE-MUSIC.md (p27:817B)'),
            dict(after_stage=4, kind='on_board_computer_scene', code='p27:814D -> p27:836A', music='UNRESOLVED', source='docs/THE-STAGES.md'),
            dict(after_stage=9, kind='on_board_computer_map_check', code='p00:45E3, p26:7EC5; all maps p26:7F7A -> stage 10; missing p26:7FC8 -> stage 5/7/8; marks 0xE393-0xE395 (p26:7E2A)', music=0x3f, source='docs/THE-STAGES.md, docs/THE-MUSIC.md (p26:7EFE)'),
            dict(after_stage=11, kind='ending', code='p00:4599; secret type 0x0B (0xE396) adds a step p27:8786', music=[0x42, 0x40, 0x41], source='docs/THE-SEQUENCES.md, docs/THE-MUSIC.md'),
            dict(trigger='secret entrance', kind='state_9', code='p26:6CA4: types 1-7 weapon p26:6E29, 8-0x0A maps p26:7D46, 0x0B p27:80B7, others p27:804A', music=[0x3f, 0x4f], source='src/p26.notes 0x6CA4, docs/THE-MUSIC.md'),
            dict(routing='stages 1,2,5,6,7,8,10 -> next (p00:45B3); 3,4 -> computer then next (p00:45CA, p27:814D); 9 -> computer (p00:45E3, p26:7EC5); 11 -> ending (p00:4599)', source='docs/THE-STAGES.md'),
            dict(note='The "three maps" are collectible marks (0xE393 red, 0xE394 blue, 0xE395 green) set by secret entrance types 8, 9, 0x0A of stages 5, 7, 8 (p26:7D46); they are not terrain maps.')]


def structure_notes():
    return ['Map ids equal stage numbers 1-11; stages 1 and 2 share one map pointer and so do 4 and 5 (p24:946F), but 1 and 4 never draw it (limits 0xFFFF).',
            'Boss code addresses come from the p04:9D9E dispatcher (index 0xE440 - 1, p01:7D40) with banks 4-5 mapped; entries at 0x9DC0 are the empty handler.',
            'Music tune numbers are the sound engine requests of p00:5792; tune names follow docs/THE-MUSIC.md.',
            'Everything marked UNRESOLVED was not verified in the listing or its docs.']


def extract_pictures(ex, folder):
    folder.mkdir(parents=True, exist_ok=True); index = []; by_addr = {}; rendered = 0
    w = ex.win(BANKS_26)
    for n in range(0x89):
        a = w.word(0x8f02 + 2 * n)
        if a == 0: index.append(dict(slot=n, unused=True)); continue
        if a in by_addr: by_addr[a]['slots'].append(n); index.append(dict(slot=n, same_as=by_addr[a]['first_slot'])); continue
        pic = ex.picture(n); im, info = render_picture(ex, pic)
        entry = dict(slot=n, first_slot=n, slots=[n], address=a, rom_offset=pic['rom_offset'], compressed_bytes=pic['compressed_bytes'], chunks=len(pic['chunks']),
                     chars=sum(len(c['chars']) for c in pic['chunks']), colour=pic['colour'], first_free_char=pic['first_free_char'],
                     buffer_addresses=[c['buffer_address'] for c in pic['chunks']], max_char_index=max(x for c in pic['chunks'] for x in c['chars']))
        if im is not None: im.save(folder / ('picture_%02X.png' % n)); entry['png'] = 'picture_%02X.png' % n; entry['render'] = info; rendered += 1
        else: entry['render'] = info
        (folder / ('picture_%02X.json' % n)).write_text(json.dumps(pic, indent=1) + '\n'); by_addr[a] = entry; index.append(entry)
    (folder / 'pictures.json').write_text(json.dumps(dict(table='p27:8F02', slots=0x89, char_table='p20:6018', pictures=index), indent=2) + '\n')
    return dict(slots=0x89, decoded=len(by_addr), rendered=rendered)


def extract_screens(ex, folder, tiles, colours):
    """Graphics sets of the logo, title, story, on-board computer and ending, with full pictures where the buffer build is static."""
    folder.mkdir(parents=True, exist_ok=True); done = []
    def gset(name, banks, lists, copies=(), rles=(), rles_addr=(), with_sprites=False):
        v = bytearray(0x4000); w = ex.win(banks)
        for a in lists: ex.graphics_list(v, w, a)
        for a in copies: ex.copies(v, w, a, name)
        for src, dst in rles: ex.rle(v, w, src, dst)
        for src in rles_addr: ex.rle_with_address(v, w, src)
        meta = dict(banks=list(banks), graphics_lists=list(lists), copies=list(copies), extra_rle=[list(x) for x in rles], rle_with_address=list(rles_addr))
        count_tiles(v, name, tiles, colours); return v, meta
    # Konami logo (p02:83EF with bank 22 at 0xA000): 6 rows of 21 chars from 0x40 at name 0x3907
    v, meta = gset('konami_logo', BANKS_22, [], rles_addr=[0xa737])
    names = bytearray(0x300)
    for r in range(6):
        for c in range(21): names[0x107 + 32 * r + c] = 0x40 + 21 * r + c
    for i in range(0x0a00, 0x0df0): v[i] = 0    # p02:8401 clears the logo colours...
    w22 = ex.win(BANKS_22); buf = bytearray(0x10000)
    for step in range(6):                        # ...and p02:8423 writes them back from six RLE images (p02:847B) at p02:8487[step]
        ex.rle(buf, w22, w22.word(0x847b + 2 * step), 0xc400, 'ram', 0xffff); dst = w22.word(0x8487 + 2 * step); v[dst:dst + 168] = buf[0xc400:0xc400 + 168]
    (folder / 'konami_logo').mkdir(parents=True, exist_ok=True); render_names(v, names, 32, 24).save(folder / 'konami_logo' / 'konami_logo.png')
    meta.update(code='p02:83EF-8422 and the final state of the fade p02:8423-847A', picture='konami_logo.png')
    write_set(folder / 'konami_logo', 'konami_logo', v, meta); done.append('konami_logo')
    # title, international BIOS (p30:8523-8574): list p22:A906, the RLE2 picture p30:887A 10x24 at 0xCA84, 12 bytes p30:89CA at 0xCA4A
    v, meta = gset('title_international', BANKS_22, [0xa906])
    buf = bytearray(0x10000); w30 = ex.win(BANKS_30); ex.rle2(buf, w30, 0x887a, 0xe800)
    names = bytearray(0x300); copy_rect(names, buf[0xe800:0xe800 + 240], 0xca84, 10, 24); names[0x4a:0x56] = w30.raw(0x89ca, 12)
    meta.update(code='p30:8523-8574', picture='title_initial_buffer.png', note='initial 0xCA00 buffer only; the logo animation of p30:85BD-870F is not replicated')
    write_set(folder / 'title_international', 'title_international', v, meta)
    render_names(v, names, 32, 24).save(folder / 'title_international' / 'title_initial_buffer.png'); done.append('title_international')
    # title, Japanese BIOS (p30:8575-8595)
    v, meta = gset('title_japanese', BANKS_22, [0xa8d8], copies=[0xa8f1], rles=[(0xaec6, 0x1800)], with_sprites=True)
    meta.update(code='p30:8575-8595'); write_set(folder / 'title_japanese', 'title_japanese', v, meta, True); done.append('title_japanese')
    # story character set (p30:8315-835D): list p22:B40B, copies at B40B+1 (via 0xCE00 buffer), RLE2 picture p22:B421 8x10 at 0xCA8B
    v, meta = gset('story_p22_B40B', BANKS_22, [0xb40b])
    w22 = ex.win(BANKS_22); buf = bytearray(0x10000); ex.rle2(buf, w22, 0xb421, 0xcd00); names = bytearray(0x300); copy_rect(names, buf[0xcd00:0xcd00 + 80], 0xca8b, 8, 10)
    meta.update(code='p30:8315-835D', picture='story_B421_buffer.png', note='copies list at 0xB40C (p00:4D17, through the 0xCE00 buffer) not applied; sequence picture 5 is drawn over this screen')
    write_set(folder / 'story_p22_B40B', 'story_p22_B40B', v, meta); render_names(v, names, 32, 24).save(folder / 'story_p22_B40B' / 'story_B421_buffer.png'); done.append('story_p22_B40B')
    # on-board computer (p26:730A-73DF): graphics 73E0/73F9, sprites p28:AF44/B0C2/B0F5, mirrors 7406, picture p28:A8C8/A935 + rectangles
    v, meta = gset('computer_room', BANKS_26, [0x73e0], copies=[0x73f9], rles=[(0xaf44, 0x1800), (0xb0c2, 0x1b40), (0xb0f5, 0x1e00)], with_sprites=True)
    w26 = ex.win(BANKS_26); ex.sprite_mirrors(v, w26, 0x7406)
    buf = bytearray(0x10000); names = bytearray(0x400)
    ex.rle(buf, w26, 0xa8c8, 0xcd00, 'ram', 0xffff); copy_rect(names, buf[0xcd00:0xcd00 + 13 * 20], 0xca26, 13, 20)
    ex.rle(buf, w26, 0xa935, 0xcd00, 'ram', 0xffff); copy_rect(names, buf[0xcd00:0xcd00 + 7 * 30], 0xcc01, 7, 30)
    for addr, ch in [(0xcbd0, 0x3d), (0xcbf0, 0x4a), (0xcbd1, 0x48), (0xcbf1, 0x55), (0xcbd6, 0x47), (0xcbf6, 0x54), (0xcbd9, 0x49), (0xcbf9, 0x56)]: names[addr - 0xca00] = ch
    copy_rect(names, w26.raw(0x76ff, 20), 0xca5a, 5, 4); copy_rect(names, w26.raw(0x77c3, 20), 0xcb7a, 5, 4)
    for table, dest, rows, cols in [(0x7573, 0xca42, 8, 4), (0x75fb, 0xcb42, 6, 3), (0x764b, 0xcbc6, 2, 10), (0x76b7, 0xcafa, 4, 4)]:
        copy_rect(names, w26.raw(w26.word(table + 2), rows * cols), dest, rows, cols)   # first displayed frame: (0 + 1) % 4
    meta.update(code='p26:730A-73DF, p26:7344-73AE, device frame 1 of p26:746C-74D7', picture='computer_room.png',
                note='static frame; counters, digits, map marks (0xCAC9/0xCACE/0xCAD3) and the sequence text are not drawn')
    write_set(folder / 'computer_room', 'computer_room', v, meta, True); render_names(v, names[:0x300], 32, 24).save(folder / 'computer_room' / 'computer_room.png'); done.append('computer_room')
    # assembled map after stage 9 (p26:7E00-7E1F): RLEs with address from p29:A000.. and list 0x7E23
    v, meta = gset('computer_assembled_map', BANKS_29, [0x7e23], rles_addr=[0xa000, 0xa0fc, 0xa105, 0xa1aa]); meta.update(code='p26:7E00-7E1F')
    write_set(folder / 'computer_assembled_map', 'computer_assembled_map', v, meta); done.append('computer_assembled_map')
    # radar after stage 3 (p27:81F4)
    v, meta = gset('radar_after_stage_3', BANKS_26, [0x8208]); meta.update(code='p27:81F4-8207'); write_set(folder / 'radar_after_stage_3', 'radar_after_stage_3', v, meta); done.append('radar_after_stage_3')
    # ending and state-9 sets, bank 29 at 0xA000 (p00:41E4)
    for name, lists, copies, rles, code in [
            ('state9_other_entrance_p29_BFB8', [0xbfb8], [0xbfc5], [], 'p27:8073-80A1'),
            ('ending_p29_A1D6', [0xa1d6], [0xa225], [], 'p27:8458'),
            ('ending_p29_A808', [0xa808], [0xa81b], [], 'p27:84BE'),
            ('ending_p29_ABBF', [0xabbf], [0xabd9], [], 'p27:8889'),
            ('ending_planet_p29_AB9A', [0xab9a], [0xabcc], [], 'p27:8A7F'),
            ('ending_p29_AACE', [0xaace], [], [], 'p27:8CDD'),
            ('ending_p29_B8BB', [0xb8bb], [], [(0xbbf3, 0x1e80)], 'p27:8DD9'),
            ('ending_p29_BD4D', [0xbd4d], [], [(0xbdca, 0x1de0)], 'p27:8E4C')]:
        v, meta = gset(name, BANKS_29, lists, copies, rles); meta.update(code=code, note='copies lists run through p00:4D17 (0xCE00 buffer) in the game; applied here as plain p00:4D1B copies')
        write_set(folder / name, name, v, meta, bool(rles)); done.append(name)
    (folder / 'screens.json').write_text(json.dumps(done, indent=2) + '\n'); return done


if __name__ == '__main__': extract()
