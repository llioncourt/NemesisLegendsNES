#!/usr/bin/env python3
"""Official NMOS 6502 instruction decoder for evidence inspection, not code/data inference."""
from __future__ import annotations
import argparse,pathlib
TABLE={}
ROWS={
0x00:'00:BRK:i 01:ORA:ix 05:ORA:z 06:ASL:z 08:PHP:i 09:ORA:n 0A:ASL:a 0D:ORA:w 0E:ASL:w',
0x10:'10:BPL:r 11:ORA:iy 15:ORA:zx 16:ASL:zx 18:CLC:i 19:ORA:wy 1D:ORA:wx 1E:ASL:wx',
0x20:'20:JSR:w 21:AND:ix 24:BIT:z 25:AND:z 26:ROL:z 28:PLP:i 29:AND:n 2A:ROL:a 2C:BIT:w 2D:AND:w 2E:ROL:w',
0x30:'30:BMI:r 31:AND:iy 35:AND:zx 36:ROL:zx 38:SEC:i 39:AND:wy 3D:AND:wx 3E:ROL:wx',
0x40:'40:RTI:i 41:EOR:ix 45:EOR:z 46:LSR:z 48:PHA:i 49:EOR:n 4A:LSR:a 4C:JMP:w 4D:EOR:w 4E:LSR:w',
0x50:'50:BVC:r 51:EOR:iy 55:EOR:zx 56:LSR:zx 58:CLI:i 59:EOR:wy 5D:EOR:wx 5E:LSR:wx',
0x60:'60:RTS:i 61:ADC:ix 65:ADC:z 66:ROR:z 68:PLA:i 69:ADC:n 6A:ROR:a 6C:JMP:ind 6D:ADC:w 6E:ROR:w',
0x70:'70:BVS:r 71:ADC:iy 75:ADC:zx 76:ROR:zx 78:SEI:i 79:ADC:wy 7D:ADC:wx 7E:ROR:wx',
0x80:'81:STA:ix 84:STY:z 85:STA:z 86:STX:z 88:DEY:i 8A:TXA:i 8C:STY:w 8D:STA:w 8E:STX:w',
0x90:'90:BCC:r 91:STA:iy 94:STY:zx 95:STA:zx 96:STX:zy 98:TYA:i 99:STA:wy 9A:TXS:i 9D:STA:wx',
0xA0:'A0:LDY:n A1:LDA:ix A2:LDX:n A4:LDY:z A5:LDA:z A6:LDX:z A8:TAY:i A9:LDA:n AA:TAX:i AC:LDY:w AD:LDA:w AE:LDX:w',
0xB0:'B0:BCS:r B1:LDA:iy B4:LDY:zx B5:LDA:zx B6:LDX:zy B8:CLV:i B9:LDA:wy BA:TSX:i BC:LDY:wx BD:LDA:wx BE:LDX:wy',
0xC0:'C0:CPY:n C1:CMP:ix C4:CPY:z C5:CMP:z C6:DEC:z C8:INY:i C9:CMP:n CA:DEX:i CC:CPY:w CD:CMP:w CE:DEC:w',
0xD0:'D0:BNE:r D1:CMP:iy D5:CMP:zx D6:DEC:zx D8:CLD:i D9:CMP:wy DD:CMP:wx DE:DEC:wx',
0xE0:'E0:CPX:n E1:SBC:ix E4:CPX:z E5:SBC:z E6:INC:z E8:INX:i E9:SBC:n EA:NOP:i EC:CPX:w ED:SBC:w EE:INC:w',
0xF0:'F0:BEQ:r F1:SBC:iy F5:SBC:zx F6:INC:zx F8:SED:i F9:SBC:wy FD:SBC:wx FE:INC:wx'}
LENGTH={k:v for v,ks in [(1,['i','a']),(2,['z','zx','zy','n','ix','iy','r']),(3,['w','wx','wy','ind'])] for k in ks}
for row in ROWS.values():
    for item in row.split():
        op,m,mode=item.split(':');TABLE[int(op,16)]=(m,mode,LENGTH[mode])
def decode(data,offset=0,base=0):
    b=data[offset];m,mode,n=TABLE.get(b,('.byte','i',1))
    raw=data[offset:offset+n]
    if len(raw)<n:return '.byte '+','.join('$%02X'%b for b in raw),len(raw)
    v=int.from_bytes(raw[1:],'little');s=''
    if m=='.byte':s='$%02X'%b
    elif mode=='a':s='A'
    elif mode=='n':s='#$%02X'%v
    elif mode in ('z','zx','zy'):s='$%02X'%v+({'zx':',X','zy':',Y'}.get(mode,''))
    elif mode in ('w','wx','wy'):s='$%04X'%v+({'wx':',X','wy':',Y'}.get(mode,''))
    elif mode=='ind':s='($%04X)'%v
    elif mode=='ix':s='($%02X,X)'%v
    elif mode=='iy':s='($%02X),Y'%v
    elif mode=='r':s='$%04X'%((base+offset+2+(v if v<128 else v-256))&65535)
    return m+(' '+s if s else ''),n

def listing(data,start,end,base):
    o=start-base
    while o<min(end-base,len(data)):
        text,n=decode(data,o,base)
        yield '%04X  %-9s %s'%((base+o)&65535,data[o:o+n].hex(' ').upper(),text);o+=n
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=pathlib.Path);p.add_argument('--base',type=lambda x:int(x,0),default=0x8000);p.add_argument('--start',type=lambda x:int(x,0));p.add_argument('--end',type=lambda x:int(x,0));a=p.parse_args();d=a.file.read_bytes();print('\n'.join(listing(d,a.start or a.base,a.end or(a.base+len(d)),a.base)))
