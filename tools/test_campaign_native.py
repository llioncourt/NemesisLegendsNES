#!/usr/bin/env python3
"""Compile and execute the native campaign module in a real NES core.
These are event/progression unit tests, not full-game or gameplay tests.
The expected routes are explicit source-derived fixtures, not a replay.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, pathlib, shutil, subprocess
from nes_test_host import NES
ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ['chapter','stage','return_stage','direction','planets','crystal',
          'operation_x','maps','backtrack','ending_flag','scene','resume_stage',
          'action','completed','retry','reserved']
EV = dict(clear=0,bonus=1,interior=2,secret=3,choose=4,crystal=5,map=6,
          ending_device=7,scene_done=8,whirlpool=9,retry=10)

def state(**values):
    result = bytearray(16); result[1] = 1
    for name, value in values.items(): result[FIELDS.index(name)] = value
    return bytes(result)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--core', type=pathlib.Path, required=True)
    ap.add_argument('--tool-dir', type=pathlib.Path)
    args = ap.parse_args()
    def tool(name):
        p = args.tool_dir / name if args.tool_dir else shutil.which(name)
        if not p: raise SystemExit(name + ' not found')
        return str(p)
    build = ROOT / 'build/campaign'; build.mkdir(parents=True, exist_ok=True)
    for source, name in [('src/campaign.s','campaign'),('tests/campaign_driver.s','driver')]:
        subprocess.run([tool('ca65'),'-I',str(ROOT/'src'),'-g','-o',str(build/(name+'.o')),str(ROOT/source)], check=True)
    rom = build / 'campaign_unit_test.nes'
    subprocess.run([tool('ld65'),'-C',str(ROOT/'cfg/campaign-test.cfg'),'-m',str(build/'link.map'),
                    '-Ln',str(build/'labels.txt'),'-o',str(rom),str(build/'campaign.o'),str(build/'driver.o')], check=True)
    labels = {line.split()[2].lstrip('.'): int(line.split()[1],16)
              for line in (build/'labels.txt').read_text().splitlines() if line.startswith('al ')}
    address = labels['Flow_State']; checks = []
    with NES(args.core, rom.read_bytes()) as nes:
        nes.run(2)
        assert nes.read(0x706,1)==b'\xa5', 'Native test driver did not boot'
        def send(before, event, param=0, command=2):
            nes.write(address,before); count=nes.read(0x705,1)[0]
            nes.write(0x701,bytes([event,param])); nes.write(0x700,bytes([command]))
            nes.run()
            assert nes.read(0x705,1)[0]==(count+1)&255, 'Native function did not return'
            assert nes.read(0x707,1)==b'\xff', '6502 stack leaked'
            return nes.read(address,16),nes.read(0x703,2)
        def check(name,before,event,expected,param=0,invalid=False):
            after,result=send(before,EV[event],param)
            if after!=expected or result!=bytes([expected[12],int(invalid)]):
                raise AssertionError(f'{name}\nactual: {dict(zip(FIELDS,after))}, return={result.hex()}\nexpected: {dict(zip(FIELDS,expected))}')
            checks.append(name); return after
        def update(before,**changes):
            out=bytearray(before);out[12]=0
            for k,v in changes.items():out[FIELDS.index(k)]=v
            return bytes(out)
        # New game must wipe stale chapter-local and persistent campaign state.
        actual,result=send(bytes([0xcc])*16,0,command=1)
        assert actual==state(action=1) and result==b'\x01\x00'
        checks.append('new_game_clears_stale_state')
        for phase,next_phase in [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(9,3),(10,4),(11,5),(12,8)]:
            check(f'n1_clear_{phase}',state(stage=phase),'clear',state(stage=next_phase,action=1))
        for phase,bonus in [(2,9),(3,10),(4,11),(7,12)]:
            check(f'n1_bonus_{phase}',state(stage=phase),'bonus',state(stage=bonus,action=1))
        n1=check('n1_final_scene',state(stage=8),'clear',state(stage=8,scene=1,action=2))
        check('n1_to_n2',n1,'scene_done',state(chapter=1,completed=1,action=1))
        # Interior return and secret routes are tested in BOTH directions.
        for direction in (0,1):
            for phase in range(1,7):
                nxt=phase+(1 if direction==0 else -1)
                initial=state(chapter=1,stage=phase,direction=direction)
                check(f'n2_clear_{phase}_{direction}',initial,'clear',update(initial,stage=nxt,action=1))
                if phase<6:
                    inside=check(f'n2_interior_{phase}_{direction}',initial,'interior',update(initial,stage=8,return_stage=nxt,action=1))
                    check(f'n2_leave_interior_{phase}_{direction}',inside,'clear',update(inside,stage=nxt,action=1))
            for phase,secret in [(3,9),(6,10)]:
                nxt=phase+(1 if direction==0 else -1)
                initial=state(chapter=1,stage=phase,direction=direction)
                secret_state=check(f'n2_secret_{phase}_{direction}',initial,'secret',update(initial,stage=secret,return_stage=nxt,action=1))
                check(f'n2_secret_return_{phase}_{direction}',secret_state,'clear',update(secret_state,stage=nxt,action=1))
                if secret==10:
                    eleven=check(f'n2_secret_chain_{direction}',secret_state,'secret',update(secret_state,stage=11,action=1))
                    check(f'n2_secret11_return_{direction}',eleven,'clear',update(eleven,stage=nxt,action=1))
        turn=check('n2_halfway_scene',state(chapter=1,stage=7),'clear',state(chapter=1,stage=7,scene=2,action=2))
        check('n2_turnaround',turn,'scene_done',state(chapter=1,stage=6,direction=1,action=1))
        final=check('n2_final_scene',state(chapter=1,stage=0,direction=1,completed=1),'clear',state(chapter=1,stage=0,direction=1,completed=1,scene=3,action=2))
        check('n2_to_salamander',final,'scene_done',state(chapter=2,completed=3,action=1))
        # All six planet orders, both with and without the Crystal Breeze.
        for crystal in (0,1):
            for order in itertools.permutations((3,4,5)):
                prefix=f'sal_{crystal}_{order}'
                current=state(chapter=2,crystal=crystal,completed=3)
                current=check(prefix+'_one',current,'clear',update(current,stage=2,action=1))
                current=check(prefix+'_two',current,'clear',update(current,stage=254,action=3))
                for planet in order:
                    current=check(prefix+f'_choose_{planet}',current,'choose',update(current,stage=planet,action=1),planet)
                    mask=current[4]|(1<<(planet-3))
                    target=(7 if crystal else 6) if mask==7 else 254
                    current=check(prefix+f'_clear_{planet}',current,'clear',update(current,planets=mask,stage=target,action=1 if mask==7 else 3))
                if crystal:
                    current=check(prefix+'_operation_x',current,'clear',update(current,operation_x=1,stage=6,action=1))
                end_scene=5 if crystal else 4
                current=check(prefix+'_end',current,'clear',update(current,scene=end_scene,action=2))
                if crystal:
                    check(prefix+'_next_chapter',current,'scene_done',state(chapter=3,completed=7,action=1))
                else:
                    current=check(prefix+'_retry_prompt',current,'scene_done',update(current,scene=0,retry=1,action=6))
                    check(prefix+'_retry',current,'retry',state(chapter=2,completed=3,action=1))
        for mask in range(8):
            current=state(chapter=3,stage=9,maps=mask)
            current=check(f'n3_map_scene_{mask}',current,'clear',update(current,scene=8,action=2))
            target=10 if mask==7 else 5 if not mask&1 else 7 if not mask&2 else 8
            current=check(f'n3_map_route_{mask}',current,'scene_done',update(current,stage=target,scene=0,backtrack=int(mask!=7),action=1))
        for phase,bit in [(5,1),(7,2),(8,4)]:
            for mask in range(8):
                current=state(chapter=3,stage=phase,maps=mask,backtrack=1)
                current=check(f'n3_collect_{phase}_{mask}',current,'map',update(current,maps=mask|bit))
                check(f'n3_revisit_scene_{phase}_{mask}',current,'clear',update(current,scene=8,action=2))
        for phase,scene in [(3,6),(4,7)]:
            current=state(chapter=3,stage=phase)
            current=check(f'n3_interlude_{phase}',current,'clear',update(current,scene=scene,action=2))
            check(f'n3_interlude_continue_{phase}',current,'scene_done',update(current,scene=0,stage=phase+1,action=1))
        for flag in (0,1):
            current=state(chapter=3,stage=11,ending_flag=flag,completed=7)
            current=check(f'n3_ending_{flag}',current,'clear',update(current,scene=9+flag,action=2))
            check(f'n3_campaign_finished_{flag}',current,'scene_done',update(current,scene=0,completed=15,action=4))
        check('n3_whirlpool',state(chapter=3,stage=3),'whirlpool',state(chapter=3,stage=3,action=5))
        check('n3_ending_device',state(chapter=3,stage=10),'ending_device',state(chapter=3,stage=10,ending_flag=1))
        check('sal_crystal',state(chapter=2,stage=4),'crystal',state(chapter=2,stage=4,crystal=1))
        invalid_cases=[
            ('n1_bad_bonus',state(stage=1),'bonus',0),
            ('n2_no_interior_in_rock_stage',state(chapter=1,stage=6),'interior',0),
            ('n2_no_interior_in_finale',state(chapter=1,stage=7),'interior',0),
            ('n2_bad_secret',state(chapter=1,stage=2),'secret',0),
            ('sal_bad_planet',state(chapter=2,stage=254),'choose',6),
            ('sal_duplicate_planet',state(chapter=2,stage=254,planets=1),'choose',3),
            ('sal_choose_without_menu',state(chapter=2,stage=2),'choose',3),
            ('n3_map_in_wrong_stage',state(chapter=3,stage=1),'map',0),
            ('device_in_wrong_stage',state(chapter=3,stage=9),'ending_device',0),
            ('scene_not_running',state(),'scene_done',0),
            ('event_during_scene',state(stage=8,scene=1),'clear',0),
            ('event_after_game_finished',state(chapter=3,stage=11,completed=15),'clear',0),
            ('stage_zero_n1',state(stage=0),'clear',0),
            ('stage_overflow_n3',state(chapter=3,stage=255),'clear',0),
            ('crystal_during_planet_choice',state(chapter=2,stage=254),'crystal',0),
        ]
        for name,current,event,param in invalid_cases:
            check(name,current,event,update(current,action=255),param,True)
    # Negative control: change the real native N1 bonus table, not the oracle.
    mutant=bytearray(rom.read_bytes())
    signature=bytes([0,0,9,10,11,0,0,12,0,0,0,0,0])
    if mutant.count(signature)!=1:raise AssertionError('Mutation target is not unique')
    mutant[mutant.index(signature)+2]=8
    with NES(args.core,bytes(mutant)) as bad:
        bad.run(2);bad.write(address,state(stage=2));bad.write(0x701,bytes([EV['bonus'],0]));bad.write(0x700,b'\x02');bad.run()
        changed=bad.read(address,16)
        if changed[1]!=8 or changed==state(stage=9,action=1):
            raise AssertionError('Negative control failed to exercise the corrupted route')
    report={'negative_control':'N1 stage-2 bonus route mutated from 9 to 8; native result differs from the source-derived expected route', 'scope':'Native 6502 campaign-event unit tests in FCEUmm; not a playable game or complete gameplay validation',
            'checks_passed':len(checks),'failed':0,'checks':checks,'state_bytes':16,'zero_page_bytes':2,
            'core_sha256':hashlib.sha256(args.core.read_bytes()).hexdigest(),
            'test_rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
            'test_rom_bytes':rom.stat().st_size,'code_bytes':labels['__CODE_SIZE__'],
            'game_port_complete':False}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/native_campaign_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
