#!/usr/bin/env python3
"""Sign nested Mach-O code before signing the containing bundle."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--app',type=Path,required=True);p.add_argument('--identity',required=True);a=p.parse_args()
app=a.app.resolve();magic={b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xfe\xed\xfa\xce',b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca'}
files=[]
for file in app.rglob('*'):
 if file.is_file() and not file.is_symlink():
  with file.open('rb') as f:
   if f.read(4) in magic:files.append(file)
for index,file in enumerate(sorted(files,key=lambda p:len(p.parts),reverse=True),1):
 args=['codesign','--force','--options','runtime','--timestamp','--sign',a.identity]
 # Numba/LLVM used by the model's audio frontend allocates executable memory.
 if file.name.startswith('python3'):
  args += ['--entitlements',str(Path(__file__).resolve().parents[1]/'src-tauri/python.entitlements.plist')]
 subprocess.run(args+[str(file)],check=True,stdout=subprocess.DEVNULL)
 if index%50==0:print(f'Signed {index}/{len(files)} code files',flush=True)
subprocess.run(['codesign','--force','--options','runtime','--timestamp','--sign',a.identity,str(app)],check=True)
subprocess.run(['codesign','--verify','--deep','--strict','--verbose=2',str(app)],check=True)
print(f'Signed {len(files)} nested code files and {app.name}.')
