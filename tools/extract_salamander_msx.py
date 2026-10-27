#!/usr/bin/env python3
"""Salamander - Operation X (MSX, Konami RC-758, 1987) source-resource reader. Not a NES gameplay implementation.
Format evidence: antxiko/Salamander-disassembly commit 6f166825c6df198f4a3044b7efb90c24b80862d3 (pinned in
third_party/ACQUISITION.json): tools/vram.py, tools/dibuja.py, tools/mundo.py and the listings
src/salamander_p00/p01/p02/p07/p08/p09/p12/p13/p14.asm, re-read 2026-10-27. Addresses are quoted as pNN:XXXX.
Engine and formats are the Nemesis 2 ones: RLE p00:4D16 (0 ends; <0x80 repeats the next byte; 0x80 brings a
new destination word; >0x80 copies n&0x7F bytes), tile lists p00:4546 [thirds][patterns][tile][colours],
VRAM->VRAM mirror/flip copies p00:44F9 (3 or 4 byte records). Maps are 4x4-tile blocks (p13:6000/600E):
horizontal stages 1,4,5,7 store 6 blocks per column (p00:49BF), vertical stages 2,3,6 store 8 blocks per row
entering from the top (p00:4A8C). Stage 7 (OPERATION X) uses tiles copied at runtime from the Nemesis 2
cartridge (p00:5B91, table p00:5BFE, 1137 bytes to 0xC100): the hash-verified Nemesis 2 ROM named in the
manifest is used when present. Preserves raw scripts/metablocks alongside decoded inspection images.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib
from PIL import Image
from extract_nemesis_msx import ROOT,REV,PAL,tile_indices,indexed_image
from extract_nemesis2_msx import sprite_sheet
EXPECTED='edbbba820ac67d6a55b9dc5da9309e45979936d5620c07d09793efaf077e86b9'
UPSTREAM='antxiko/Salamander-disassembly@6f166825c6df198f4a3044b7efb90c24b80862d3'
STAGES=range(1,8)
VERTICAL_MASK=0x26                      # p00:4835 bit_de_fase: one bit per stage, set for 2, 3 and 6
VISIBLE_ROWS=21                         # p01:6016 dumps 21 rows of the 24-row RAM map to the name table
SCROLL_START=0x20                       # p02:8707
# p00:5C77-5CC8: mid-stage tile reloads, (scroll of the entering column/row, bank-0 table of 3 pointers)
CHANGES={1:[(0x190,0x5CFA)],3:[(0x20F,0x5D00)],6:[(0xB8,0x5D06),(0x1A0,0x5D0C)],7:[(0x1C0,0x5D12)]}
# p02:8525-86EF stage scripts: ('h',scroll stop) normal scroll; ('down'|'left'|'right',from,to) detour through a
# bank-14 map driven by counter 0xE612 (p00:4BE6); ('boss',n) boss n at 0xE640; ('core',) stage 7 fixed object 0xE6C8
SCRIPTS={1:[('h',0x11F),('down',0x18,0x00),('h',0x1FF),('down',0x30,0x18),('h',0x21F),('boss',1)],
         2:[('h',0x20F),('boss',2)],3:[('h',0x20F),('boss',8),('boss',3)],
         4:[('h',0x1BF),('down',0x18,0x00),('h',0x25F),('wave','p11:BD3E/BD53'),('boss',4)],
         5:[('h',0x1DF),('boss',5)],
         6:[('h',0x14F),('left',0x20,0x00),('h',0x167),('right',0x1F,0x3F),('h',0x227),('boss',7),('boss',6)],
         7:[('h',0x1BF),('core',),('h',0x1DF),('core',)]}
DETOUR_MAP={1:0x80FC,4:0x815C,6:0x818C}  # p00:4C90 (stage 1), p00:4C96 (others, used by 4), p00:4C4A (stage 6)
class Window:
 """Read the cartridge with bank 0 at 0x4000 and three 8 KB banks at 0x6000/0x8000/0xA000; optional RAM image at 0xC000."""
 def __init__(self,rom,banks,ram=None,name=None):self.rom=rom;self.banks=(0,)+tuple(banks);self.ram=ram;self.name=name or 'banks_'+'_'.join(map(str,banks))
 def offset(self,a):
  if a>=0xC000 and self.ram is not None:return None
  if not 0x4000<=a<0xc000:raise ValueError('Unmapped address %04X'%a)
  return self.banks[(a-0x4000)//8192]*8192+(a&8191)
 def __call__(self,a):
  if a>=0xC000 and self.ram is not None:return self.ram[a-0xC000]
  return self.rom[self.offset(a)]
 def word(self,a):return self(a)|(self(a+1)<<8)
 def raw(self,a,n):return bytes(self(a+i) for i in range(n))
class Extractor:
 def __init__(self,rom,nemesis2=None):
  if hashlib.sha256(rom).hexdigest()!=EXPECTED:raise ValueError('Wrong Salamander MSX revision')
  self.rom=rom;self.game=Window(rom,(1,2,3));self.gfx=Window(rom,(7,8,9));self.maps=Window(rom,(13,14,15));self.special=Window(rom,(1,2,12))
  self.streams={};self.copy_records=[];self.pieces=[];self.ram=self.neighbour_ram(nemesis2)
 def neighbour_ram(self,n2):
  """p00:5BE1 run from 0xC03C: 20 records [count][source word] at p00:5BFE, read from Nemesis 2 banks 7-8-9 (0x6000-0xBFFF) to 0xC100."""
  ram=bytearray(0x4000);d=0x100
  for k in range(20):
   a=0x5BFE+3*k;n=self.game(a);src=self.game.word(a+1);off=(7+(src-0x6000)//8192)*8192+(src&8191)
   self.pieces.append(dict(count=n,nemesis2_cpu_address=src,nemesis2_rom_offset=off,ram_destination=0xC000+d))
   if n2 is not None:ram[d:d+n]=n2[off:off+n]
   d+=n
  if d-0x100!=1137:raise ValueError('Nemesis 2 piece table does not sum to 1137 bytes')
  return ram if n2 is not None else None
 def window(self,stage):
  if stage!=7:return self.gfx
  return Window(self.rom,(7,8,9),self.ram if self.ram is not None else bytearray(0x4000),'banks_7_8_9+nemesis2_ram_copy' if self.ram is not None else 'banks_7_8_9+MISSING_nemesis2')
 def vertical(self,stage):return bool(VERTICAL_MASK>>(stage-1)&1)
 def rle(self,v,w,src,dst):
  start=src;writes=0
  for _ in range(16384):
   n=w(src);src+=1
   if n==0:
    raw=w.raw(start,src-start);key=(w.name,start,len(raw))
    self.streams[key]=dict(window=w.name,cpu_address=start,rom_offset=w.offset(start),compressed_bytes=len(raw),decoded_writes=writes,sha256=hashlib.sha256(raw).hexdigest());return
   if n==0x80:dst=w.word(src);src+=2;continue
   if n<0x80:data=bytes([w(src)])*n;src+=1
   else:data=w.raw(src,n&127);src+=n&127
   for b in data:v[dst&0x3fff]=b;dst+=1;writes+=1
  raise ValueError('Unterminated RLE')
 def rle3(self,v,w,src,dst):
  for t in (0,0x800,0x1000):self.rle(v,w,src,dst+t)   # p00:4CE5
 def lists(self,v,w,a):
  for _ in range(256):
   flags=w(a)
   if not flags:return
   for bit,base in [(0,0x1000),(1,0x800),(2,0)]:
    if flags>>bit&1:
     target=base+8*w(a+3);self.rle(v,w,w.word(a+1),0x2000+target);self.rle(v,w,w.word(a+4),target)
   a+=6
  raise ValueError('Unterminated tile list')
 def mirrors(self,v,w,a,vertical):
  for _ in range(256):
   source=w(a)
   if not source:return
   dest=w(a+1);flags=w(a+2);count=(flags>>6)&3;size=3
   if not count:count=w(a+3);size=4
   third=0 if flags&4 else 0x800 if flags&2 else 0x1000
   p=bytearray(v[(0x2000+third+8*source+i)&0x3fff] for i in range(count*8));c=bytearray(v[(third+8*source+i)&0x3fff] for i in range(count*8))
   if vertical:
    for i in range(0,len(p),8):p[i:i+8]=p[i:i+8][::-1];c[i:i+8]=c[i:i+8][::-1]
   else:p=bytearray(REV[b] for b in p)
   for bit,base in [(3,0x1000),(4,0x800),(5,0)]:
    if flags>>bit&1:
     for i in range(len(p)):v[(0x2000+base+dest*8+i)&0x3fff]=p[i];v[(base+dest*8+i)&0x3fff]=c[i]
   self.copy_records.append(dict(window=w.name,address=a,source=source,destination=dest,flags=flags,count=count,record_bytes=size,vertical=vertical));a+=size
  raise ValueError('Unterminated copy list')
 def vram(self,stage):
  """p00:44B7 then p00:483F: the tile VRAM a stage starts with."""
  v=bytearray(16384);w=self.window(stage);g=self.game;vert=self.vertical(stage)
  self.lists(v,w,0x6C63);self.lists(v,w,0x6C95 if vert else 0x6C8E);self.lists(v,w,w.word(0x6C37+2*stage))
  self.mirrors(v,w,w.word(0x6C45+2*stage),False);self.mirrors(v,w,w.word(0x6C53+2*stage),True)
  self.rle3(v,g,0x4876 if vert else 0x4868,0x2280);self.rle3(v,g,0x4879 if vert else 0x486B,0x0280)
  return v
 def change(self,v,stage,table):
  w=self.window(stage);g=self.game;self.lists(v,w,g.word(table));self.mirrors(v,w,g.word(table+2),False);self.mirrors(v,w,g.word(table+4),True)  # p00:5CCB
 def tranches(self,stage):
  v=self.vram(stage);out=[(0,bytes(v))]
  for scroll,table in CHANGES.get(stage,[]):self.change(v,stage,table);out.append((scroll,bytes(v)))
  return out
 def boss_vram(self,stage,boss,base):
  """p00:4DC8: boss 8 loads nothing; 3 and 6 use p07:6822/6895/68C0 (painted progressively by p00:4763); the rest their p07:67D6/67E4/67F2 entry."""
  v=bytearray(base);w=self.window(stage)
  if boss==8:return v
  if boss in (3,6):self.lists(v,w,0x6822);self.mirrors(v,w,0x6895,False);self.mirrors(v,w,0x68C0,True)
  else:self.lists(v,w,w.word(0x67D6+2*boss));self.mirrors(v,w,w.word(0x67E4+2*boss),False);self.mirrors(v,w,w.word(0x67F2+2*boss),True)
  return v
 def sprite_copies(self,v,w,a):
  for _ in range(256):
   kind=w(a)
   if not kind:return
   n,src,dst=w(a+1),w(a+2),w(a+3)
   for k in range(n):
    pos=0x1800+src*8+k*32;data=v[pos:pos+32]
    if kind==1:data=data[:16][::-1]+data[16:][::-1]                        # p00:4411 upside down
    else:data=bytes(REV[b] for b in data);data=data[16:]+data[:16]          # p00:4D3B mirror, columns swapped
    pos=0x1800+dst*8+k*32;v[pos:pos+32]=data
   a+=4
  raise ValueError('Unterminated sprite copy list')
 def sprites(self,stage,base):
  """p00:438C -> p00:444F (common streams), p00:4494 (stage list p08:8B26) and p00:43A7 (copies p08:8BD3)."""
  v=bytearray(base);w=self.window(stage);c=self.vertical(stage)
  self.rle(v,w,0xA130,0x1880);self.rle(v,w,0xA06F,0x1960)
  self.rle(v,w,0xA009 if c else 0xA042,0x18C0);self.rle(v,w,0xA0F3 if c else 0xA0D8,0x1900);self.rle(v,w,0xA122 if c else 0xA113,0x18A0)
  a=w.word(0x8B26+2*stage)
  for _ in range(256):
   if not w(a):break
   self.rle(v,w,w.word(a+1),0x1800+8*w(a));a+=3
  else:raise ValueError('Unterminated sprite stream list')
  self.sprite_copies(v,w,w.word(0x8BD3+2*stage));return bytes(v[0x1800:0x2000])
 def route(self,stage):
  g=self.game;a=0x88F2+6*stage;start,end,stop=g.word(a),g.word(a+2),g.word(a+4)   # p02:88A2 -> 0xE621/E623/E625
  if bool(g(0x8921+stage))!=self.vertical(stage):raise ValueError('p02:8921 and p00:4835 disagree on direction')
  if SCRIPTS[stage][0][1]!=stop:raise ValueError('First scroll stop differs from p02 script')
  return start,end,stop
 def block(self,stage,n):
  m=self.maps;a=0x600E+16*n if n<4 else m.word(0x5FFE+2*stage)+16*(n-4)   # p00:4A25/4A30
  return m.raw(a,16),a
 def expand(self,stage,script,vertical,start,used):
  """Rows of (tile, scroll at which it enters the screen), as p00:49BF (columns) or p00:4A8C (rows entering from the top) fill the RAM map."""
  def blk(n):
   b,a=self.block(stage,n);used[n]=dict(id=n,address=a,rom_offset=self.maps.offset(a),hex=b.hex());return b
  if not vertical:
   rows=[[] for _ in range(24)]
   for c in range(len(script)//6):
    for x in range(4):
     for r in range(6):
      b=blk(script[6*c+r])
      for k in range(4):rows[4*r+k].append((b[4*k+x],start+4*c+x))
   return rows
  rows=[]
  for r in range(len(script)//8):
   part=[[] for _ in range(4)]
   for n in script[8*r:8*r+8]:
    b=blk(n)
    for k in range(4):part[k].extend((ch,start+4*r+3-k) for ch in b[4*k:4*k+4])
   rows=part+rows
  return rows
 def terrain(self,stage):
  start,end,stop=self.route(stage);vertical=self.vertical(stage);m=self.maps
  steps=(end-1-start)//4+1;per=8 if vertical else 6;a=m.word(0x6F4C+2*stage);script=m.raw(a,steps*per);used={}
  rows=self.expand(stage,script,vertical,start,used)
  table=m.word(0x5FFE+2*stage);table_end=m.word(0x5FFE+2*(stage+1)) if stage<7 else 0x6F4E   # p13:6000 pointers; the last table ends where DATA_mapas starts
  meta=dict(stage_id=stage,direction='vertical' if vertical else 'horizontal',rows=len(rows),columns=len(rows[0]),visible_rows=VISIBLE_ROWS if not vertical else None,
            route=dict(start_scroll=start,end_scroll=end,first_scroll_stop=stop,initial_scroll=SCROLL_START,record_address=0x88F2+6*stage,record_rom_offset=self.game.offset(0x88F2+6*stage)),
            column_script_address=a,column_script_rom_offset=m.offset(a),column_script_bytes=len(script),script_unit='row' if vertical else 'column',blocks_per_unit=per,block_steps=steps,
            metatile_table_address=table,metatile_table_rom_offset=m.offset(table),metatile_table_bytes=table_end-table,metatile_table_blocks=(table_end-table)//16,
            metatiles_used=len(used),common_metatile_address=0x600E,metatiles=[used[k] for k in sorted(used)],
            runtime_integration=False,dynamic_terrain_enemy_events_and_items='not_extracted')
  return meta,rows,script
 def detour(self,stage,used):
  """p00:4BE6: the scroll stops and 0xE612 walks a bank-14 map with the stage's own blocks; 'down' maps are in row (vertical) format, 'left'/'right' in column format."""
  a=DETOUR_MAP.get(stage)
  if a is None:return None,None
  segs=[s for s in SCRIPTS[stage] if s[0] in ('down','left','right')];stops=[s[1] for s in SCRIPTS[stage] if s[0]=='h']
  vertical=segs[0][0]=='down';top=max(max(s[1],s[2]) for s in segs)+(0 if vertical else 1);per=8 if vertical else 6;steps=top//4
  script=self.maps.raw(a,steps*per);rows=self.expand(stage,script,vertical,0,used)
  # the detour rows/columns enter while the main scroll is parked at the stop before that segment
  stop_of={}
  for i,s in enumerate(segs):
   for e in range(min(s[1],s[2]),max(s[1],s[2])+1):stop_of[e]=stops[i]
  for row in rows:
   for i,(ch,e) in enumerate(row):row[i]=(ch,stop_of.get(e,stops[0]))
  return dict(address=a,rom_offset=self.maps.offset(a),bytes=len(script),format='row' if vertical else 'column',blocks_per_unit=per,block_steps=steps,rows=len(rows),columns=len(rows[0]),
              segments=[dict(kind=s[0],counter_from=s[1],counter_to=s[2],main_scroll_parked_at=stops[i]) for i,s in enumerate(segs)],reader='p00:4C8D' if vertical else 'p00:4C3D'),rows
 def music(self,stage):
  g=self.game;a=g.word(0x876A+2*stage);out=[]
  for _ in range(64):
   pos=g.word(a);out.append(dict(until_scroll=pos,track=g(a+2)));a+=3
   if pos==0xFFFF:return dict(list_address=g.word(0x876A+2*stage),records=out)   # p02:8748
  raise ValueError('Unterminated music list')
 def animation(self,stage):
  """p12:A4A9: every 4 frames (16 in stage 4), without a boss, one step of p12:A52F[stage]: [n|colours<<7] then n x [tile][thirds][8 bytes]."""
  w=self.special;a=w.word(0xA52F+2*stage)
  if not a:return None,b''
  n=w(a)&0x7F;raw=w.raw(a,1+10*n)
  steps=[dict(tile=raw[1+10*k],thirds=raw[2+10*k],data=raw[3+10*k:11+10*k].hex()) for k in range(n)]
  return dict(address=a,rom_offset=w.offset(a),bytes=len(raw),steps=n,writes_colours=bool(w(a)&0x80),period_frames=16 if stage==4 else 4,steps_detail=steps),raw
 def world(self,stage,rows,detour_rows):
  """tools/mundo.py simulation of p02's script: {(x,y):(tile,scroll)} with the detours in place; x right, y down, in tiles."""
  start,end,stop=self.route(stage);vertical=self.vertical(stage);cells={};s=SCROLL_START;vx,vy=0,0
  if not vertical:vx=s-start-31
  else:vy=-(s-start)
  def column(src,e):return [src[r][e][0] for r in range(24)]
  def row(src,e):return [c[0] for c in src[len(src)-1-e]]
  for seg in SCRIPTS[stage]:
   if seg[0]=='h':
    while s<seg[1]:
     s+=1;c=s-start
     if not vertical:
      vx=c-31
      if 0<=c and s<end:
       for r,ch in enumerate(column(rows,c)):cells[(c,vy+r)]=(ch,s)
     else:
      vy=-c
      if 0<=c and s<end:
       for i,ch in enumerate(row(rows,c)):cells[(vx+i,vy)]=(ch,s)
   elif seg[0] in ('down','left','right'):
    kind,frm,to=seg;step=-1 if frm>to else 1
    for e in range(frm+step,to+step,step):
     if kind=='down':
      vy+=1
      for i,ch in enumerate(row(detour_rows,e)):cells[(vx+i,vy+23)]=(ch,s)
     else:
      vx+=-1 if kind=='left' else 1;x=vx if kind=='left' else vx+31
      for r,ch in enumerate(column(detour_rows,e)):cells[(x,vy+r)]=(ch,s)
  return cells

def render_cells(cells,tranches,vertical):
 """Paint (tile, scroll) cells with the VRAM tranche in force at that scroll. Horizontal maps take the third of the screen row (y%24)//8;
 vertical maps use third 0 (rows pass through all three thirds while scrolling; see tiles_differing_between_thirds in stage.json)."""
 xs=[x for x,y in cells];ys=[y for x,y in cells];x0,y0=min(xs),min(ys)
 im=Image.new('P',((max(xs)-x0+1)*8,(max(ys)-y0+1)*8));im.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-48));cache={}
 for (x,y),(t,s) in cells.items():
  ti=max(i for i,(d,_) in enumerate(tranches) if s>=d);third=0 if vertical else (y%24)//8;key=(ti,third,t)
  if key not in cache:cache[key]=indexed_image(tile_indices(tranches[ti][1],t,third),(8,8))
  im.paste(cache[key],((x-x0)*8,(y-y0)*8))
 return im

def render_rows(rows,tranches,vertical,limit=None):
 rows=rows[:limit] if limit else rows
 return render_cells({(x,y):c for y,row in enumerate(rows) for x,c in enumerate(row)},tranches,vertical)

def thirds_differ(v,tiles):
 return sum(1 for t in tiles if len({bytes(v[a+t*8:a+t*8+8])+bytes(v[0x2000+a+t*8:0x2000+a+t*8+8]) for a in (0,0x800,0x1000)})>1)

def tile_sheet(v):
 sheet=Image.new('P',(16*8*3,16*8));sheet.putpalette([c for rgb in PAL for c in rgb]+[0]*(768-48))
 for third in range(3):
  for tile in range(256):sheet.paste(indexed_image(tile_indices(v,tile,third),(8,8)),(third*128+(tile%16)*8,(tile//16)*8))
 return sheet.resize((768,256),Image.Resampling.NEAREST)

# Facts from the pinned docs (docs/THE-STAGES.md, THE-BOSSES.md, THE-MUSIC.md, CURIOSITIES.md); boss names are the Gradius Wiki's, not in the ROM.
CARDS={1:('OPERATION ONE','-TOP FLIGHT SPEED TO LATIS-',None),2:('OPERATION TWO','-CONDUCT TO SPACE STATION ZOT-',None),
       3:('OPERATION THREE','-SET THE CRUSH BLOW SYSTEM-','EIONEUS'),4:('OPERATION THREE','-SET THE CRUSH BLOW SYSTEM-','LAVINIA'),
       5:('OPERATION THREE','-SET THE CRUSH BLOW SYSTEM-','KIERKE'),6:('OPERATION FOUR','-CRUSH SALAMANDER-',None),7:('OPERATION X','-WRATH OF VENOM-',None)}
BOSS_NAMES={1:'Golem',2:'Cruiser Tetran',3:'Dead End',4:'Seducer',5:'Enigma',6:'Metal Slave',7:'Outer Limits',8:'Center Core'}
ROLES={1:'first stage, always first',2:'second stage, always second',3:'planet EIONEUS, one of three picked on the radar (p10:988A, clock p10:9A43)',
       4:'planet LAVINIA, one of three picked on the radar',5:'planet KIERKE, one of three picked on the radar',6:'final stage (OPERATION FOUR); boss 6 falling starts the ending (p11:B58D)',
       7:'OPERATION X secret stage: only with Nemesis 2 in the other slot (p03:B599/B5E3), played before stage 6 (p10:8B7B); its tiles come from that cartridge (p00:5B91)'}

def structure(ex,manifest):
 g=ex.game;bosses={n+1:dict(code_address='p11:%04X'%g.word(0x6E89+2*n),dispatch_index=n,wiki_name=BOSS_NAMES[n+1]) for n in range(8)}  # p01:6E76: A = 0xE640 - 1
 maps=[]
 for m in manifest:
  s=m['stage_id'];card,sub,planet=CARDS[s];music=[r['track'] for r in m['music']['records']]
  entry=dict(map_id='map_%02d'%s,stage_id=s,card=card,subtitle=sub,planet=planet,role=ROLES[s],direction=m['direction'],
             length={'columns' if m['direction']=='horizontal' else 'rows':m['columns'] if m['direction']=='horizontal' else m['rows'],'block_steps':m['block_steps']},
             route=m['route'],map_script=dict(cpu_address='p%02d:%04X'%(ex.maps.offset(m['column_script_address'])//8192,m['column_script_address']),rom_offset=m['column_script_rom_offset'],bytes=m['column_script_bytes']),
             metatile_table=dict(cpu_address='p13:%04X'%m['metatile_table_address'],rom_offset=m['metatile_table_rom_offset'],bytes=m['metatile_table_bytes'],blocks=m['metatile_table_blocks'],blocks_used_including_common=m['metatiles_used']),
             graphics=m['graphics'],sprites=m['sprites'],tile_changes=m['tile_changes'],tile_animation=m['tile_animation'],detour=m.get('detour'),
             script=[list(x) for x in SCRIPTS[s]],script_code='p02:%04X'%g.word(0x8517+2*(s-1)),
             bosses=[dict(bosses[x[1]],boss_id=x[1]) for x in SCRIPTS[s] if x[0]=='boss'] or [dict(role='fixed core object at p12:A000 (0xE6C8), two parts; wiki names Venom / True Venom, UNRESOLVED mapping to code')],
             music=dict(list_address='p02:%04X'%m['music']['list_address'],stage_track=music[0],boss_track=music[-1],records=m['music']['records']),
             unresolved=list(m['unresolved']))
  maps.append(entry)
 return dict(source='salamander_msx',source_sha256=EXPECTED,upstream=UPSTREAM,
             cartridge=dict(mapper='Konami SCC, 16 x 8 KB banks',bank_sets={'game':'1-2-3','sound':'4-5-6','graphics':'7-8-9','maps':'13-14-15','intro_cutscenes_endings':'10 at 0x8000','bosses':'11 at 0xA000','special_enemies_items':'12 at 0xA000'},
                            screen='TMS9918 SCREEN 2: patterns 0x2000, colours 0x0000, names 0x3800, sprite patterns 0x1800, sprite attributes 0x3B00; 21 play rows + 3 status rows'),
             progression=dict(order='1, 2, then 3/4/5 in the order picked on the radar (p10:988A; clock p10:9A43), then 6; stage 7 before 6 only with Nemesis 2 (p10:8B7B)',
                              stage_dispatch_table='p02:8517',route_table='p02:88F2 (6 bytes per stage: start, end, first scroll stop)',direction_table='p02:8921 (also bit mask 0x26 at p00:4835)',
                              restart_scroll_table='p02:88E8: at stage (re)start the scroll resumes at this value if it had passed it, else at 0x20 (p02:88BC-88CE)'),
             formats=dict(rle='p00:4D16',tile_list='p00:4546',vram_copies='p00:44F9',stage_tiles='p00:44B7',sprites='p00:438C',map_column='p00:49BF',map_row='p00:4A8C',detour='p00:4BE6',mid_stage_change='p00:5C77/5CCB',tile_animation='p12:A4A9',boss_tiles='p00:4DC8',boss_dispatch='p01:6E89'),
             bosses=bosses,maps=maps,
             unresolved_global=['Enemy spawn/wave/event tables (p14:84BA events, p14:8560 waves, p14:85D1/85DF appearances, p01:6C5D 65 enemy records) are not decoded here.',
                                'Which item sits at each place in stages 3, 5 and 6 (0xE350-0xE359) and what results 2-4 change (p01:7B33): open upstream.',
                                'Enemy 0x06 (stage 4) and 0x30/0x38/0x40 (stage 6) use sprite patterns 0x40-0x6F not loaded at stage start: open upstream.',
                                'p14:80FC-81EC is labelled in the upstream p14 notes as stage-6 map tail with no reader, but p00:4C90/4C96/4C4A read it as the three detour maps; this extractor follows the code.',
                                'Boss names are Gradius Wiki names; the cartridge names no boss. Stage 7 core wiki names (Venom / True Venom) are not matched to code.',
                                'Music track numbers come from p02:876A; the sound engine itself (bank 4) is out of scope.'])

def extract():
 selected=json.loads((ROOT/'manifests/selected_sources.json').read_text());src=selected['salamander_msx']
 n2=selected.get('nemesis2_msx');n2path=ROOT/n2['path'] if n2 else None;n2rom=None
 if n2path and n2path.exists():
  data=n2path.read_bytes()
  if hashlib.sha256(data).hexdigest()==n2['sha256']:n2rom=data
 ex=Extractor((ROOT/src['path']).read_bytes(),n2rom);out=ROOT/'assets/msx/salamander';out.mkdir(parents=True,exist_ok=True)
 manifest=[];tiles={};colors=collections.Counter();previews=[];occurrences=0;sprite_sets=0;detours=0
 for stage in STAGES:
  folder=out/('map_%02d'%stage);folder.mkdir(exist_ok=True);tr=ex.tranches(stage);v=tr[0][1];meta,rows,script=ex.terrain(stage);vert=ex.vertical(stage)
  w=ex.window(stage);g=ex.game;unresolved=[]
  (folder/'source_vram.bin').write_bytes(v);(folder/'terrain_rows.bin').write_bytes(b''.join(bytes(c[0] for c in r) for r in rows));(folder/'column_script.bin').write_bytes(script)
  for scroll,snap in tr[1:]:(folder/('source_vram_after_%03X.bin'%scroll)).write_bytes(snap)
  render_rows(rows,tr,vert,None if vert else VISIBLE_ROWS).save(folder/'terrain.png')
  used_tiles=sorted({c[0] for r in rows for c in r})
  meta.update(graphics=dict(window=w.name,common_list='p07:6C63',direction_list='p07:%04X'%(0x6C95 if vert else 0x6C8E),stage_list='p07:%04X'%w.word(0x6C37+2*stage),mirror_copies='p07:%04X'%w.word(0x6C45+2*stage),flip_copies='p07:%04X'%w.word(0x6C53+2*stage),
                            star_tiles_rle3='p00:%04X/%04X -> VRAM 0x2280/0x0280 (tiles 0x50-0x51, animated by p00:4B97)'%((0x4876,0x4879) if vert else (0x4868,0x486B))),
              tile_changes=[dict(at_scroll=s,table='p00:%04X'%t,tile_list='p07:%04X'%g.word(t),mirror_copies='p07:%04X'%g.word(t+2),flip_copies='p07:%04X'%g.word(t+4),snapshot='source_vram_after_%03X.bin'%s) for s,t in CHANGES.get(stage,[])],
              tiles_used=len(used_tiles),tiles_differing_between_thirds=[thirds_differ(snap,used_tiles) for _,snap in tr],music=ex.music(stage))
  anim,raw=ex.animation(stage);meta['tile_animation']=anim
  if raw:(folder/'tile_animation.bin').write_bytes(raw)
  spr=ex.sprites(stage,v);(folder/'sprites_stage.bin').write_bytes(spr);sprite_sheet(spr).save(folder/'sprites.png');sprite_sets+=1
  meta['sprites']=dict(window=w.name,stream_list='p08:%04X'%w.word(0x8B26+2*stage) if stage!=7 else 'p07:6066',copy_list='p08:%04X'%w.word(0x8BD3+2*stage),common_streams='p09:A130->0x1880, A06F->0x1960, %s'%('A009->0x18C0, A0F3->0x1900, A122->0x18A0' if vert else 'A042->0x18C0, A0D8->0x1900, A113->0x18A0'),file='sprites_stage.bin',ship_sprites='not included: p01:6060 writes the ship posture (p14:95F7) to 0x1800-0x183F every frame')
  bosses=[x[1] for x in SCRIPTS[stage] if x[0]=='boss'];meta['boss_tile_sets']=[]
  for b in bosses:
   bv=ex.boss_vram(stage,b,tr[-1][1]);(folder/('boss_%d_vram.bin'%b)).write_bytes(bv);tile_sheet(bv).save(folder/('boss_%d_tiles.png'%b))
   meta['boss_tile_sets'].append(dict(boss_id=b,file='boss_%d_vram.bin'%b,loader='p00:4DC8',lists='none' if b==8 else 'p07:6822/6895/68C0 (progressive, p00:4763)' if b in (3,6) else 'p07:%04X/%04X/%04X'%(w.word(0x67D6+2*b),w.word(0x67E4+2*b),w.word(0x67F2+2*b))))
   for third in range(3):
    for tile in range(256):pix=tile_indices(bv,tile,third);tiles.setdefault(pix,[]).append([stage,'boss_%d'%b,third,tile]);colors[len(set(pix))]+=1;occurrences+=1
  dmeta,drows=ex.detour(stage,{})
  if dmeta:
   detours+=1;(folder/'detour_rows.bin').write_bytes(b''.join(bytes(c[0] for c in r) for r in drows));(folder/'detour_script.bin').write_bytes(ex.maps.raw(dmeta['address'],dmeta['bytes']))
   render_rows(drows,tr,vert).save(folder/'detour.png');dmeta.update(files=['detour_rows.bin','detour_script.bin','detour.png'],uses_stage_metatile_table=True,third_note='horizontal stages: third taken from the picture row, the real third changes as the rows scroll up')
   meta['detour']=dmeta
  else:drows=None
  if stage==7:
   meta['nemesis2_pieces']=dict(table='p00:5BFE',copier='p00:5B91/5BE1',total_bytes=1137,source='nemesis2_msx (%s)'%('used' if n2rom else 'MISSING: tiles from that cartridge are blank'),pieces=ex.pieces)
   if not n2rom:unresolved.append('Nemesis 2 ROM not available: stage 7 tiles copied from it are blank in this run.')
  if stage==2:unresolved.append('p13 mapa_fase2_cola: 48 bytes (6 rows) of map after the measured end 0x1F8 have no reader upstream.')
  if stage==4:unresolved.append('Between scrolls 0x100 and 0x150 the scenery is dumped one frame in 64 (p00:5FC5, p01:6016): the barely-visible base is rendered fully here.')
  meta['unresolved']=unresolved
  render_cells(ex.world(stage,rows,drows),tr,vert).save(folder/'route.png')
  for ti,(scroll,snap) in enumerate(tr):
   for third in range(3):
    for tile in range(256):pix=tile_indices(snap,tile,third);tiles.setdefault(pix,[]).append([stage,'vram' if ti==0 else 'after_%03X'%scroll,third,tile]);colors[len(set(pix))]+=1;occurrences+=1
  (folder/'stage.json').write_text(json.dumps(meta,indent=2)+'\n');manifest.append(meta)
  img=Image.open(folder/'terrain.png').convert('RGB');y0=max(0,img.height-168) if vert else 0;previews.append(img.crop((0,y0,256,y0+168)))   # vertical strips: the stage start is at the bottom
 (out/'source_tile_dictionary.bin').write_bytes(b''.join(tiles))
 (out/'source_tile_references.json').write_text(json.dumps([dict(sha256=hashlib.sha256(p).hexdigest(),references=r) for p,r in tiles.items()]))
 (out/'stage_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'compressed_streams.json').write_text(json.dumps(list(ex.streams.values()),indent=2)+'\n');(out/'mirror_records.json').write_text(json.dumps(ex.copy_records,indent=2)+'\n')
 contact=Image.new('RGB',(1024,336))
 for i,im in enumerate(previews):contact.paste(im,((i%4)*256,(i//4)*168))
 contact.save(out/'all_7_map_previews.png')
 horizontal=[m for m in manifest if m['direction']=='horizontal'];vertical=[m for m in manifest if m['direction']=='vertical']
 report=dict(source_sha256=EXPECTED,upstream=UPSTREAM,map_records=7,horizontal_maps=[m['stage_id'] for m in horizontal],vertical_maps=[m['stage_id'] for m in vertical],detour_maps=detours,
             terrain_columns_horizontal=sum(m['columns'] for m in horizontal),terrain_rows_vertical=sum(m['rows'] for m in vertical),
             source_tile_occurrences=occurrences,unique_source_pixel_tiles=len(tiles),sprite_sets=sprite_sets,boss_tile_sets=sum(len(m['boss_tile_sets']) for m in manifest),
             compressed_streams=len(ex.streams),rle_stream_bytes_sum=sum(s['compressed_bytes'] for s in ex.streams.values()),mirror_records=len(ex.copy_records),
             tiles_differing_between_thirds={m['stage_id']:m['tiles_differing_between_thirds'] for m in manifest},nemesis2_rom_used=bool(n2rom),
             runtime_integration=False,source_hardware_vram_comparison='pending (upstream reports its dibuja/mundo output identical to openMSX VRAM)',color_counts_per_tile=dict(colors),
             limitations=['Static terrain and source graphics only: enemies, waves, events, items, boss behaviour, cutscenes and the sound engine are not implemented or decoded.',
                          'Stages 2, 3 and 6 scroll vertically: rows are stored top-to-bottom as they appear on screen (the ROM stores them bottom-up, p00:4A8C) and painted with third 0; tiles_differing_between_thirds says how many used tiles would differ.',
                          'Detour maps (stages 1, 4, 6) are painted with the third of their picture row; on horizontal stages the real third changes as rows scroll.',
                          'Stage 7 tiles are copied at runtime from the Nemesis 2 cartridge; this run '+('used' if n2rom else 'LACKED')+' the manifest nemesis2_msx ROM.',
                          'Stars (tiles 0x50/0x51, p00:4B97), animated tiles (p12:A4A9) and the stage-4 one-frame-in-64 scenery dump are rendered in their initial static state.',
                          'Ship sprites (p14:95F7) and enemy frames loaded by enemy routines are not in the per-stage sprite sets; boss tile sets 3/6 are shown fully loaded although painted progressively.',
                          'VRAM snapshots and expanded maps are inspection files, not a proposed ROM representation. No NES palette quantization has been applied.'])
 (ROOT/'reports/salamander_extraction.json').write_text(json.dumps(report,indent=2)+'\n')
 (ROOT/'reports/salamander_structure.json').write_text(json.dumps(structure(ex,manifest),indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':extract()
