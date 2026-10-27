"""Packaging invariants; no replacement for game-mechanics tests."""
import hashlib,json,pathlib,shutil,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from checkpoint import check_files
try:
    from verify_selected_inputs import verify
except ModuleNotFoundError:
    verify=None  # private package only; public checkout skips these checks

class CheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'manifests/checkpoint.json').is_file():
            raise unittest.SkipTest('Lean private packaging profile is not present')
        if verify is None or not (ROOT/'private_sources').is_dir():
            raise unittest.SkipTest('Private recovery package (verify_selected_inputs, private_sources) is required')
        cls.profile=json.loads((ROOT/'manifests/checkpoint.json').read_text())
    def test_exact_playable_rom(self):
        data=(ROOT/self.profile['rom']).read_bytes()
        self.assertEqual(len(data),self.profile['rom_bytes'])
        self.assertEqual(hashlib.sha256(data).hexdigest(),self.profile['rom_sha256'])
    def test_gameplay_core_modules_unchanged(self):
        for path,sha in self.profile['unchanged_game_sources'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha,path)
    def test_checkpoint_gameplay_changes_are_pinned(self):
        self.assertTrue(self.profile.get('gameplay_changed'), 'This checkpoint has native source changes')
        for path,sha in self.profile['checkpoint_changed_sources'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha,path)
        self.assertIn('src/native_stage2.s',self.profile['checkpoint_changed_sources'])
    def test_source_coverage_cannot_claim_finished_anthology(self):
        ledger=json.loads((ROOT/'manifests/content_coverage.json').read_text())
        self.assertFalse(ledger['full_game_complete'])
        self.assertEqual(len(ledger['chapters']),4)
        self.assertTrue(all(not chapter['nes_gameplay_complete'] for chapter in ledger['chapters']))
    def test_exact_selected_source_set(self):
        data=verify()
        self.assertEqual((data['inventory_count'],data['msx_count'],data['nes_count']),(10,4,6))
    def test_no_unselected_private_images(self):
        selected=json.loads((ROOT/'manifests/selected_sources.json').read_text())
        actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'private_sources').iterdir() if p.is_file()}
        self.assertEqual(actual,{r['path'] for r in selected.values()})
    def test_corrupt_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);(root/'manifests').mkdir()
            shutil.copy2(ROOT/'manifests/selected_sources.json',root/'manifests/selected_sources.json')
            shutil.copytree(ROOT/'private_sources',root/'private_sources')
            target=next((root/'private_sources').glob('*.rom'))
            raw=bytearray(target.read_bytes());raw[512]^=1;target.write_bytes(raw)
            with self.assertRaises(ValueError):verify(root)
    def test_file_manifest_detects_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);(root/'sample.txt').write_bytes(b'known')
            mf=root/'manifest.json';mf.write_text(json.dumps({'files':[{'path':'sample.txt','bytes':5,'sha256':hashlib.sha256(b'known').hexdigest()}]}))
            self.assertEqual(check_files(root,mf),1)
            (root/'sample.txt').write_bytes(b'wrong')
            with self.assertRaises(ValueError):check_files(root,mf)
    def test_file_manifest_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);mf=root/'manifest.json'
            mf.write_text(json.dumps({'files':[{'path':'../bad','bytes':0,'sha256':'0'*64}]}))
            with self.assertRaises(ValueError):check_files(root,mf)

if __name__=='__main__':unittest.main(verbosity=2)
