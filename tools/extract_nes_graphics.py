#!/usr/bin/env python3
"""Reproducible tile-graphics extraction from the six hash-verified NES/Famicom reference ROMs.
CHR-ROM games (Gradius JP/US mapper 3, Gradius II mapper 25): every 8 KiB CHR bank is dumped.
CHR-RAM games (Salamander FC mapper 73, Life Force mapper 2): graphics live inside PRG and are
located from code evidence found by byte signature (offsets are recorded in the report):
  * PPU RLE decoder (Life Force $F0A7, Salamander $ECC5): stream = [ppu_lo, ppu_hi] header, then
    $FF end, $7F new header, $80|n = n literal bytes, n<$7F = repeat next byte n times.
  * Tile-stream table (routine $EC97 / $E8C1): parallel tables of source pointer, PPU destination
    and tile count; one 16-byte tile per frame is copied through the $0700 NMI buffer.
  * Salamander RAM RLE decoder ($F7C8): headerless variant of the same grammar into WRAM $7000;
    the decoded blocks are exactly what the tile-stream table reads.
  * Raw-tile heuristic over everything not covered above (low confidence, dictionary-excluded).
Outputs under assets/nes/<slug>/chr/ stay local (gitignored); only reports/nes_extraction.json is public
and it never contains ROM bytes. Python 3.10+, numpy, Pillow.
"""
from __future__ import annotations
import collections, hashlib, json, pathlib, re, sys
import numpy as np
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from source_audit import parse_ines
ROOT = pathlib.Path(__file__).resolve().parents[1]
CHR_ROM = ['gradius_nes_jp', 'gradius_nes_us', 'gradius2_fc']
CHR_RAM = ['salamander_fc', 'lifeforce_nes_us', 'lifeforce_nes_us_rev1']
BANK = 16384
GREY = np.array([0, 85, 170, 255], np.uint8); BITS = np.arange(7, -1, -1)
POP = np.array([bin(i).count('1') for i in range(256)], np.int32)
REV = bytes(int(f'{x:08b}'[::-1], 2) for x in range(256))
# PPU RLE decoder body: CMP #$FF/BEQ, CMP #$7F/BEQ, TAY, BPL, AND #$7F, STA $02, LDY #1, LDA ($00),Y, STA $2007
SIG_PPU_RLE = re.compile(rb'\xc9\xff\xf0.\xc9\x7f\xf0.\xa8\x10.\x29\x7f\x85\x02\xa0\x01\xb1\x00\x8d\x07\x20', re.S)
# Tile-stream routine head: LDA cnt,Y; STA $0D; TYA; ASL; TAY; LDA dst,Y; STA $0E; LDA dst+1,Y; STA $0F; LDA #0; STA $0B; LDA src,Y; STA $08; ...
SIG_TILE_TABLE = re.compile(rb'\xb9(..)\x85\x0d\x98\x0a\xa8\xb9(..)\x85\x0e\xb9..\x85\x0f\xa9\x00\x85\x0b\xb9(..)\x85\x08\xb9..\x85\x09', re.S)
# RAM RLE table loader: LDA tbl,Y; STA $00; LDA tbl+1,Y; STA $01; LDA #0; STA $08; LDA #hi; STA $09; JMP decoder
SIG_RAM_RLE = re.compile(rb'\xb9(..)\x85\x00\xb9..\x85\x01\xa9\x00\x85\x08\xa9(.)\x85\x09\x4c(..)', re.S)
# Manual visual review of rendered sheets (2026-10-27); only applied when the offset is found again.
VISUAL = {'lifeforce_nes_us': {0x4001: 'font, Konami logo and title lettering', 0x3C6B: 'planet picture', 0x88D0: 'HUD font and power-up labels',
                               0x4FAA: 'organic terrain', 0x16DF: 'scenery silhouettes and ship sprites', 0x1D3F: 'sprite fragments',
                               0x1067: 'large striped boss sprite', 0x131CD: 'large creature sprite'},
          'salamander_fc': {0x4000: 'Salamander title logo with kana and Konami mark', 0x88BD: 'HUD font and power-up labels', 0x3244: 'ship and enemy sprites'}}

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def sheet(data: bytes, per_row=16, scale=2) -> Image.Image:
    n = len(data) // 16; rows = max(1, (n + per_row - 1) // per_row)
    img = np.zeros((rows * 8, per_row * 8), np.uint8)
    if n:
        t = np.frombuffer(data[:n * 16], np.uint8).reshape(n, 16)
        pix = GREY[((t[:, :8, None] >> BITS) & 1) | (((t[:, 8:, None] >> BITS) & 1) << 1)]
        for i in range(n): img[(i // per_row) * 8:(i // per_row) * 8 + 8, (i % per_row) * 8:(i % per_row) * 8 + 8] = pix[i]
    im = Image.fromarray(img, 'L'); return im.resize((im.width * scale, im.height * scale), Image.NEAREST)

def features(data: bytes) -> dict:
    """Pixel-level plausibility statistics of 16-byte 2bpp tiles (calibrated on the CHR-ROM games)."""
    t = np.frombuffer(data[:len(data) // 16 * 16], np.uint8).reshape(-1, 16); n = len(t)
    p = ((t[:, :8, None] >> BITS) & 1) | (((t[:, 8:, None] >> BITS) & 1) << 1)
    g = np.zeros((n, 10, 10), np.int8); g[:, 1:9, 1:9] = p
    same = (g[:, 1:9, 1:9] == g[:, 0:8, 1:9]) | (g[:, 1:9, 1:9] == g[:, 2:10, 1:9]) | (g[:, 1:9, 1:9] == g[:, 1:9, 0:8]) | (g[:, 1:9, 1:9] == g[:, 1:9, 2:10])
    nz = p != 0; c = np.bincount(p.ravel(), minlength=4) / p.size
    ncol = np.array([len(np.unique(x)) for x in p.reshape(n, -1)])
    return dict(tiles=n, zero_ff_fraction=float(np.isin(t, [0, 255]).mean()),
                h_transitions=float((p[:, :, 1:] != p[:, :, :-1]).sum((1, 2)).mean()),
                v_transitions=float((p[:, 1:, :] != p[:, :-1, :]).sum((1, 2)).mean()),
                min_colour_share=float(c[1:].min()), colour3_share=float(c[3]), mean_colours=float(ncol.mean()),
                blank_edge_fraction=float(((p == 0).all(2).any(1) | (p == 0).all(1).any(1)).mean()),
                speckle=float((nz & ~same).sum() / max(1, nz.sum())))

def raw_gate(f: dict) -> bool:
    return (f['h_transitions'] <= 17.5 and f['v_transitions'] <= 21 and f['zero_ff_fraction'] >= 0.25 and f['min_colour_share'] <= 0.13
            and f['blank_edge_fraction'] >= 0.5 and f['colour3_share'] <= 0.4 and f['mean_colours'] <= 3.6 and f['speckle'] <= 0.25)

def parse_rle(prg: bytes, p: int, limit: int, header=True):
    """Konami RLE. Returns (end_offset, [(ppu_or_ram_address, bytes)...]) or None when not a valid stream."""
    segs = []; out = bytearray(); addr = 0
    if header:
        if p + 2 > limit: return None
        addr = prg[p] | prg[p + 1] << 8; p += 2
        if addr >> 8 >= 0x40: return None
    while True:
        if p >= limit: return None
        op = prg[p]
        if op == 0xFF:
            if out: segs.append((addr, bytes(out)))
            return p + 1, segs
        if header and op == 0x7F:
            if out: segs.append((addr, bytes(out))); out = bytearray()
            if p + 3 > limit: return None
            addr = prg[p + 1] | prg[p + 2] << 8; p += 3
            if addr >> 8 >= 0x40: return None
            continue
        if op in (0, 0x80): return None          # degenerate 255-byte forms never emitted by the encoder
        if op & 0x80:
            n = op & 0x7F
            if p + 1 + n > limit: return None
            out += prg[p + 1:p + 1 + n]; p += 1 + n
        else:
            if p + 2 > limit: return None
            out += bytes([prg[p + 1]]) * op; p += 2
        if len(out) > 0x4000: return None

class Game:
    def __init__(self, slug: str, src: dict):
        self.slug = slug; rom = (ROOT / src['path']).read_bytes()
        if sha(rom) != src['sha256']: raise ValueError(f'{slug}: ROM hash mismatch')
        self.h = parse_ines(rom); self.prg = rom[self.h['prg_offset']:self.h['prg_offset'] + self.h['prg_bytes']]
        self.chr = rom[self.h['chr_offset']:self.h['chr_offset'] + self.h['chr_bytes']]
        self.nbanks = len(self.prg) // BANK; self.out = ROOT / 'assets/nes' / slug / 'chr'; self.out.mkdir(parents=True, exist_ok=True)
        self.words = collections.Counter(self.prg[i] | self.prg[i + 1] << 8 for i in range(len(self.prg) - 1))
    def cpu(self, off: int) -> int: return (0xC000 if off // BANK == self.nbanks - 1 else 0x8000) + off % BANK
    def fixed_off(self, addr: int) -> int: return (self.nbanks - 1) * BANK + addr - 0xC000
    def word_at(self, off: int) -> int: return self.prg[off] | self.prg[off + 1] << 8

    # --- 1. PPU RLE streams -------------------------------------------------------------------------
    def scan_ppu_streams(self):
        found = []
        for bank in range(self.nbanks):
            b0 = bank * BANK; limit = b0 + BANK
            valid = {p: r for p in range(b0, limit - 3) if (r := parse_rle(self.prg, p, limit)) and sum(len(s) for _, s in r[1]) >= 16}
            ref = {p for p in valid if self.words.get(self.cpu(p), 0) > 0}
            p = b0; prev_end = -1
            while p < limit - 3:
                if p in valid:
                    end, segs = valid[p]
                    if p not in ref and any(p < q < end for q in ref): p += 1; continue   # prefer a pointer-referenced start
                    found.append(dict(start=p, end=end, segs=segs, referenced=p in ref, bank=bank, chained=p == prev_end or p == b0)); p = end; prev_end = end
                else: p += 1
        return found
    def judge_ppu(self, x: dict):
        chr_ = b''.join(s[:0x2000 - a] for a, s in x['segs'] if a < 0x2000); kinds = sorted({'chr' if a < 0x2000 else 'nametable' if a < 0x3000 else 'palette' if a >= 0x3F00 else 'other' for a, _ in x['segs']})
        if 'chr' not in kinds: return 'not_pattern_table', kinds, None
        if x['end'] - x['start'] < 32: return 'compressed_too_short', kinds, None
        if len(chr_) < 128: return 'decoded_too_small', kinds, None
        if any(a % 16 for a, _ in x['segs'] if a < 0x2000) or len(chr_) % 16: return 'not_tile_aligned', kinds, None
        f = features(chr_)
        if f['zero_ff_fraction'] < 0.2: return 'few_00_ff_bytes', kinds, f
        if f['v_transitions'] / max(1, f['h_transitions']) < 0.65: return 'vertical_stripes', kinds, f
        if len(set(chr_)) < 16: return 'low_byte_variety', kinds, f
        return 'accepted', kinds, f

    # --- 2. tile-stream table ----------------------------------------------------------------------
    def tile_table(self):
        m = SIG_TILE_TABLE.search(self.prg)
        if not m: return None
        cnt, dst, src = (int.from_bytes(m.group(i), 'little') for i in (1, 2, 3)); n = (dst - src) // 2
        if n <= 0 or (cnt - dst) // 2 != n or src < 0xC000: return None
        entry = self.cpu(m.start()); callers = collections.defaultdict(set)
        for i in range(len(self.prg) - 4):
            if self.prg[i] == 0xA0 and self.prg[i + 2] == 0x20 and entry - 8 <= self.word_at(i + 3) <= entry: callers[self.prg[i + 1]].add(i // BANK)
        entries = []
        for y in range(n):
            entries.append(dict(index=y, src=self.word_at(self.fixed_off(src) + 2 * y), ppu=self.word_at(self.fixed_off(dst) + 2 * y),
                                tiles=self.prg[self.fixed_off(cnt) + y], caller_banks=sorted(callers.get(y, []))))
        return dict(routine_prg_offset=m.start(), routine_cpu=entry, src_table=src, dst_table=dst, count_table=cnt, entries=entries)

    # --- 3. RAM RLE blocks (Salamander WRAM staging) ------------------------------------------------
    def ram_streams(self, expected_sizes: set):
        out = []
        for m in SIG_RAM_RLE.finditer(self.prg):
            tbl = int.from_bytes(m.group(1), 'little'); ram_hi = m.group(2)[0]; dec = int.from_bytes(m.group(3), 'little')
            if not 0xC000 <= tbl < 0x10000 or not 0x60 <= ram_hi <= 0x7F: continue
            t = self.fixed_off(tbl); ptrs = []
            while t + 1 < len(self.prg) and len(ptrs) < 16:   # the table ends where its first fixed-bank target begins
                a = self.word_at(t); fixed = [p for p in ptrs + [a] if p >= 0xC000]
                if a < 0x8000 or (fixed and t >= self.fixed_off(min(fixed))): break
                ptrs.append(a); t += 2
            for i, a in enumerate(ptrs):
                if a >= 0xC000: continue   # fixed-bank entry: $FF empty stream in practice
                for bank in range(self.nbanks - 1):
                    o = bank * BANK + a - 0x8000; r = parse_rle(self.prg, o, (bank + 1) * BANK, header=False)
                    if not r or len(r[1]) != 1 or len(r[1][0][1]) < 256: continue
                    data = r[1][0][1]; size16 = (len(data) + 15) // 16 * 16; f = features(data)
                    exact = size16 in expected_sizes
                    if not exact and f['zero_ff_fraction'] < 0.15: continue
                    out.append(dict(table=tbl, table_index=i, decoder_cpu=dec, ram=ram_hi << 8, cpu=a, bank=bank, start=o, end=r[0], data=data,
                                    confidence='high' if exact else 'medium', size_matches_tile_table=exact, features=f))
        return out

    # --- 4. raw heuristic ------------------------------------------------------------------------------
    def raw_runs(self, covered: np.ndarray, w=8):
        nt = len(self.prg) // 16; ok = np.zeros(nt, bool)
        for t in range(nt - w + 1):
            a = t * 16
            if covered[a:a + w * 16].any(): continue
            if raw_gate(features(self.prg[a:a + w * 16])): ok[t:t + w] = True
        runs = []; t = 0
        while t < nt:
            if ok[t]:
                u = t
                while u < nt and ok[u]: u += 1
                f = features(self.prg[t * 16:u * 16])
                if raw_gate(f): runs.append((t * 16, u * 16, f))
                t = u
            else: t += 1
        return runs

def flip_h(t: bytes) -> bytes: return bytes(REV[x] for x in t)
def flip_v(t: bytes) -> bytes: return t[7::-1] + t[15:7:-1]
def canonical(t: bytes) -> bytes:
    hv = flip_v(flip_h(t)); return min(t, flip_h(t), flip_v(t), hv)

class Dictionary:
    def __init__(self): self.tiles = {}; self.refs = collections.defaultdict(list); self.per_game = collections.defaultdict(lambda: dict(occ=0, exact=set(), flip=set()))
    def add(self, slug: str, unit: str, data: bytes):
        exact = set(); flip = set(); g = self.per_game[slug]
        for i in range(0, len(data) // 16 * 16, 16):
            t = data[i:i + 16]; h = sha(t); self.tiles.setdefault(h, t); self.refs[h].append([slug, unit, i // 16])
            exact.add(h); flip.add(canonical(t)); g['occ'] += 1
        g['exact'] |= exact; g['flip'] |= flip
        return dict(tile_occurrences=len(data) // 16, exact_unique=len(exact), flip_unique=len(flip))

def extract(root=ROOT):
    sel = json.loads((root / 'manifests/selected_sources.json').read_text(encoding='utf-8'))
    d = Dictionary(); report = {}
    for slug in CHR_ROM + CHR_RAM:
        g = Game(slug, sel[slug]); r = dict(mapper=g.h['mapper'], prg_bytes=len(g.prg), chr_bytes=len(g.chr), chr_type='CHR-ROM' if g.chr else 'CHR-RAM')
        if g.chr:
            banks = []
            for i in range(0, len(g.chr), 8192):
                bank = g.chr[i:i + 8192]; name = f'bank_{i // 8192:02d}'
                (g.out / f'{name}.bin').write_bytes(bank); sheet(bank).save(g.out / f'{name}.png')
                banks.append(dict(bank=i // 8192, sha256=sha(bank), **d.add(slug, name, bank)))
            r['banks'] = banks
        else:
            r.update(extract_chr_ram(g, d));
        pg = d.per_game[slug]; r['tiles'] = dict(occurrences=pg['occ'], exact_unique=len(pg['exact']), flip_unique=len(pg['flip']), flip_duplicates=len(pg['exact']) - len(pg['flip']))
        report[slug] = r
    (root / 'assets/nes/nes_tile_dictionary.bin').write_bytes(b''.join(d.tiles.values()))
    (root / 'assets/nes/nes_tile_references.json').write_text(json.dumps(dict(d.refs), separators=(',', ':')), encoding='utf-8')
    flips = {canonical(t) for t in d.tiles.values()}
    cross = collections.Counter(len({ref[0] for ref in refs}) for refs in d.refs.values())
    summary = dict(schema=1, source_manifest='manifests/selected_sources.json', games=report,
                   aggregate=dict(tile_occurrences=sum(len(v) for v in d.refs.values()), exact_unique=len(d.tiles), flip_unique=len(flips),
                                  flip_duplicates=len(d.tiles) - len(flips), dictionary_bytes=16 * len(d.tiles),
                                  tiles_shared_by_n_games=dict(sorted(cross.items())),
                                  dictionary_scope='CHR-ROM banks plus high/medium-confidence CHR-RAM regions; low-confidence raw candidates excluded'),
                   limitations=['CHR-ROM banks are raw 8 KiB dumps; which 1 KiB/2 KiB slices a mapper actually maps together is not reconstructed.',
                                'CHR-RAM regions come from decoder grammar, pointer tables and plausibility heuristics, not from emulation traces; completeness is not claimed.',
                                'Tiles written to CHR-RAM by code other than the identified RLE decoders and tile-stream table (e.g. computed or nametable-only updates) are not covered.',
                                'Raw-heuristic candidates are unconfirmed and excluded from the dictionary; some may be map or object data.',
                                'Tile identity is raw 2bpp pixel data only: no palette, attribute or metatile equivalence is implied.',
                                'Konami RLE streams that write nametables or palettes are counted but not extracted.'])
    (root / 'reports/nes_extraction.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: (v if k != 'games' else {s: {kk: vv for kk, vv in gv.items() if kk != 'regions'} for s, gv in v.items()}) for k, v in summary.items()}, indent=2))
    return summary

def extract_chr_ram(g: Game, d: Dictionary) -> dict:
    regions = []; covered = np.zeros(len(g.prg), bool); rejected = collections.Counter(); other = collections.Counter(); evidence = {}
    m = SIG_PPU_RLE.search(g.prg)
    evidence['ppu_rle_decoder'] = dict(prg_offset=m.start(), cpu=g.cpu(m.start())) if m else None
    def add(method, start, end, data, confidence, **meta):
        reg = dict(method=method, prg_offset=start, prg_length=end - start, bank=start // BANK, cpu=g.cpu(start),
                   decoded_bytes=len(data) // 16 * 16, confidence=confidence, decoded_sha256=sha(data), **meta)
        if start in VISUAL.get(g.slug, {}): reg['visual_review'] = VISUAL[g.slug][start]
        reg['plausibility'] = {k: round(v, 3) for k, v in features(data).items() if k != 'tiles'}
        covered[start:end] = True; regions.append((reg, data))
    for x in g.scan_ppu_streams():
        verdict, kinds, f = g.judge_ppu(x)
        if verdict != 'accepted':
            (other if verdict == 'not_pattern_table' else rejected)[verdict if verdict != 'not_pattern_table' else '+'.join(kinds)] += 1; continue
        chr_ = b''.join(s[:0x2000 - a] for a, s in x['segs'] if a < 0x2000); anchored = x['referenced'] or x['chained']
        conf = 'high' if anchored and len(chr_) >= 256 else 'medium' if anchored else 'low'
        add('konami_rle_ppu_stream', x['start'], x['end'], chr_, conf, ppu_destinations=[a for a, _ in x['segs'] if a < 0x2000],
            pointer_referenced=x['referenced'], contiguous_with_previous_stream=x['chained'], clipped_at_2000=any(a + len(s) > 0x2000 for a, s in x['segs'] if a < 0x2000),
            evidence='valid Konami RLE grammar, FF-terminated inside its 16 KiB bank, tile-aligned destination, plausible pixels')
    tab = g.tile_table(); expected = set()
    if tab:
        evidence['tile_stream_table'] = {k: v for k, v in tab.items() if k != 'entries'}; evidence['tile_stream_entries'] = tab['entries']
        for e in tab['entries']:
            if 0x8000 <= e['src'] < 0xC000:
                for bank in e['caller_banks'] or range(g.nbanks - 1):
                    o = bank * BANK + e['src'] - 0x8000; data = g.prg[o:o + 16 * e['tiles']]
                    if covered[o:o + len(data)].any(): continue
                    f = features(data); conf = 'high' if e['caller_banks'] else 'medium'
                    add('tile_stream_table_raw', o, o + len(data), data, conf, ppu_destinations=[e['ppu']], table_index=e['index'], bank_from_caller=bool(e['caller_banks']),
                        plausibility_gate=raw_gate(f), evidence='entry of the per-tile NMI-buffer copy table; bank resolved from LDY #n; JSR callers' if e['caller_banks'] else 'table entry, bank unresolved')
            elif 0x6000 <= e['src'] < 0x8000:
                size = e['tiles']; nxt = e['src'] + 16 * e['tiles']
                for f2 in tab['entries']:
                    if f2['src'] == nxt: size += f2['tiles']; nxt += 16 * f2['tiles']
                expected.add(size * 16)
        if expected: evidence['wram_block_sizes_expected'] = sorted(expected)
    for s in g.ram_streams(expected):
        if covered[s['start']:s['end']].any(): continue
        add('konami_rle_ram_stream', s['start'], s['end'], s['data'], s['confidence'], ram_destination=s['ram'], decoder_cpu=s['decoder_cpu'], pointer_table_cpu=s['table'],
            table_index=s['table_index'], size_matches_tile_table=s['size_matches_tile_table'], clipped_at_2000=False,
            evidence='headerless Konami RLE pointed to by the per-stage WRAM table; decoded size equals the tile-stream table block' if s['size_matches_tile_table'] else 'headerless Konami RLE from the WRAM table; size not matched')
    for a, e, f in g.raw_runs(covered):
        add('raw_heuristic', a, e, g.prg[a:e], 'low', evidence='uncovered PRG run whose 8-tile windows all pass the pixel plausibility gate; unconfirmed')
    regions.sort(key=lambda r: r[0]['prg_offset']); out = []
    for n, (reg, data) in enumerate(regions):   # name, hash and write in PRG order; low confidence stays out of the dictionary
        reg = dict(region=f'region_{n:02d}', **reg)
        reg.update(d.add(g.slug, reg['region'], data) if reg['confidence'] != 'low' else dict(tile_occurrences=len(data) // 16))
        (g.out / f"{reg['region']}.bin").write_bytes(data); sheet(data).save(g.out / f"{reg['region']}.png"); out.append(reg)
    regions = out; conf = collections.Counter(r['confidence'] for r in regions)
    return dict(evidence=evidence, regions=regions, region_count=len(regions), regions_by_confidence=dict(conf),
                region_tiles_by_confidence={c: sum(r['tile_occurrences'] for r in regions if r['confidence'] == c) for c in conf},
                rejected_rle_candidates=dict(rejected), non_pattern_rle_candidates=dict(other),
                confidence_notes=['high: decoder grammar plus a code anchor (pointer reference, bank start, back-to-back stream, caller bank or exact size match).',
                                  'medium: grammar-valid and plausible but without a second anchor, or a table entry whose bank could not be resolved.',
                                  'low: raw heuristic only; written to disk for inspection, excluded from tile statistics and the dictionary.'])

if __name__ == '__main__': extract()
