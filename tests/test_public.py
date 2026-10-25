"""Public unit checks. No original ROM, audio or upstream checkout required."""
import hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_audit import parse_ines,digest,CANONICAL
from create_title_asset import encode,decode
from PIL import Image
class PublicTests(unittest.TestCase):
    def cartridge(self,prg=1,chr_banks=1,flags6=0,flags7=0,extra=None):
        h=bytearray(b'NES\x1a'+bytes(12));h[4:8]=bytes([prg,chr_banks,flags6,flags7])
        if extra:
            for index,value in extra.items():h[index]=value
        return bytes(h)+bytes(512 if flags6&4 else 0)+bytes(prg*16384+chr_banks*8192)
    def test_ines_offsets(self):
        r=parse_ines(self.cartridge(2,4,0x30));self.assertEqual((r['mapper'],r['prg_offset'],r['chr_offset']),(3,16,32784))
    def test_trainer_offsets(self):
        self.assertEqual(parse_ines(self.cartridge(flags6=4))['prg_offset'],528)
    def test_truncated_cartridge_rejected(self):
        with self.assertRaises(ValueError):parse_ines(self.cartridge()[:-1])
    def test_wrong_header_rejected(self):
        with self.assertRaises(ValueError):parse_ines(b'not a cartridge')
    def test_nes2_mapper_bits(self):
        r=parse_ines(self.cartridge(flags6=0x50,flags7=0x38,extra={8:2}))
        self.assertEqual(r['mapper'],0x235);self.assertTrue(r['nes2'])
    def test_nes2_exponent_sizes_rejected(self):
        with self.assertRaises(ValueError):parse_ines(self.cartridge(flags7=8,extra={9:15}))
    def test_digest_known_fixture(self):
        self.assertEqual(digest(b'123456789')['crc32'],'cbf43926')
        self.assertEqual(digest(b'123456789')['sha256'],hashlib.sha256(b'123456789').hexdigest())
    def test_four_canonical_source_hashes(self):
        self.assertEqual(len(CANONICAL),4)
        for value,size in CANONICAL.values():
            self.assertEqual(len(value),64);int(value,16);self.assertIn(size,(131072,262144))
    def test_title_roundtrip_on_synthetic_pattern(self):
        im=Image.new('P',(256,240))
        for y in range(240):
            for x in range(256):im.putpixel((x,y),(x//2+y//2)%4)
        chrdata,nt,count=encode(im)
        self.assertEqual(len(chrdata),4096);self.assertEqual(len(nt),1024)
        self.assertEqual(decode(chrdata,nt).tobytes(),im.tobytes());self.assertLessEqual(count,256)
    def test_no_four_rom_launcher_contract(self):
        c=json.loads((ROOT/'manifests/campaign_contract.json').read_text())
        self.assertFalse(c['rom_launcher']);self.assertTrue(c['one_native_6502_runtime']);self.assertEqual(len(c['order']),4)
    def test_cheat_menu_is_not_claimed_complete(self):
        c=json.loads((ROOT/'manifests/content_coverage.json').read_text())
        self.assertFalse(c['full_game_complete']);self.assertFalse(c['silicon_forge_menu_implemented'])
    def test_suno_limit(self):
        text=(ROOT/'audio/SUNO_STYLE.txt').read_text().strip();self.assertTrue(0<len(text)<=1000)
    def test_four_pinned_sources(self):
        c=json.loads((ROOT/'evidence/source_catalog.json').read_text())
        pins=[r for r in c['repositories']if r.get('commit')]
        self.assertEqual(len(pins),4)
        for r in pins:self.assertEqual(len(r['commit']),40);int(r['commit'],16)
if __name__=='__main__':unittest.main(verbosity=2)
