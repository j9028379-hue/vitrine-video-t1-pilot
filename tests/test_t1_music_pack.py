import hashlib, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, FormatChecker
from adapter.t1_adapter import (
 load_music_selection_state, record_music_render_result, select_music_track_from_state,
 attach_music_track, attach_voice_track, build_render_plan, select_music_track,
)
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/T1_special_menu_music_pack_v1_0_0.json'
VOICE_CFG=ROOT/'config/T1_special_menu_voice_mix_v1_0_0.json'
EXPECTED=[239426,464383,406552,178406]
def h(rel): return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def load_config(): return json.loads(CFG.read_text())
def test_exact_approved_four_and_no_rejected_content_id_track():
 config=load_config(); tracks=config['tracks']
 template=json.loads((ROOT/'config/T1_special_menu_template_v1_0_0.json').read_text())
 assert config['audio_profile']==template['audio_profile']=='afrobeat_amapiano'
 assert [track['pixabay_id'] for track in tracks]==EXPECTED
 assert len(tracks)==4 and all(track['production_eligible'] for track in tracks)
 assert all(track['content_id_registered'] is False for track in tracks)
 assert 573944 not in [track['pixabay_id'] for track in tracks]
 assert all((ROOT/track['file']).is_file() for track in tracks)
def test_published_silent_base_fingerprints_remain_recorded_and_capture_is_unchanged():
 config=load_config(); base=config['non_destructive_base']
 # These are the immutable public Release asset digests.  The repository's
 # canonical JSON may gain catalogue-only metadata without rewriting that Release.
 assert base['canonical_silent_template_sha256']=='5a742abf8307b6347d28e6eb7d540b8d17e88482c3548422affa8e54c38d7b1b'
 assert base['silent_package_manifest_sha256']=='e1148f3d3fea0259072632b3a5e3d5db12340f3eb176b19cd8512329b2bd29c0'
 assert base['base_files_must_remain_unchanged'] is True
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


def test_casino_rotation_never_repeats_the_previous_successful_track():
 config=load_config(); previous=None; observed=[]
 for index in range(256):
  chosen=select_music_track(config,render_job_id=f'production-{index:04d}',previous_variant_id=previous)
  assert chosen['id']!=previous
  observed.append(chosen['id']); previous=chosen['id']
 assert set(observed)==set(config['selection_contract']['allowed_variant_ids'])
 assert config['selection_contract']['automatic_candidate_count_after_first_render']==3


def test_explicit_selection_cannot_bypass_the_no_repeat_rule():
 config=load_config(); previous='t1_music_178406'
 with pytest.raises(ValueError,match='immédiate interdite'):
  select_music_track(config,render_job_id='job',requested_variant_id=previous,previous_variant_id=previous)
 with pytest.raises(ValueError,match='précédente inconnue'):
  select_music_track(config,render_job_id='job',previous_variant_id='t1_music_573944')
 chosen=select_music_track(config,render_job_id='job',requested_variant_id='t1_music_239426',previous_variant_id=previous)
 assert chosen['id']=='t1_music_239426'


def test_persistent_state_advances_only_after_success_and_survives_reload(tmp_path):
 config=load_config(); state_path=tmp_path/'music-state.json'
 first=select_music_track_from_state(config,render_job_id='state-job-1',state_path=state_path)
 failed=record_music_render_result(config,state_path=state_path,render_job_id='state-job-1',selected_music_id=first['id'],succeeded=False)
 assert failed['last_successful_music_id'] is None and not state_path.exists()
 committed=record_music_render_result(config,state_path=state_path,render_job_id='state-job-1',selected_music_id=first['id'],succeeded=True)
 assert committed['successful_render_count']==1
 assert load_music_selection_state(state_path)==committed
 second=select_music_track_from_state(config,render_job_id='state-job-2',state_path=state_path)
 assert second['id']!=first['id']
 unchanged=record_music_render_result(config,state_path=state_path,render_job_id='state-job-2',selected_music_id=second['id'],succeeded=False)
 assert unchanged==committed and load_music_selection_state(state_path)==committed


def test_persistent_state_rejects_explicit_repeat_and_success_callback_is_idempotent(tmp_path):
 config=load_config(); state_path=tmp_path/'music-state.json'; selected=config['tracks'][0]['id']
 first=record_music_render_result(config,state_path=state_path,render_job_id='success-1',selected_music_id=selected,succeeded=True)
 assert record_music_render_result(config,state_path=state_path,render_job_id='success-1',selected_music_id=selected,succeeded=True)==first
 with pytest.raises(ValueError,match='immédiate interdite'):
  select_music_track_from_state(config,render_job_id='success-2',state_path=state_path,requested_variant_id=selected)
 with pytest.raises(ValueError,match='immédiate interdite'):
  record_music_render_result(config,state_path=state_path,render_job_id='success-2',selected_music_id=selected,succeeded=True)
 schema=json.loads((ROOT/'schemas/T1_music_selection_state.schema.json').read_text())
 Draft202012Validator(schema).validate(load_music_selection_state(state_path))


def test_concurrent_duplicate_success_is_serialized_and_rejected_once(tmp_path):
 config=load_config(); state_path=tmp_path/'music-state.json'; selected=config['tracks'][0]['id']
 def commit(job_id):
  try:
   record_music_render_result(config,state_path=state_path,render_job_id=job_id,selected_music_id=selected,succeeded=True)
   return 'committed'
  except ValueError:
   return 'rejected'
 with ThreadPoolExecutor(max_workers=2) as executor:
  outcomes=list(executor.map(commit,['concurrent-t1-1','concurrent-t1-2']))
 assert sorted(outcomes)==['committed','rejected']
 state=load_music_selection_state(state_path)
 assert state['last_successful_music_id']==selected and state['successful_render_count']==1


def test_persistent_state_rejects_unknown_last_success(tmp_path):
 state_path=tmp_path/'music-state.json'
 state_path.write_text(json.dumps({'schema_version':'1.0.0','last_successful_music_id':'t1_music_573944','last_successful_render_job_id':'bad-job','successful_render_count':1}))
 with pytest.raises(ValueError,match='inconnue'):
  load_music_selection_state(state_path)


def test_adapter_attaches_local_music_without_changing_merchant_fields():
 config=load_config()
 v12=json.loads((ROOT/'specs/T1_ENGINEERING_SPEC_V1_2.json').read_text())
 v62=json.loads((ROOT/'specs/restaurants_maquis_T1.spec_v6_2.public-safe.json').read_text())
 raw=json.loads((ROOT/'demo/T1_demo_input.json').read_text())
 plan=build_render_plan(v12,v62,raw); before=dict(plan['fields'])
 attach_music_track(plan,config,render_job_id='job-match-out',requested_variant_id='t1_music_178406')
 assert plan['fields']==before and plan['output']['audio'] is True
 assert plan['audio_track']['audio_profile']=='afrobeat_amapiano'
 assert plan['audio_track']['pixabay_id']==178406
 assert plan['audio_track']['file'].endswith('t1_178406_120bpm_30s.mp3')
 assert plan['audio_track']['previous_variant_id'] is None
 assert plan['audio_track']['last_successful_music_id'] is None
 assert plan['audio_track']['no_immediate_repeat'] is True
 assert plan['audio_track']['state_update_policy']=='after_success_only'
 assert plan['audio_track']['network_required'] is False
 assert plan['audio_track']['start_f']==0 and plan['audio_track']['end_f_exclusive']==900
def test_voice_mix_contract_matches_its_schema():
 voice=json.loads(VOICE_CFG.read_text())
 schema=json.loads((ROOT/'schemas/T1_voice_mix.schema.json').read_text())
 Draft202012Validator(schema,format_checker=FormatChecker()).validate(voice)

def test_voice_stem_and_ducking_attach_without_changing_visual_timing():
 config=load_config(); voice=json.loads(VOICE_CFG.read_text())
 v12=json.loads((ROOT/'specs/T1_ENGINEERING_SPEC_V1_2.json').read_text())
 v62=json.loads((ROOT/'specs/restaurants_maquis_T1.spec_v6_2.public-safe.json').read_text())
 raw=json.loads((ROOT/'demo/T1_demo_input.json').read_text())
 plan=build_render_plan(v12,v62,raw); original_shots=plan['shots']; original_overlays=plan['overlays']
 attach_music_track(plan,config,render_job_id='voice-test',requested_variant_id='t1_music_178406')
 attach_voice_track(plan,voice)
 assert plan['shots']==original_shots and plan['overlays']==original_overlays
 assert plan['voice_track']['enabled'] is True and plan['voice_track']['network_required'] is False
 assert plan['voice_track']['start_f']==0 and plan['voice_track']['end_f_exclusive']==900
 assert [p['start_f'] for p in plan['voice_track']['placements']]==[36,204,441,654]
 assert plan['audio_track']['runtime_no_speech_gain_db']==-3
 assert plan['audio_track']['runtime_speech_gain_db']==-10
 assert plan['audio_track']['duck_attack_ms']==120 and plan['audio_track']['duck_release_ms']==450
 assert plan['audio_track']['final_ducking_status']=='validated_offline_reference_mix_v1'
 assert plan['audio_mix']['music_variant_count']==4 and plan['audio_mix']['sfx'] is False

def test_audio_qc_is_green_for_every_track():
 config=load_config(); assert config['quality_gate']['qc_all_pass'] is True
 for track in config['tracks']:
  qc=track['qc']
  assert qc['samples']==1323000 and qc['duration_s_measured']==30.0
  assert qc['pass_duration_exact'] and qc['pass_bpm_118_122']
  assert qc['pass_true_peak_le_minus_0_7'] and qc['pass_lufs_minus_17_7_to_minus_16_7']
def test_voice_music_reference_mix_qc_is_green_for_exact_four_variants():
 report=json.loads((ROOT/'reports/T1_voice_music_v1_validation.json').read_text())
 assert report['status']=='PASS' and report['duration_s']==30.0
 assert [item['pixabay_id'] for item in report['variants']]==EXPECTED
 assert report['ducking']['minimum_music_gain_db']==-10
 assert report['ducking']['maximum_music_gain_db']==-3
 assert report['ducking']['duck_attack_ms']==120 and report['ducking']['duck_release_ms']==450
 assert report['voice']['stem']['decoded_samples']==1_440_000
 for item in report['variants']:
  assert item['status']=='PASS'
  assert item['master_wav']['decoded_samples']==1_440_000
  assert item['master_wav']['clipped_sample_count']==0
  assert item['preview_mp4']['clipped_sample_count']==0
  assert item['preview_mp4']['visual_source_bitstream_identical'] is True
  assert item['intelligibility_proxy']['aggregate_speech_to_music_db']>=4

def test_validator_accepts_release():
 subprocess.run([sys.executable,str(ROOT/'tools/validate_t1_music_pack.py')],cwd=ROOT,check=True)
