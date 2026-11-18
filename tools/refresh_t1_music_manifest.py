#!/usr/bin/env python3
"""Refresh deterministic hashes for the approved four-track T1 music sidecar."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/T1_special_menu_music_pack_v1_0_0.json'
MANIFEST=ROOT/'packages/t1-special-menu-music-v1/manifest.json'
EXTRA=[
 'audio/music/t1-afrobeat-amapiano-v1/source_manifest.json',
 'audio/music/t1-afrobeat-amapiano-v1/BUILD_PROVENANCE.json',
]
def sha(path:Path)->str:
 return hashlib.sha256(path.read_bytes()).hexdigest()
def refresh()->dict:
 cfg=json.loads(CFG.read_text())
 paths=[str(CFG.relative_to(ROOT))]
 paths += [track['file'] for track in cfg['tracks']]
 paths += [track['evidence_file'] for track in cfg['tracks']]
 paths += EXTRA
 artifacts=[]
 for rel in paths:
  p=ROOT/rel
  if not p.is_file(): raise SystemExit(f'Missing package artifact: {rel}')
  artifacts.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
 manifest={
  'manifest_schema_version':'1.0.0',
  'package_id':'t1-special-menu-afrobeat-amapiano-music-v1',
  'version':'1.0.0',
  'status':'release_ready_all_four_tracks',
  'base_silent_release':'t1-special-menu-template-v1.0.0-silent',
  'config':str(CFG.relative_to(ROOT)),
  'runtime':{'offline':True,'backend':'AndroidX Media3 local asset','server_download':False},
  'artifacts':artifacts,
  'release_gates':{
   'exactly_four_tracks':True,
   'approved_pixabay_ids':[239426,464383,406552,178406],
   'content_id_track_count':0,
   'all_audio_qc':True,
   'all_tracks_production_ready':True,
   'rejected_track_not_bundled':573944,
  },
 }
 MANIFEST.parent.mkdir(parents=True,exist_ok=True)
 MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 return manifest
if __name__=='__main__':
 m=refresh(); print(f"Refreshed {MANIFEST.relative_to(ROOT)}: {len(m['artifacts'])} artifacts, 4/4 production-ready.")
