#!/usr/bin/env python3
"""CP0007 actual-cartridge title tests plus bounded NMI timing. No hardware claim."""
from __future__ import annotations
import argparse, hashlib, json, pathlib
import numpy as np
from PIL import Image
from nes_test_host import NES
from test_vblank_budget import Counter6502
ROOT=pathlib.Path(__file__).resolve().parents[1]
OPTS={b'fceumm_overscan':b'disabled',b'fceumm_overscan_v_top':b'0',b'fceumm_overscan_v_bottom':b'0'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--core',required=True);a=ap.parse_args()
    rom=(ROOT/'build/native/Nemesis_Legends_CP0016.nes').read_bytes()
    out=ROOT/'reports/cp0016';out.mkdir(parents=True,exist_ok=True)
    checks=[];timing=[]
    def check(name,passed,**kw):
        row=dict(name=name,passed=bool(passed),**kw);checks.append(row)
        print(name, bool(passed),kw,flush=True)
        if not passed:raise AssertionError(name)
    def tap(n,*buttons):
        n.buttons[0]=set(buttons);n.run(1);n.buttons[0]=set();n.run(2)
    def state(n):return list(n.read(0x7e0,16))
    def peak(n):return int(np.max(np.abs(np.frombuffer(n.samples[-4000:],dtype='<i2').astype(np.int32))))
    with NES(a.core,rom,True,OPTS) as n:
        observed=[];row_order=[];previous=-1
        for f in range(100):
            n.run(1);s=state(n)
            if n.read(0x18,1)==b'\1' and s[4]!=previous:
                previous=s[4];observed.append(dict(frame=f+1,step=s[4],tick=s[5]))
                if 3<=s[4]<=10:row_order.append(s[9])
                n.png(out/('entrance_step_%02d.png'%s[4]))
        check('reveal_all_eight_rows_bottom_up',row_order==list(reversed(range(8))),rows=row_order)
        check('entrance_ready_after_13_acknowledged_events',state(n)[4]==13 and state(n)[8]==0 and state(n)[2]==0)
        check('normal_boot_no_QA_assistance',n.read(0x53,1)==b'\0')
        check('no_title_hardware_sprites',all(v>=240 for v in n.read(0x200,256)[::4]))
        check('native_resolution',n.picture[1:3]==(256,240))
        n.png(out/'title.png');first=np.asarray(Image.open(out/'title.png')).copy()
        n.run(180);n.png(out/'title_idle.png');second=np.asarray(Image.open(out/'title_idle.png'))
        mask=np.ones((240,256),bool);mask[152:216,48:208]=False
        check('background_unchanged_during_idle',np.array_equal(first[mask],second[mask]))
        check('panel_center_is_opaque_black',np.all(second[182:188,57:199]==0))
        check('title_audio_is_native_and_audible',peak(n)>100)
        tap(n,4);check('up_wraps_to_options',state(n)[1]==1)
        tap(n,5);check('down_wraps_to_start',state(n)[1]==0)
        tap(n,4,5);check('opposite_directions_cancel',state(n)[1]==0)
        n.buttons[0]={5};n.run(1);one=state(n)[1];n.run(14);before=state(n)[1];n.run(1);after=state(n)[1]
        n.buttons[0]=set();n.run(2)
        check('held_repeat_15_frames_then_moves',one==1 and before==1 and after==0)
        tap(n,2);tap(n,8);check('options_is_functional',state(n)[:2]==[1,0])
        n.png(out/'options_on.png');tap(n,8);n.run(180)
        check('mute_silences_existing_tone',state(n)[3]==1 and n.read(0x1a,1)==b'\0' and peak(n)<50)
        n.png(out/'options_off.png');tap(n,8);n.run(80)
        check('unmute_restores_real_APU',state(n)[3]==0 and n.read(0x1a,1)==b'\1' and peak(n)>100)
        tap(n,0);check('B_returns_to_root_options_selection',state(n)[:2]==[0,1])
        tap(n,5);tap(n,3,8);n.run(60)
        check('simultaneous_confirm_starts_once_without_pause',n.read(2,1)==b'\1' and n.read(0x24,1)==b'\3' and n.read(0x1d,1)==b'\1')
        check('no_title_requests_leak_into_game',state(n)[2]==0)
        n.png(out/'gameplay.png');x=n.read(0x20,1)[0]
        n.buttons[0]={7};n.run(6);n.buttons[0]=set()
        check('movement_preserved',n.read(0x20,1)[0]>x)
        tap(n,3);n.run(20);check('pause_preserved',n.read(2,1)==b'\2')
        tap(n,3);check('resume_preserved',n.read(2,1)==b'\1')
        # QA-only forced game-over state tests return and stale HUD cleanup.
        n.write(2,b'\3');n.write(0x25,b'\1');n.write(0x24,b'\0');n.write(0x5a,b'\1')
        n.run(120)
        check('game_over_reinitializes_title_and_clears_stale_requests',n.read(2,1)==b'\0' and n.read(9,1)==b'\0' and n.read(0x5a,1)==b'\0' and n.read(0x76,1)==b'\0' and state(n)[8]==0,qa='forced game-over and pending HUD')
        n.png(out/'return_to_title.png');returned=np.asarray(Image.open(out/'return_to_title.png'))
        check('return_title_art_preserved',np.array_equal(returned[mask],first[mask]),qa='forced game-over')
        n.run(1200);check('long_idle_stays_in_title_without_error',n.read(2,1)==b'\0' and state(n)[15]==0)
        n.lib.retro_reset();n.run(120);check('reset_reboots_title_cleanly',n.read(2,1)==b'\0' and state(n)[8]==0 and state(n)[15]==0)
    # Check early confirm in each individual entrance event, no RAM writes.
    for target_step in range(13):
        with NES(a.core,rom,False,OPTS) as n:
            for f in range(120):
                n.run(1)
                if n.read(0x18,1)==b'\1' and state(n)[4]==target_step:break
            else:raise AssertionError('entrance step not observed')
            n.buttons[0]={3};n.run(90)
            check('early_start_step_%02d_does_not_start_game'%target_step,n.read(2,1)==b'\0' and state(n)[8]==0 and state(n)[7]==1)
            n.buttons[0]=set();n.run(3);tap(n,3);n.run(30)
            check('early_start_step_%02d_requires_new_press'%target_step,n.read(2,1)==b'\1')
    with NES(a.core,rom,True,OPTS) as n:
        n.run(100);tap(n,4);tap(n,8);tap(n,8);tap(n,0);tap(n,5);tap(n,3);n.run(120)
        check('mute_persists_into_game',n.read(2,1)==b'\1' and state(n)[3]==1 and n.read(0x1a,1)==b'\0' and peak(n)<50)
    # Every legal NMI command, row, submenu and mute combination. Execute
    # production bytes with worst OAM DMA; no DMC DMA assumed during PPU work.
    for command in range(7):
        for row in (range(8) if command==1 else [0]):
            for page in range(2):
                for muted in range(2):
                    for dim in (range(2) if command==2 else [0]):
                        c=Counter6502(rom);c.m[0x8000:0xa000]=rom[16+9*8192:16+10*8192]
                        c.m[1]=c.m[0x18]=1;c.m[2]=0;c.m[0x1a]=0
                        c.m[0x7e0]=page;c.m[0x7e2]=command;c.m[0x7e3]=muted;c.m[0x7e9]=row;c.m[0x7ea]=dim
                        c.run();last=max(t for _,t in c.video)
                        timing.append(dict(command=command,row=row,page=page,muted=muted,dim=dim,last_video_write_cycle=last,passed=last<2273))
                        if command==1:assert c.m[0x5104]==1
                        assert c.m[0x7e2]==0
    check('all_legal_title_NMI_paths_fit',all(t['passed'] for t in timing),cases=len(timing),worst=max(t['last_video_write_cycle'] for t in timing))
    for invalid_cmd,invalid_row in [(255,0),(1,8),(1,255)]:
        c=Counter6502(rom);c.m[0x8000:0xa000]=rom[16+9*8192:16+10*8192]
        c.m[1]=c.m[0x18]=1;c.m[0x7e2]=invalid_cmd;c.m[0x7e9]=invalid_row
        c.run();check('invalid_command_or_row_rejected_%d_%d'%(invalid_cmd,invalid_row),c.m[0x7ef]==1 and c.m[0x7e2]==0)
    report=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,entrance=observed,timing=timing,
        passed=all(c['passed'] for c in checks),physical_hardware_tested=False,
        scope='Title/control integration and bounded NTSC timing, not full-game validation.',
        timing_assumptions=['Worst OAM DMA 514 cycles','No DMC DMA during video transfers','Audio driver runs after video writes'])
    (out/'title_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    Image.open(out/'title.png').resize((768,720),Image.Resampling.NEAREST).save(out/'title_3x.png')
    print('PASS',len(checks), 'title checks')
if __name__=='__main__':main()
