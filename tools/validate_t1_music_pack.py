#!/usr/bin/env python3
"""Fail-closed validator for T1's approved four-track offline music sidecar."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/T1_special_menu_music_pack_v1_0_0.json'
SCHEMA=ROOT/'schemas/T1_music_pack.schema.json'
STATE_SCHEMA=ROOT/'schemas/T1_music_selection_state.schema.json'
MANIFEST=ROOT/'packages/t1-special-menu-music-v1/manifest.json'
EXPECTED_IDS=[239426,464383,406552,178406]
PUBLISHED_BASE={
 'canonical_silent_template_sha256':'5a742abf8307b6347d28e6eb7d540b8d17e88482c3548422affa8e54c38d7b1b',
 'silent_package_manifest_sha256':'e1148f3d3fea0259072632b3a5e3d5db12340f3eb176b19cd8512329b2bd29c0',
 'capture_guide_sha256':'93a807f88e0e0f909cb589e8539419a4d1c387c12bc1b9966ba7dbe1a936075c',
}
def digest(path:Path)->str:
 return hashlib.sha256(path.read_bytes()).hexdigest()
def fail(message:str)->bool:
 print('FAIL:',message,file=sys.stderr); return False
def ffprobe(path:Path)->dict:
 command=['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,sample_rate,channels,bit_rate','-of','json',str(path)]
 return json.loads(subprocess.check_output(command,text=True))
def validate()->bool:
 ok=True
 cfg=json.loads(CFG.read_text()); schema=json.loads(SCHEMA.read_text()); state_schema=json.loads(STATE_SCHEMA.read_text())
 for label,candidate in [('music pack',schema),('selection state',state_schema)]:
  try: Draft202012Validator.check_schema(candidate)
  except Exception as error: ok=fail(f'{label} schema is invalid: {error}') and ok
 errors=sorted(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(cfg),key=lambda e:list(e.path))
 for error in errors: ok=fail(f'schema {list(error.path)}: {error.message}') and ok
 initial_state={'schema_version':'1.0.0','last_successful_music_id':None,'last_successful_render_job_id':None,'successful_render_count':0,'successful_render_jobs':{}}
 for error in Draft202012Validator(state_schema).iter_errors(initial_state): ok=fail(f'initial state schema: {error.message}') and ok
 ids=[track['pixabay_id'] for track in cfg['tracks']]
 if cfg.get('audio_profile')!='afrobeat_amapiano': ok=fail('audio profile does not match the delivered Afrobeat/Amapiano catalogue') and ok
 if ids!=EXPECTED_IDS: ok=fail(f'approved IDs/order mismatch: {ids}') and ok
 if any(track['pixabay_id']==573944 for track in cfg['tracks']): ok=fail('rejected track 573944 is still selectable') and ok
 base=cfg.get('non_destructive_base',{})
 for field,expected in PUBLISHED_BASE.items():
  if base.get(field)!=expected: ok=fail(f'published silent Release fingerprint changed: {field}') and ok
 if base.get('commit')!='cab2aa2a4a841341c9e84aeb08e243ea9baec0f4' or base.get('base_files_must_remain_unchanged') is not True: ok=fail('published silent Release provenance changed') and ok
 capture=ROOT/'capture-guide/consignes_T1.json'
 if not capture.is_file() or digest(capture)!=PUBLISHED_BASE['capture_guide_sha256']: ok=fail('capture guide changed') and ok
 selection=cfg.get('selection_contract',{})
 if selection.get('allowed_variant_ids')!=[f't1_music_{item}' for item in EXPECTED_IDS]: ok=fail('strict rotation order differs from the approved four-track order') and ok
 if selection.get('default_variant_id')!='t1_music_239426': ok=fail('initial state must select the first approved track') and ok
 if selection.get('runtime_mode')!='production auto and explicit selection follow the strict approved order 1→2→3→4 after each successful render': ok=fail('runtime mode does not require the strict four-step cycle') and ok
 if not selection.get('no_immediate_repeat'): ok=fail('immediate music repetition is not forbidden') and ok
 if selection.get('explicit_selection_policy')!='exact_successor_only': ok=fail('explicit music selection can bypass the exact successor') and ok
 if selection.get('automatic_candidate_count_after_first_render')!=1: ok=fail('automatic rotation must select exactly the next track in the strict four-step cycle') and ok
 if selection.get('selection_state_scope')!='caller-owned persistent JSON' or selection.get('selection_state_schema')!='schemas/T1_music_selection_state.schema.json' or selection.get('idempotency_ledger_key')!='successful_render_jobs' or selection.get('state_update_policy')!='after_success_only' or selection.get('failed_render_state_policy')!='unchanged' or selection.get('network_required') is not False: ok=fail('music rotation must use the offline persistent idempotent after-success-only contract') and ok
 for track in cfg['tracks']:
  path=ROOT/track['file']; evidence=ROOT/track['evidence_file']
  if not path.is_file(): ok=fail(f'missing audio {path}') and ok; continue
  if digest(path)!=track['sha256'] or path.stat().st_size!=track['bytes']: ok=fail(f'hash/size mismatch {path}') and ok
  if not evidence.is_file(): ok=fail(f'missing source evidence {evidence}') and ok
  else:
   ev=json.loads(evidence.read_text())
   ev_cid=ev.get('content_id_registered')
   if ev_cid is None:
    props=ev.get('json_ld',{}).get('additionalProperty',[])
    ev_cid=any(item.get('name')=='Content ID Registered' and item.get('value') is True for item in props)
   if ev_cid: ok=fail(f'Content ID evidence found for {track["pixabay_id"]}') and ok
  meta=ffprobe(path); stream=meta['streams'][0]
  if stream['codec_name']!='mp3' or int(stream['sample_rate'])!=44100 or int(stream['channels'])!=2: ok=fail(f'format mismatch {path}') and ok
  if abs(float(meta['format']['duration'])-30)>0.05: ok=fail(f'container duration mismatch {path}') and ok
  pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','s16le','-acodec','pcm_s16le','-'])
  decoded_samples=len(pcm)//(2*int(stream['channels']))
  if decoded_samples!=1323000: ok=fail(f'decoded sample count mismatch {path}: {decoded_samples}') and ok
  qc=track['qc']
  qpass=(qc['pass_duration_exact'] and qc['pass_bpm_118_122'] and qc['pass_true_peak_le_minus_0_7'] and qc['pass_lufs_minus_17_7_to_minus_16_7'])
  if not qpass: ok=fail(f'audio QC failed {path}') and ok
  if track['content_id_registered'] or not track['production_eligible']: ok=fail(f'track is not production-ready {path}') and ok
 manifest=json.loads(MANIFEST.read_text())
 gates=manifest['release_gates']
 if gates['approved_pixabay_ids']!=EXPECTED_IDS or not gates['all_tracks_production_ready'] or gates['content_id_track_count']!=0: ok=fail('manifest release gates are inconsistent') and ok
 artifact_paths=[item['path'] for item in manifest['artifacts']]
 if any('573944' in rel for rel in artifact_paths): ok=fail('rejected 573944 artifact is bundled') and ok
 for artifact in manifest['artifacts']:
  path=ROOT/artifact['path']
  if not path.is_file() or digest(path)!=artifact['sha256'] or path.stat().st_size!=artifact['bytes']: ok=fail(f'package artifact mismatch {artifact["path"]}') and ok
 source=json.loads((ROOT/'audio/music/t1-afrobeat-amapiano-v1/source_manifest.json').read_text())
 if source['approved_ids']!=EXPECTED_IDS or any(t['content_id_registered'] for t in source['tracks']): ok=fail('source manifest is inconsistent') and ok
 return ok
if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.parse_args()
 good=validate(); print('PASS: T1 music pack contains exactly four approved, Content-ID-free, production-ready tracks.' if good else 'FAIL: T1 music pack rejected.')
 raise SystemExit(0 if good else 1)
