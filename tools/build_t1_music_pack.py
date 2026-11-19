#!/usr/bin/env python3
"""Build the deterministic T1 music successor package without mutating its silent base."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/T1_special_menu_music_pack_v1_0_0.json'
PKG=ROOT/'packages/t1-special-menu-music-v1/manifest.json'
OUT=ROOT/'packages/t1-special-menu-music-v1/t1-special-menu-afrobeat-amapiano-music-v1.zip'
FIXED_DT=(2026,11,18,0,0,0)
def sha(path:Path)->str:
 return hashlib.sha256(path.read_bytes()).hexdigest()
def main()->None:
 subprocess.run([sys.executable,str(ROOT/'tools/validate_t1_music_pack.py')],cwd=ROOT,check=True)
 manifest=json.loads(PKG.read_text())
 files=[
  PKG,ROOT/'schemas/T1_music_pack.schema.json',ROOT/'schemas/T1_music_selection_state.schema.json',ROOT/'adapter/t1_adapter.py',
  ROOT/'tools/build_t1_music_pack.py',ROOT/'tools/validate_t1_music_pack.py',ROOT/'tools/refresh_t1_music_manifest.py',ROOT/'tools/record_t1_music_result.py',
  ROOT/'docs/T1_MUSIC_INTEGRATION.md',
 ]
 files += [ROOT/artifact['path'] for artifact in manifest['artifacts']]
 with tempfile.TemporaryDirectory() as temp:
  stage=Path(temp)/'t1-special-menu-afrobeat-amapiano-music-v1'; stage.mkdir()
  for source in files:
   target=stage/source.relative_to(ROOT); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
  build={'package_id':manifest['package_id'],'base_silent_commit':'cab2aa2a4a841341c9e84aeb08e243ea9baec0f4','music_config_sha256':sha(CFG),'files':[]}
  for path in sorted(stage.rglob('*')):
   if path.is_file(): build['files'].append({'path':str(path.relative_to(stage)),'bytes':path.stat().st_size,'sha256':sha(path)})
  (stage/'BUILD-MANIFEST.json').write_text(json.dumps(build,ensure_ascii=False,indent=2)+'\n')
  OUT.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
   for path in sorted(stage.rglob('*')):
    if path.is_file():
     arc=str(path.relative_to(stage.parent)); info=zipfile.ZipInfo(arc,FIXED_DT); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644 << 16
     archive.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 print(f'Built {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes, sha256 {sha(OUT)})')
if __name__=='__main__': main()
