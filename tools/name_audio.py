#!/usr/bin/env python3
"""Attach published titles; keep command-mapping confidence explicit."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
G1=['Beginning Of The History (Air Battle)','Challenger 1985 (Stage 1)','Beat Back (Stage 2)','Blank Mask (Stage 3)','Free Flyer (Stage 4)','Mazed Music (Stage 5)','Mechanical Globule (Stage 6)','Final Attack (Stage 7)','Aircraft Carrier (Boss)']
G2=['Equipment (Select)','TABIDACHI (Air Battle)','Burning Heat (Stage 1)','The Final Enemy (Boss)','Fortress (Stage 2)','Heavy Blow (Stage 3-1)','Dead End (Stage 3-2)','The Old Stone Age (Stage 4)','GRADIUS 1 BOSS Theme (Stage 5-1)','SALAMANDER BOSS Theme (Stage 5-2)','Over Heat (Stage 6)','Something Ghostly (Stage 7)','Take Care! (Last Boss)','Farewell (Ending)','GAME OVER']
SAL={0x3a:'Combat (Unused)',0x25:'Power of Anger (Stage 1)',0x28:'Starfield (Stage 2)',0x2b:'Planet RATIS (Stage 3)',0x2e:'Burn the Wind (Stage 4)',0x31:'Thunderbolt (Stage 5)',0x37:'Destroy Them All (Stage 6)',0x22:'Aircraft Carrier (Gradius Boss)',0x3d:'Poison of Snake (Boss)',0x40:'Peace Again (Ending)',0x43:'Crystal Forever (Game Over)'}
URL={'gradius':'https://ototoy.jp/_/default/p/3649893','gradius2_fc':'https://ototoy.jp/_/default/p/3649890','salamander_fc':'https://ototoy.jp/_/default/p/3649892'}
def main():
 for folder in sorted((ROOT/'audio').glob('*/*')):
  p=folder/'tracks.json'
  if not p.is_file():continue
  d=json.loads(p.read_text())
  for t in d['tracks']:
   slug=folder.name;cmd=t['command'];title=None
   if slug=='gradius':
    if t['index']<9:title=G1[t['index']]
    elif cmd==0xb2:title='All Pattern Clear (Ending)'
    elif cmd==0xaf:title='Game Over'
   elif slug=='gradius2_fc':title=G2[t['index']]
   elif slug=='salamander_fc':title=SAL.get(cmd)
   if title:
    t.update(title=title,title_status='published_title',title_source=URL[slug],title_source_accessed='2026-10-25',command_mapping_status='catalogue_order_inference_not_full_gameplay_verified' if slug=='gradius2_fc' else 'ROM_context_plus_published_catalogue')
   elif slug=='salamander_fc' and cmd==0x34:
    t.update(title='Temple Finale (Stage 5 Alternate Cue)',title_status='contextual_not_official',command_mapping_status='ROM_call_site_bank6_AE29')
   elif slug in ('nemesis_msx','nemesis2_msx','salamander_msx'):
    t['command_mapping_status']='upstream_audio_configuration_not_full_gameplay_verified'
    if 'Score Sequence' in t['title'] or 'Stage Score' in t['title']:
     t['title']='Unidentified Source Cue %02X'%cmd
     t['title_status']='neutral_identifier_context_unresolved'
   t['source_command_hex']='%02X'%cmd
  d['coverage_statement']='Selected source commands only; presence of sound is not evidence of complete musical coverage or a finished NES conversion.'
  p.write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
