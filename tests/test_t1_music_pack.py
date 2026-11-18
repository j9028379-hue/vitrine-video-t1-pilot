import hashlib, json, subprocess, sys
from pathlib import Path
import pytest
from adapter.t1_adapter import attach_music_track, build_render_plan, select_music_track
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/T1_special_menu_music_pack_v1_0_0.json'
EXPECTED=[239426,464383,406552,178406]
def h(rel): return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def load_config(): return json.loads(CFG.read_text())
def test_exact_approved_four_and_no_rejected_content_id_track():
 config=load_config(); tracks=config['tracks']
 assert [track['pixabay_id'] for track in tracks]==EXPECTED
 assert len(tracks)==4 and all(track['production_eligible'] for track in tracks)
 assert all(track['content_id_registered'] is False for track in tracks)
 assert 573944 not in [track['pixabay_id'] for track in tracks]
 assert all((ROOT/track['file']).is_file() for track in tracks)
def test_published_silent_base_is_byte_identical():
 assert h('config/T1_special_menu_template_v1_0_0.json')=='5a742abf8307b6347d28e6eb7d540b8d17e88482c3548422affa8e54c38d7b1b'
 assert h('packages/t1-special-menu-v1/manifest.json')=='e1148f3d3fea0259072632b3a5e3d5db12340f3eb176b19cd8512329b2bd29c0'
 assert h('capture-guide/consignes_T1.json')=='93a807f88e0e0f909cb589e8539419a4d1c387c12bc1b9966ba7dbe1a936075c'
def test_selection_is_deterministic_and_uses_all_four_approved_tracks():
 config=load_config()
 a=select_music_track(config,render_job_id='render-job-stable')
 b=select_music_track(config,render_job_id='render-job-stable')
 assert a['id']==b['id'] and a['pixabay_id'] in EXPECTED
 for track in config['tracks']:
  chosen=select_music_track(config,render_job_id='ignored',requested_variant_id=track['id'])
  assert chosen['pixabay_id']==track['pixabay_id']
 with pytest.raises(ValueError,match='inconnue'):
  select_music_track(config,render_job_id='job',requested_variant_id='t1_music_573944')
def test_adapter_attaches_local_music_without_changing_merchant_fields():
 config=load_config()
 v12=json.loads((ROOT/'specs/T1_ENGINEERING_SPEC_V1_2.json').read_text())
 v62=json.loads((ROOT/'specs/restaurants_maquis_T1.spec_v6_2.public-safe.json').read_text())
 raw=json.loads((ROOT/'demo/T1_demo_input.json').read_text())
 plan=build_render_plan(v12,v62,raw); before=dict(plan['fields'])
 attach_music_track(plan,config,render_job_id='job-match-out',requested_variant_id='t1_music_178406')
 assert plan['fields']==before and plan['output']['audio'] is True
 assert plan['audio_track']['pixabay_id']==178406
 assert plan['audio_track']['file'].endswith('t1_178406_120bpm_30s.mp3')
 assert plan['audio_track']['network_required'] is False
 assert plan['audio_track']['start_f']==0 and plan['audio_track']['end_f_exclusive']==900
def test_audio_qc_is_green_for_every_track():
 config=load_config(); assert config['quality_gate']['qc_all_pass'] is True
 for track in config['tracks']:
  qc=track['qc']
  assert qc['samples']==1323000 and qc['duration_s_measured']==30.0
  assert qc['pass_duration_exact'] and qc['pass_bpm_118_122']
  assert qc['pass_true_peak_le_minus_0_7'] and qc['pass_lufs_minus_17_7_to_minus_16_7']
def test_validator_accepts_release():
 subprocess.run([sys.executable,str(ROOT/'tools/validate_t1_music_pack.py')],cwd=ROOT,check=True)
