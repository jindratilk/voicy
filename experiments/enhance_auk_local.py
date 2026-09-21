"""Experimental local AuK file runner with automatic context-overlap joins.

Run using the isolated MLX Python and PYTHONPATH=work/AuK/src. Models must
already be downloaded and converted; this command never downloads them.
"""
import argparse,json,os,resource,sys,threading,time
from dataclasses import asdict
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from math import gcd
sys.path.insert(0,str(Path(__file__).absolute().parents[1]))
from server.chunking import plan_chunks,assemble_chunks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--models',type=Path,default=Path('work/auk-lab'))
    p.add_argument('--nfe',type=int,default=32)
    p.add_argument('--memory-mode', choices=['auto','sequential','resident'], default='auto', help='Resident override is for controlled benchmarks; the app uses auto.')
    a=p.parse_args()
    if not 1<=a.nfe<=128:p.error('nfe must be between 1 and 128')
    if a.output.exists():p.error('Output directory already exists; preserving it')
    x,sr=sf.read(a.input,dtype='float32',always_2d=True)
    x=x.mean(axis=1)
    if not len(x) or not np.isfinite(x).all():p.error('Input must be nonempty finite audio')
    g=gcd(sr,24000);x=resample_poly(x,24000//g,sr//g).astype(np.float32)
    plan=plan_chunks(len(x),24000)
    import mlx.core as mx
    from auk_mlx.infer import AukMLX,GenerateOptions
    from server.memory_policy import read_snapshot,choose_plan,should_release_resident
    from server.auk_runtime import install_embedding_reuse
    snapshot=read_snapshot()
    weights_bytes=sum((a.models/name).stat().st_size for name in [
        'mlx/vae.safetensors','mlx/dit_base.q8.safetensors','mlx/thinker/thinker.q8.safetensors'])
    memory_plan=choose_plan(snapshot,weights_bytes)
    resident=memory_plan.resident if a.memory_mode=='auto' else a.memory_mode=='resident'
    if resident and not memory_plan.resident:
        p.error('Resident mode requires normal pressure and sufficient free memory; use auto or sequential.')
    mx.set_memory_limit(memory_plan.metal_limit);mx.set_cache_limit(memory_plan.cache_limit)
    print('Memory policy:',json.dumps({'snapshot':asdict(snapshot),'plan':asdict(memory_plan),'resident':resident}),flush=True)
    install_embedding_reuse()
    def watch():
        while True:
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>memory_plan.rss_limit:
                os.write(2,b'AuK stopped: memory safety budget exceeded\n');os._exit(75)
            time.sleep(.5)
    threading.Thread(target=watch,daemon=True).start()
    engine=AukMLX(str(a.models/'mlx'),str(a.models/'original/config.yaml'),str(a.models/'qwen'),bits=8,group_size=64,sequential=not resident)
    a.output.mkdir(parents=True)
    prompt='Preserve all speakers, remove noise and reverberation, and output clean speech of the same length.'
    config={'input':str(a.input.absolute()),'input_sample_rate':sr,'output_sample_rate':24000,'plan':[c.__dict__ for c in plan],'nfe':a.nfe,'seed':2026,'instruction':prompt,'bits':8,'group_size':64,'cfg_strength':2.,'memory_policy':asdict(memory_plan),'initial_resident':resident}
    (a.output/'config.json').write_text(json.dumps(config,indent=2))
    chunks=[];timings=[];memory_downgrades=0
    for index,c in enumerate(plan):
        if not engine.sequential:
            current=read_snapshot()
            if should_release_resident(current):
                # Switch only between complete chunks; weights/seed/arithmetic stay unchanged.
                engine.vae=engine.dit=engine.thinker=None
                engine._release()
                engine.sequential=True
                mx.set_cache_limit(256*1024**2)
                memory_downgrades+=1
                print('Memory pressure: switching to sequential execution.',flush=True)
        chunk=np.pad(x[c.start:c.start+c.valid_frames],(0,c.frames-c.valid_frames))
        path=a.output/f'input-{index:04}.wav';sf.write(path,chunk,24000,subtype='FLOAT')
        print(f'Starting chunk {index+1}/{len(plan)}',flush=True)
        t=time.perf_counter()
        y,ysr=engine.generate(prompt,audio_path=str(path),opts=GenerateOptions(gen_seconds=c.frames/24000,nfe=a.nfe,cfg_strength=2.,sway_sampling_coef=-1.,seed=2026))
        if ysr!=24000 or len(y)!=c.frames or not np.isfinite(y).all():raise ValueError('Invalid model output')
        sf.write(a.output/f'chunk-{index:04}.wav',y,ysr,subtype='FLOAT');chunks.append(y);timings.append(time.perf_counter()-t)
        print(f'Completed chunk {index+1}/{len(plan)} in {timings[-1]:.2f}s',flush=True)
    y,joins=assemble_chunks(x,chunks,plan,24000)
    sf.write(a.output/'output.wav',y,24000,subtype='FLOAT')
    report={'frames':len(y),'sample_rate':24000,'duration':len(y)/24000,'joins':joins,'chunk_seconds_elapsed':timings,'memory_policy':asdict(memory_plan),'memory_downgrades':memory_downgrades,'metal_peak_bytes':mx.get_peak_memory(),'resident_high_water_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limitations':'Automatic low-energy joins are not guaranteed speech pauses. Timing drift and voice identity require validation. All chunks are retained in memory; this experimental runner is not yet suitable for unbounded recordings.'}
    (a.output/'result.json').write_text(json.dumps(report,indent=2));print(report,flush=True)

if __name__=='__main__':main()
