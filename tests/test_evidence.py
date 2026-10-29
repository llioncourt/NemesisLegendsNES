from __future__ import annotations
import hashlib,json,pathlib,struct,sys,unittest,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_audit import parse_ines,digest
from extract_nemesis_msx import Extractor,REV
from create_title_asset import decode
class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not (ROOT/'private_sources').is_dir():raise unittest.SkipTest('Private originals are required; run the evidence rebuilder first.')
  cls.selected=json.loads((ROOT/'manifests/selected_sources.json').read_text());cls.audit=json.loads((ROOT/'reports/source_audit.json').read_text())
 def original(self,slug):return (ROOT/self.selected[slug]['path']).read_bytes()
 def test_inventory_counts(self):
  expected=(10,4,6) if self.audit.get('scope')=='selected-only' else (137,131,6)
  self.assertEqual((self.audit['inventory_count'],self.audit['msx_count'],self.audit['nes_count']),expected)
  self.assertEqual(len(json.loads((ROOT/'manifests/input_inventory.json').read_text())),expected[0])
 def test_selected_hashes(self):
  for slug,s in self.selected.items():self.assertEqual(hashlib.sha256(self.original(slug)).hexdigest(),s['sha256'])
 def test_nemesis3_exact_canonical_is_selected(self):
  self.assertEqual(self.audit['missing'],[])
  data=self.original('nemesis3_msx')
  self.assertEqual(len(data),262144)
  self.assertEqual(hashlib.sha1(data).hexdigest(),'7393f677e0fae5fc83071c6b74756117b7d75e2d')
  self.assertEqual(hashlib.sha256(data).hexdigest(),'fb4f66bcc3eabaf7eea6b91d1e2f5a15aa2f80a31a056af41d948b32646877a9')
 def test_nes_mapper_identities(self):
  expected={'gradius_nes_jp':3,'gradius_nes_us':3,'gradius2_fc':25,'salamander_fc':73,'lifeforce_nes_us':2,'lifeforce_nes_us_rev1':2}
  for slug,mapper in expected.items():self.assertEqual(parse_ines(self.original(slug))['mapper'],mapper)
 def test_reject_truncated_ines(self):
  with self.assertRaises(ValueError):parse_ines(b'NES\x1a'+bytes([2,1])+bytes(10))
 def test_reject_not_ines(self):
  with self.assertRaises(ValueError):parse_ines(b'wrong')
 def test_original_z80_mirror_signatures(self):
  rom=self.original('nemesis_msx')
  for a,b in [(0x434d,'dd6e0326002929292201e1'),(0x4454,'dd6e002600292929'),(0x43f2,'2100e3ed5b01e10608cb1e8f10fb77231b7ab320f2c9')]:self.assertEqual(rom[a-0x4000:a-0x4000+len(bytes.fromhex(b))],bytes.fromhex(b))
 def test_first_mirror_record(self):
  rom=self.original('nemesis_msx');p=5*8192+0x96ae-0x8000;self.assertEqual(rom[p:p+4],bytes.fromhex('63682905'))
 def synthetic_mirror(self,vertical):
  ex=Extractor(self.original('nemesis_msx'));table={0x9202:0,0x9203:0x93,0x9300:0x10,0x9301:0x20,0x9302:0x24,0x9303:1,0x9304:0};old=ex.byte
  ex.byte=lambda bank,addr:table[addr] if bank==5 and addr in table else old(bank,addr)
  v=bytearray(0x4000);pat=bytes([1,2,4,8,16,32,64,128]);col=bytes([0x12,0x34,0x56,0x78,0x9a,0xbc,0xde,0xf1]);v[0x2080:0x2088]=pat;v[0x80:0x88]=col;ex.mirror_table(v,0x9200,1,vertical);return v,pat,col
 def test_horizontal_preserves_colors(self):
  v,p,c=self.synthetic_mirror(False);self.assertEqual(v[0x2100:0x2108],bytes(REV[b]for b in p));self.assertEqual(v[0x100:0x108],c)
 def test_vertical_reverses_both_rows(self):
  v,p,c=self.synthetic_mirror(True);self.assertEqual(v[0x2100:0x2108],p[::-1]);self.assertEqual(v[0x100:0x108],c[::-1])
 def test_map_shapes(self):
  for game in ['nemesis','nemesis2']:
   folders=list((ROOT/'assets/msx'/game).glob('stage_*' if game=='nemesis' else 'map_*'));folders=[f for f in folders if f.is_dir()];self.assertEqual(len(folders),12)
   for f in folders:
    m=json.loads((f/'stage.json').read_text());width=m.get('preview_columns',m.get('columns'));self.assertEqual(len((f/'terrain_rows.bin').read_bytes()),22*width);self.assertEqual(len((f/'source_vram.bin').read_bytes()),16384)
 def test_nemesis2_packed_records(self):
  r=json.loads((ROOT/'assets/msx/nemesis2/mirror_records.json').read_text());self.assertTrue(any(x['record_bytes']==3 for x in r));self.assertTrue(any(x['record_bytes']==4 for x in r))
  for x in r:
   if x['record_bytes']==3:self.assertEqual(x['count'],x['flags']>>6)
 def test_global_tile_dictionary(self):
  base=ROOT/'assets/msx';b=(base/'global_source_indexed_tiles.bin').read_bytes();rows=json.loads((base/'global_source_indexed_tile_refs.json').read_text());self.assertEqual(len(b),len(rows)*64)
  for row in rows:self.assertEqual(hashlib.sha256(b[64*row['index']:64*(row['index']+1)]).hexdigest(),row['sha256'])
 def test_title_native_roundtrip(self):
  from PIL import Image
  f=ROOT/'assets/title';c=(f/'title.chr').read_bytes();n=(f/'title.nam').read_bytes();self.assertEqual(len(c),4096);self.assertEqual(len(n),1024);self.assertEqual(decode(c,n).tobytes(),Image.open(f/'title_native_asset.png').tobytes())
 def test_nsf_headers_and_counts(self):
  files=list((ROOT/'audio/native_nes').glob('*/*.nsf'));self.assertEqual(len(files),4);count=0  # Gradius, Gradius II, Salamander FC, Life Force (CP0019)
  for p in files:
   b=p.read_bytes();self.assertEqual(b[:5],b'NESM\x1a');count+=b[6];load,init,play=struct.unpack_from('<HHH',b,8);self.assertGreaterEqual(load,0x8000);self.assertLess(init-load,len(b)-128);self.assertLess(play-load,len(b)-128);self.assertEqual(b[123],0)
  self.assertEqual(count,82)
 def test_kss_not_renamed_nsf(self):
  files=list((ROOT/'audio/msx_reference').glob('*/*.kss'));self.assertEqual(len(files),4)  # Nemesis, Nemesis 2, Salamander, Nemesis 3 (CP0019)
  for p in files:
   b=p.read_bytes();self.assertEqual(b[:4],b'KSCC');load,size,init,play=struct.unpack_from('<HHHH',b,4);self.assertIn(load,(0x4000,0x6000));self.assertEqual(init,0xc000);self.assertEqual(play,0xc0e0);self.assertGreaterEqual(len(b),16+size)
 def test_audio_manifest_hashes(self):
  m=json.loads((ROOT/'audio/metadata.json').read_text())
  if m['track_count']==0:self.skipTest('MP3 rendering not requested; use --render-audio for this integration check.')
  self.assertEqual(m['track_count'],98);self.assertFalse(m['msx_to_nes_conversion_complete'])
  for t in m['tracks']:
   p=ROOT/t['mp3'];self.assertEqual(p.stat().st_size,t['bytes']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),t['sha256']);self.assertGreater(t['rendered_seconds'],0)
 def test_suno_limit(self):self.assertLessEqual(len((ROOT/'audio/SUNO_STYLE.txt').read_text().strip()),1000)
 def test_no_false_completion(self):
  m=json.loads((ROOT/'manifests/content_coverage.json').read_text())
  self.assertFalse(m['full_game_complete'])
  self.assertFalse(m['konami_code_implemented'])
  self.assertTrue(all(not c['nes_gameplay_complete'] for c in m['chapters']))
  # CP0004 changes the playable-component claim, not the completion gate.
  # Require its real binary and hash-matched passing gameplay evidence.
  if m['playable_game_rom']:
      rom=(ROOT/'build/native/Nemesis_Legends_CP0006.nes').read_bytes()
      self.assertEqual(rom[:4], b'NES\x1a')
      self.assertEqual((rom[6] >> 4) | (rom[7] & 240), 5)
      sha=hashlib.sha256(rom).hexdigest()
      for name in ('combat_unit_tests.json','native_integration_tests.json','stage_one_integration.json'):
          report=json.loads((ROOT/'reports/cp0006'/name).read_text())
          self.assertEqual(report['rom_sha256'],sha)
      combat=json.loads((ROOT/'reports/cp0006/combat_unit_tests.json').read_text())
      self.assertTrue(combat['passed'])
      self.assertTrue(combat['negative_control']['rejected'])
      gameplay=json.loads((ROOT/'reports/cp0006/native_integration_tests.json').read_text())
      self.assertTrue(all(c['passed'] for c in gameplay['checks']))
      self.assertTrue(m['custom_title_in_game'])
      self.assertFalse(m['chapters'][0]['first_stage_unassisted_clear_validated'])
 def test_original_input_archives(self):
  files=list((ROOT/'inputs').glob('*.zip'))
  if not files and json.loads((ROOT/'manifests/checkpoint.json').read_text()).get('original_archives_included') is False:self.skipTest('Original upload ZIPs are archived separately; the ten selected original images are hash-checked.')
  self.assertEqual(len(files),8)
  for p in files:
   with zipfile.ZipFile(p)as z:self.assertIsNone(z.testzip())
 def test_uploaded_archives_match_manifest(self):
  if not list((ROOT/'inputs').glob('*.zip')) and json.loads((ROOT/'manifests/checkpoint.json').read_text()).get('original_archives_included') is False:self.skipTest('Original upload ZIPs are not part of the lean checkpoint.')
  for item in json.loads((ROOT/'manifests/input_archives.json').read_text()):
   data=(ROOT/'inputs'/item['name']).read_bytes()
   self.assertEqual(len(data),item['bytes'])
   self.assertEqual(hashlib.sha256(data).hexdigest(),item['sha256'])
 def test_nemesis3_variants_do_not_replace_original(self):
  report=json.loads((ROOT/'reports/nemesis3_input_validation.json').read_text())
  self.assertEqual(report['rom_entries_in_upload'],16)
  self.assertEqual(sum(x['selected_canonical'] for x in report['variant_comparisons']),1)
  selected=next(x for x in report['variant_comparisons'] if x['selected_canonical'])
  self.assertEqual(selected['differing_bytes_in_common_prefix'],0)
  self.assertEqual(selected['size_delta_from_canonical'],0)
  self.assertFalse(report['nemesis3_gameplay_ported'])
  self.assertFalse(report['nemesis3_audio_ripped'])
if __name__=='__main__':unittest.main(verbosity=2)
