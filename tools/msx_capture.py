#!/usr/bin/env python3
"""Run an MSX cartridge in openMSX (headless, C-BIOS) and capture VRAM, VDP
registers, CPU memory and screenshots at chosen moments.

Reference-capture tool for the asset catalogue: it reads the private originals
and writes captures to a private folder; nothing it writes belongs in git.

Plan (JSON file or string): a list of events, run in emulated time order.
  {"t": 21.0, "key": "SPACE", "hold": 0.1}       press a key (names in KEYS)
  {"t": 30.0, "poke": [[0xE000, 3], ...]}        write CPU memory
  {"t": 30.0, "every_frame_poke": [[addr, v]]}   keep writing every frame from t on
  {"t": 35.0, "dump": "name"}                    VRAM+regs+memory+screenshot
  {"t": 35.0, "shot": "name"}                    screenshot only
  {"t": 90.0, "exit": true}
Times are emulated seconds from power on (throttle off, so a minute of game
runs in a few seconds). Output per dump: <name>.vram (16 KiB), <name>.regs
(8 VDP registers + status), <name>.mem (64 KiB as the CPU sees it), <name>.png.

usage: msx_capture.py ROM PLAN OUTDIR [--machine C-BIOS_MSX1_JP] [--timeout 300]
"""
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, sys, tempfile

# MSX keyboard matrix (row, bit mask). Cursor keys and space are row 8.
KEYS = {
    'SPACE': (8, 0x01), 'HOME': (8, 0x02), 'INS': (8, 0x04), 'DEL': (8, 0x08),
    'LEFT': (8, 0x10), 'UP': (8, 0x20), 'DOWN': (8, 0x40), 'RIGHT': (8, 0x80),
    'F1': (6, 0x20), 'F2': (6, 0x40), 'F3': (6, 0x80), 'F4': (7, 0x01), 'F5': (7, 0x02),
    'ESC': (7, 0x04), 'TAB': (7, 0x08), 'STOP': (7, 0x10), 'BS': (7, 0x20),
    'SELECT': (7, 0x40), 'RETURN': (7, 0x80), 'SHIFT': (6, 0x01), 'CTRL': (6, 0x02),
    'GRAPH': (6, 0x04), 'CAPS': (6, 0x08), 'CODE': (6, 0x10),
    'M': (4, 0x04), 'N': (4, 0x08), 'Z': (5, 0x80), 'X': (5, 0x20),
}
for i, ch in enumerate('01234567'): KEYS[ch] = (0, 1 << i)
KEYS['8'] = (1, 0x01); KEYS['9'] = (1, 0x02)

TCL_HEAD = r'''
set throttle off
proc ll_hex {cmd n} { set out ""; for {set i 0} {$i < $n} {incr i} { append out [format "%02x" [eval $cmd $i]] }; return $out }
proc ll_dump {path} {
  set f [open "$path.vram" w]; fconfigure $f -translation binary
  puts -nonewline $f [debug read_block VRAM 0 16384]; close $f
  set regs ""; for {set r 0} {$r < 8} {incr r} { append regs [format "%02x" [vdpreg $r]] }
  append regs [format "%02x" [debug read "VDP status regs" 0]]
  set f [open "$path.regs" w]; puts $f $regs; close $f
  set f [open "$path.mem" w]; fconfigure $f -translation binary
  puts -nonewline $f [debug read_block memory 0 65536]; close $f
  screenshot -raw "$path.png"
}
proc ll_press {row mask secs} { keymatrixdown $row $mask; after time $secs "keymatrixup $row $mask" }
set ll_pokes {}
proc ll_frame {} { global ll_pokes; foreach p $ll_pokes { debug write memory [lindex $p 0] [lindex $p 1] }; after frame ll_frame }
after frame ll_frame
'''

def build_tcl(plan, out: pathlib.Path) -> str:
    lines = [TCL_HEAD]
    for ev in sorted(plan, key=lambda e: e['t']):
        t = '%.3f' % ev['t']
        if 'key' in ev:
            row, mask = KEYS[ev['key'].upper()]
            lines.append('after time %s {ll_press %d %d %s}' % (t, row, mask, ev.get('hold', 0.1)))
        if 'poke' in ev:
            body = '; '.join('debug write memory %d %d' % (a, v) for a, v in ev['poke'])
            lines.append('after time %s {%s}' % (t, body))
        if 'every_frame_poke' in ev:
            items = ' '.join('{%d %d}' % (a, v) for a, v in ev['every_frame_poke'])
            lines.append('after time %s {lappend ll_pokes %s}' % (t, items))
        if 'dump' in ev:
            lines.append('after time %s {ll_dump "%s"}' % (t, (out / ev['dump']).as_posix()))
        if 'shot' in ev:
            lines.append('after time %s {screenshot -raw "%s.png"}' % (t, (out / ev['shot']).as_posix()))
        if ev.get('exit'):
            lines.append('after time %s exit' % t)
    if not any(ev.get('exit') for ev in plan):
        lines.append('after time %.3f exit' % (max(e['t'] for e in plan) + 0.5))
    return '\n'.join(lines) + '\n'

def run(rom, plan, out, machine='C-BIOS_MSX1_JP', timeout=300, extra_tcl=''):
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='msxcap-') as tmp:
        script = pathlib.Path(tmp) / 'plan.tcl'
        script.write_text(build_tcl(plan, out) + extra_tcl)
        cmd = ['xvfb-run', '-a', 'openmsx', '-machine', machine, '-cart', str(rom), '-script', str(script)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    noise = ('sequencer', 'ALSA lib')
    errors = [l for l in (r.stdout + r.stderr).splitlines()
              if 'error' in l.lower() and not any(n in l for n in noise)]
    return errors

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rom'); ap.add_argument('plan'); ap.add_argument('out')
    ap.add_argument('--machine', default='C-BIOS_MSX1_JP'); ap.add_argument('--timeout', type=int, default=300)
    a = ap.parse_args()
    plan = json.loads(pathlib.Path(a.plan).read_text() if os.path.isfile(a.plan) else a.plan)
    errors = run(a.rom, plan, a.out, a.machine, a.timeout)
    for e in errors: print(e, file=sys.stderr)
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
