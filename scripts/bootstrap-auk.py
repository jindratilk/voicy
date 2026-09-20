#!/usr/bin/env python3
"""Reproduce the pinned AuK runtime on Apple Silicon; no private workspace required."""
import hashlib,json,os,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='6943a1e967409e8c73139a7a345f2a611cfb3dd6'
MODEL='790742b71a4430120daf2b2099192abae449eb9f'
QWEN='f75b40e3da2003cdd6e1829b1f420ca70797c34e'
def run(*args,**kwargs):subprocess.run([str(x) for x in args],check=True,**kwargs)
def main():
 if platform.system()!='Darwin' or platform.machine()!='arm64':raise SystemExit('Apple Silicon macOS required.')
 uv=shutil.which('uv')
 if not uv:raise SystemExit('Install uv from https://docs.astral.sh/uv/ first.')
 install=ROOT/'.auk';install.mkdir(exist_ok=True)
 if not (install/'venv/bin/python').exists():run(uv,'venv','--python','3.13.14',install/'venv')
 python=install/'venv/bin/python'
 run(uv,'pip','sync','--python',python,ROOT/'experiments/auk-mlx-requirements.freeze.txt')
 repo=ROOT/'build/auk-source'
 if not (repo/'.git').exists():
  repo.mkdir(parents=True,exist_ok=True);run('git','init',repo);run('git','-C',repo,'remote','add','origin','https://github.com/Tencent-Hunyuan/AuK.git')
 run('git','-C',repo,'fetch','--depth','1','origin',SOURCE);run('git','-C',repo,'checkout','--detach',SOURCE)
 shutil.copytree(repo/'src',install/'source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copy2(repo/'LICENSE',install/'SOURCE-LICENSE');shutil.copy2(ROOT/'experiments/auk-mlx-requirements.freeze.txt',install/'requirements.lock')
 env={**os.environ,'PYTHONPATH':str(install/'source')}
 original=ROOT/'build/checkpoints/auk';qwen=ROOT/'build/checkpoints/qwen'
 download="from huggingface_hub import snapshot_download; import sys,json; snapshot_download(repo_id=sys.argv[1],revision=sys.argv[2],local_dir=sys.argv[3],allow_patterns=json.loads(sys.argv[4]))"
 run(python,'-c',download,'tencent/AuK',MODEL,original,json.dumps(['config.yaml','LICENSE','vae.safetensors','auk_base.safetensors']))
 run(python,'-c',download,'Qwen/Qwen2.5-Omni-3B',QWEN,qwen,json.dumps(['*.json','*.txt','LICENSE','model-00001-of-00003.safetensors','model-00002-of-00003.safetensors']))
 models=install/'models';(models/'mlx').mkdir(parents=True,exist_ok=True)
 run(python,'-m','auk_mlx.convert','vae',original/'vae.safetensors',models/'mlx/vae.safetensors',env=env)
 run(python,ROOT/'experiments/convert_auk_streaming.py','dit',original/'auk_base.safetensors',models/'mlx',env=env)
 run(python,ROOT/'experiments/convert_auk_streaming.py','thinker',qwen,models/'mlx/thinker',env=env)
 for source,dest in [(original,models/'original'),(qwen,models/'qwen')]:
  dest.mkdir(exist_ok=True)
  for p in source.iterdir():
   if p.is_file() and (p.suffix in ('.json','.txt','.yaml') or p.name=='LICENSE'):shutil.copy2(p,dest/p.name)
 expected=json.loads((ROOT/'scripts/model-manifest.json').read_text())
 for name,digest in expected.items():
  path=install/name
  with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  if actual!=digest:raise SystemExit(f'Model verification failed: {name}')
 (install/'READY.json').write_text(json.dumps({'source_revision':SOURCE,'model_revision':MODEL,'files_sha256':expected},indent=2))
 print('Pinned model installation verified.')
if __name__=='__main__':main()
