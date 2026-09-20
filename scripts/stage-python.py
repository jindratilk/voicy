#!/usr/bin/env python3
"""Stage relocatable python-build-standalone and pinned MLX packages."""
from pathlib import Path
import os,shutil,subprocess
root=Path(__file__).resolve().parents[1]
venv=root/'.auk/venv'
python=venv/'bin/python'
base=Path(subprocess.check_output([str(python),'-c','import sys;print(sys.base_prefix)'],text=True).strip())
target=root/'build/runtime/python'
if not target.exists():
 target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cp','-cR',str(base),str(target)],check=True)
 subprocess.run(['cp','-cR',str(venv/'lib/python3.13/site-packages')+'/.',str(target/'lib/python3.13/site-packages')+'/'],check=True)
subprocess.run(['uv','pip','install','--python',str(target/'bin/python3'),'--break-system-packages','fastapi==0.141.1','uvicorn==0.53.0','python-multipart==0.0.32'],check=True)
print(target)
