#!/usr/bin/env python3
"""Controller-driven CP0009 gameplay cadence verification in the actual FCEUmm core.
Video and native sound driver keep their original 60Hz refresh. Explicitly
selected gameplay rates are 30/40/60 logical frames per 60 video frames.
Neither screenshots nor cadence tests claim original MSX stage fidelity.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]
PACE=0x520

def tap(n, button):
    n.buttons[0]={button}; n.run(1); n.buttons[0]=set(); n.run(2)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--core',required=True);a=ap.parse_args()
    rom=(ROOT/'build/native/Nemesis_Legends_CP0013.nes').read_bytes()
    output=ROOT/'reports/cp0013';output.mkdir(parents=True,exist_ok=True)
    checks=[]
    def check(name, ok, **detail):
        checks.append(dict(name=name,passed=bool(ok),**detail))
        print(name, 'PASS' if ok else 'FAIL', detail,flush=True)
        if not ok: raise AssertionError(name)
    with NES(a.core,rom,True) as n:
        n.run(180);tap(n,3);n.run(8)
        check('starts_on_gameplay_with_slow30_without_qa',n.read(2,1)==b'\x01' and n.read(PACE,1)==b'\0' and n.read(0x53,1)==b'\0')
        check('visible_hud_identifies_30',n.read(0x380+29,2)==b'30')
        n.write(0x53,b'\1')  # test only: avoid actor collisions while measuring cadence
        for mode,expected in ((0,30),(1,40),(2,60)):
            if mode:
                tap(n,2)  # real SELECT edge changes speed; no RAM speed injection
            check('controller_changed_rate_to_'+str(expected),n.read(PACE,1)[0]==mode)
            start=int.from_bytes(n.read(0x1b,1),'little');f=n.read(0,1)[0]
            n.run(120)
            count=(n.read(0x1b,1)[0]-start)&255
            video=(n.read(0,1)[0]-f)&255
            check('video_120_frames_at_mode_'+str(expected),video==120,display_frames=video)
            check('logic_rate_'+str(expected)+'_hz',count==expected*2,logic_frames=count,video_frames=120)
            check('HUD_rate_'+str(expected),n.read(0x380+29,2)==str(expected).encode())
            check('no_missed_NMI_at_'+str(expected),n.read(0x1c,1)[0]==0)
            n.png(output/f'gameplay_{expected}hz.png')
        # Mode 2 -> mode 0 (cycle via SELECT once), and preserve one-frame A input
        # when it happens exactly on the skipped video frame of 30Hz mode.
        tap(n,2)
        check('mode_cycles_back_to30',n.read(PACE,1)==b'\0')
        for _ in range(3):
            if n.read(PACE+1,1)[0]%2==0:break
            n.run(1)
        else:raise AssertionError('unable to align skipped frame')
        n.write(0x27,b'\1')  # one preloaded power choice: QA fixture, not acquisition
        before=n.read(0x1b,1)[0]
        n.buttons[0]={8};n.run(1);n.buttons[0]=set()
        check('press_occurs_on_skipped_simulation_frame',n.read(0x1b,1)[0]==before)
        n.run(1)
        check('buffered_A_still_applies_power',n.read(0x22,1)==b'\1' and n.read(0x27,1)==b'\0')
        pos=n.read(7,2);tap(n,3);n.run(90)
        check('pause_freezes_simulation',n.read(2,1)==b'\2' and n.read(7,2)==pos)
        tap(n,2);check('select_changes_speed_while_paused',n.read(PACE,1)==b'\1' and n.read(2,1)==b'\2')
        tap(n,3);check('start_resumes_after_speed_adjustment',n.read(2,1)==b'\1')
    # Outside-QA accessibility measure: how much time before first life lost
    # with the player doing nothing. Compare at 30 vs 60 in actual cartridge.
    survival={}
    for mode in (0,2):
        with NES(a.core,rom,False) as n:
            n.run(180);tap(n,3);n.run(4)
            if mode==2:
                tap(n,2);tap(n,2)
            check('normal_play_without_injected_qa_'+str(mode),n.read(0x53,1)==b'\0')
            lives=n.read(0x24,1)[0]
            for frame in range(1200):
                n.run(1)
                if n.read(0x24,1)[0]<lives or n.read(2,1)[0]==3:
                    survival[str(mode)]=frame+1;break
            else:survival[str(mode)]=None
    check('first_collision_delayed_in_slow_mode',survival['0'] is not None and survival['2'] is not None and survival['0']>=int(survival['2']*1.6),survival_video_frames=survival)
    report=dict(checkpoint='CP0009',rom_sha256=hashlib.sha256(rom).hexdigest(),
        mode_selector='SELECT in gameplay or pause; 30 -> 40 -> 60 -> 30',
        video_rate='60 Hz independent of game logic',source_reference_mode=60,
        default='30Hz accessibility mode; non-original cadence',
        controller_real=True,first_collision_unassisted_frames=survival,
        QA_injection_only='invulnerability for deterministic cadence; one selected power-slot for edge test',
        checks=checks,passed=all(r['passed'] for r in checks))
    (output/'pacing_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(checks),'pacing checks')
if __name__=='__main__':main()
