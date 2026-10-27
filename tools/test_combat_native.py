#!/usr/bin/env python3
"""Run exact production 6502 combat routines in FCEUmm, with labeled RAM fixtures.
The harness occupies unused PRG bank 13; all tested production bytes are kept.
This tests mechanics, not acquisition, rendered campaign completion, or hardware.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,subprocess
from nes_test_host import NES
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--tools',type=pathlib.Path,required=True);a=p.parse_args()
 source=ROOT/'build/native/Nemesis_Legends_CP0012.nes';rom=source.read_bytes()
 labels={name:int(value,16) for value,name in re.findall(r'^al ([0-9A-Fa-f]+) \.([A-Za-z_][A-Za-z_0-9]*)$',(ROOT/'build/native/native.lbl').read_text(),re.M)}
 build=ROOT/'build/combat_tests';build.mkdir(parents=True,exist_ok=True)
 required=['InitActors','CollectBomb','CollectCapsule','LaserStep','MovePlayer','Upgrade','UpdateOptions','UpdateHUD','ShieldContact']
 for name in required:
  if name not in labels:raise ValueError(f'Missing production symbol {name}')
 code=['.setcpu "6502"','.segment "CODE"','Start:','lda #0','ldx #0','ClearInternal:']
 for page in (0,2,3,4,5,6,7):code += [f'sta ${page:02x}00,x']
 code += ['inx','bne ClearInternal','lda #$60','sta $71','lda #0','sta $70','ldy #0','ClearCart:','sta ($70),y','iny','bne ClearCart','inc $71','ldx $71','cpx #$80','bne ClearCart']
 expected=[]
 def setv(addr,value):code.extend([f'lda #${value&255:02x}',f'sta ${addr:04x}'])
 def call(name):code.append(f'jsr ${labels[name]:04x}')
 def check(addr,value,name):
  k=len(expected)+1;expected.append(dict(index=k,name=name,address=f'{addr:04X}',expected=value))
  code.extend([f'lda ${addr:04x}',f'cmp #${value&255:02x}',f'beq Ok{k}','inc $0781',f'lda #${k:02x}','sta $0783',f'jmp Next{k}',f'Ok{k}:','inc $0782',f'Next{k}:'])
 def init():
  setv(0x0b,0x80);call('InitActors');setv(0x3b,0);setv(6,0);setv(0x6900+18,17)
 def obj(n,typ,hp=10,x=112,y=80):
  addr=0x6d00+n*32
  for off,value in [(0,typ),(4,y),(6,x),(15,hp),(27,3)]:setv(addr+off,value)
 def laser(length):
  for addr,val in [(0x20,80),(0x21,74),(0x38,0),(0x39,0x66),(0x6600,3),(0x6601,96),(0x6602,80),(0x6603,0),(0x6604,0),(0x6605,0),(0x6606,length)]:setv(addr,val)
 # MSX p02:9B0D,9B4D: base 1.5 pixels/frame, cancelling opposing directions.
 setv(0x20,80);setv(0x21,74);setv(0x77,0);setv(0x78,0);setv(0x22,0);setv(3,1)
 call('MovePlayer');check(0x20,81,'base_speed_first_integer_step');check(0x77,128,'base_speed_keeps_half_pixel')
 call('MovePlayer');check(0x20,83,'base_speed_two_frames_are_three_pixels');check(0x77,0,'fraction_carries_into_position')
 setv(3,3);call('MovePlayer');check(0x20,83,'opposing_horizontal_directions_cancel')
 setv(0x22,8);setv(3,1);call('MovePlayer');check(0x20,88,'speed_eight_caps_velocity_at_five_pixels')
 setv(0x20,8);setv(3,2);call('MovePlayer');check(0x20,8,'left_boundary_clamps');check(0x77,0,'boundary_clears_fraction')
 # Source option FIFO advances every valid-direction frame, not animation tick.
 setv(0x2b,2);setv(0x690a,0);setv(0x1b,0);setv(3,1);setv(0x20,40);setv(0x21,50)
 call('UpdateOptions');check(0x690a,1,'option_fifo_advances_on_even_frame')
 setv(0x1b,1);setv(0x20,42);call('UpdateOptions');check(0x690a,2,'option_fifo_advances_on_odd_frame')
 setv(3,0);call('UpdateOptions');check(0x690a,2,'stationary_options_preserve_spacing')
 setv(3,3);call('UpdateOptions');check(0x690a,2,'opposing_directions_do_not_push_option_fifo')
 setv(0x1d,1);setv(0x24,3);setv(0x27,4);call('UpdateHUD')
 check(0x38e,58,'power_label_colon_is_not_overwritten');check(0x38f,52,'power_digit_has_own_cell')
 check(0x394,58,'option_label_colon_is_not_overwritten');check(0x395,50,'option_digit_has_own_cell')
 # p03:A0CB shield 10; occupied power choices do not consume the cursor.
 setv(5,0x80);setv(0x27,6);setv(0x2c,0);call('Upgrade');check(0x2c,10,'shield_grants_ten_hits');check(0x27,0,'shield_consumes_selected_slot')
 setv(0x27,6);call('Upgrade');check(0x27,6,'installed_shield_keeps_selected_slot')
 setv(0x22,8);setv(0x27,1);call('Upgrade');check(0x22,8,'speed_does_not_overflow_limit');check(0x27,1,'maximum_speed_keeps_selected_slot')
 setv(0x2a,0);setv(0x29,1);setv(0x27,4);call('Upgrade');check(0x2a,1,'laser_first_level');check(0x29,0,'laser_disables_double')
 setv(0x27,4);call('Upgrade');check(0x2a,2,'laser_second_level');setv(0x27,4);call('Upgrade');check(0x27,4,'maximum_laser_keeps_selected_slot')
 # p01:7420: field intercepts ordinary actor before the ship body; ten hits.
 init();setv(0x20,80);setv(0x21,74);setv(0x2c,10);obj(0,3,x=104,y=74)
 setv(0x2f,0);setv(0x30,0);setv(0x31,0x6d);call('ShieldContact')
 check(0x2c,9,'enemy_contact_consumes_one_shield_hit');check(0x6d00,0x15,'field_destroys_intercepted_enemy')
 obj(0,3,x=104,y=74);setv(0x2c,1);call('ShieldContact');check(0x2c,0,'last_hit_removes_field');check(0x6d00,0x15,'last_hit_still_destroys_enemy')
 obj(0,3,x=104,y=74);call('ShieldContact');check(0x6d00,3,'no_field_does_not_destroy_enemy')
 setv(0x2c,10);obj(0,3,x=180,y=74);call('ShieldContact');check(0x2c,10,'outside_field_keeps_strength');check(0x6d00,3,'outside_field_keeps_enemy')
 # p01:758E-75B7: blue bomb explodes regular and five-part enemies, not bullets.
 init();obj(0,0x13);obj(1,3);obj(2,0x12);obj(12,0x20)
 setv(0x6700,1);setv(0x54,22);setv(0x27,4);setv(0x2f,0);setv(0x30,0);setv(0x31,0x6d)
 call('CollectBomb')
 check(0x6d00,0,'blue_capsule_is_consumed');check(0x6d20,0x15,'blue_bomb_explodes_regular_enemy')
 check(0x6e80,0x15,'blue_bomb_explodes_dedicated_mid_part');check(0x6d40,0x12,'blue_bomb_preserves_red_capsule')
 check(0x6700,1,'blue_bomb_does_not_erase_separate_enemy_bullets');check(0x54,22,'blue_bomb_does_not_damage_big_core')
 check(0x27,4,'blue_capsule_does_not_advance_power_bar');check(0x6915,1,'blue_bomb_counter');check(0x690e,2,'bomb_awards_actual_kills')
 setv(0x27,6);setv(0x2d,0xfe);setv(0x2e,0);call('CollectCapsule')
 check(0x27,1,'red_capsule_wraps_six_to_one');check(0x2d,3,'red_capsule_adds_five_score_units');check(0x2e,1,'score_addition_carries')
 # p02:9D8F,9E66-9EDF: source growth/detachment/travel.
 init();laser(8);call('LaserStep');check(0x6605,4,'short_laser_grows_four_chars');check(0x6606,4,'short_laser_remaining_four');check(0x6603,0,'short_laser_still_attached')
 call('LaserStep');check(0x6605,8,'short_laser_reaches_eight_chars');check(0x6603,1,'short_laser_detaches_at_eight')
 call('LaserStep');check(0x6601,128,'detached_laser_moves_thirty_two_pixels')
 init();laser(15)
 for _ in range(4):call('LaserStep')
 check(0x6605,15,'long_laser_reaches_fifteen_chars');check(0x6606,0,'long_laser_consumes_growth_budget');check(0x6603,1,'long_laser_detaches')
 # Wall at world tile (16,10): x128,y80. Collision clips, then beam collapses.
 init();laser(8);setv(0x620a,1);call('LaserStep');call('LaserStep')
 check(0x6605,4,'wall_clips_laser_at_exact_source_tile');check(0x6603,2,'wall_changes_laser_to_shrinking_state');call('LaserStep');check(0x6600,0,'four_char_tail_disappears_after_wall');setv(0x620a,0)
 # p01:72AE-72C2: one laser kills multiple vulnerable actors; immunity is explicit.
 init();laser(8);obj(0,3,hp=10,x=104);obj(1,0x20,hp=10,x=112);obj(2,0x0b,hp=255,x=104)
 call('LaserStep');check(0x6d00,0x15,'laser_kills_vulnerable_enemy_without_normal_shot_hp_loop');check(0x6d20,0x15,'same_laser_kills_second_intersected_actor');check(0x6d40,0x0b,'source_type_0b_resists_laser');check(0x690e,2,'laser_kill_counter_is_exact')
 code+=['lda #$a5','sta $0780','Stop: jmp Stop','.segment "TRAMP"','sei','cld','ldx #$ff','txs','lda #0','sta $2000','sta $2001','sta $4015','sta $5204','lda #$40','sta $4017','lda #3','sta $5100','lda #2','sta $5102','lda #1','sta $5103','lda #0','sta $5113','lda #$8d','sta $5114','lda #$87','sta $5115','lda #$8e','sta $5116','lda #$8f','sta $5117','jmp Start']
 asm=build/'driver.s';asm.write_text('\n'.join(code)+'\n')
 cfg=build/'driver.cfg';cfg.write_text('MEMORY { C:start=$8000,size=$2000,file=%O,fill=yes; T:start=$E900,size=$100,file=%O,fill=yes; } SEGMENTS { CODE:load=C,type=ro; TRAMP:load=T,type=ro; }\n')
 subprocess.run([str(a.tools/'ca65'),str(asm),'-o',str(build/'driver.o')],check=True)
 subprocess.run([str(a.tools/'ld65'),'-C',str(cfg),str(build/'driver.o'),'-o',str(build/'driver.bin')],check=True)
 data=(build/'driver.bin').read_bytes();test=bytearray(rom)
 assert test[16+13*8192:16+14*8192]==bytes([255])*8192,'Fixture bank is no longer free'
 assert test[16+15*8192+0x900:16+15*8192+0xa00]==bytes([255])*256,'Fixture trampoline space is no longer free'
 test[16+13*8192:16+14*8192]=data[:8192];test[16+15*8192+0x900:16+15*8192+0xa00]=data[8192:]
 test[16+128*1024-4:16+128*1024-2]=bytes.fromhex('00e9')
 def run(image):
  with NES(a.core,bytes(image)) as n:
   n.run(15);return list(n.read(0x780,4))
 result=run(test)
 # Negative control mutates only the production growth instruction, not the oracle.
 mutation=bytearray(test);lo=labels['LaserStep'];hi=labels['LaserDraw'];base=16+14*8192-0xc000
 needle=bytes.fromhex('a204a005b138');spot=mutation.find(needle,base+lo,base+hi)
 assert spot>=0,'Production growth instruction signature changed; review negative control'
 mutation[spot+1]=3;negative=run(mutation)
 passed=result==[0xa5,0,len(expected),0] and negative[0]==0xa5 and negative[1]>0
 report=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),harness_sha256=hashlib.sha256(test).hexdigest(),scope=__doc__,assertions=expected,observed=result,negative_control=dict(change='production laser grows 3 rather than 4 characters',observed=negative,rejected=negative[1]>0),passed=passed)
 (ROOT/'reports/cp0012/combat_unit_tests.json').write_text(json.dumps(report,indent=2)+'\n')
 print('COMBAT',result,'ASSERTIONS',len(expected),'NEGATIVE',negative,'PASS',passed)
 if not passed:
  if result[3]:print('LAST FAILURE:',expected[result[3]-1])
  raise SystemExit(1)
if __name__=='__main__':main()
