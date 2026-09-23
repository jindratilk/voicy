"""Bounded stage reuse without tensor batching or changed random-number order."""
import time
import numpy as np
import soundfile as sf
import mlx.core as mx
from auk_mlx.infer import GenerateOptions
from server.memory_policy import read_snapshot, can_retain_vae, grouped_window_size


def generate_chunks(engine, source, plan, output, prompt, nfe):
    """Release large stages between phases; keep at most two chunks on the GPU."""
    generated, timings = [], []

    def trim_vae():
        if not can_retain_vae(read_snapshot(), mx.get_active_memory()):
            engine.vae = None
            engine._release()

    index = 0
    while index < len(plan):
        window = plan[index:index + grouped_window_size(read_snapshot())]
        inputs = []
        started = time.perf_counter()
        print(f'Starting chunk {index+1}/{len(plan)}', flush=True)
        for offset, chunk in enumerate(window):
            wave = np.pad(source[chunk.start:chunk.start+chunk.valid_frames],
                          (0, chunk.frames-chunk.valid_frames))
            path = output/f'input-{index+offset:04}.wav'
            sf.write(path, wave, 24000, subtype='FLOAT')
            inputs.append((wave, path))
        if engine.vae is None:
            engine.vae = engine._build_vae()
        refs = []
        for wave, _ in inputs:
            ref = engine.encode_audio(wave)
            mx.eval(ref)
            refs.append(ref)
        trim_vae()
        engine.thinker = engine._build_thinker()
        conditioning = []
        for _, path in inputs:
            text = engine.encode_text([{'role': 'user', 'content': [
                {'type': 'text', 'text': prompt}, {'type': 'audio', 'audio': str(path)}]}])
            mx.eval(text)
            conditioning.append(text)
        engine.thinker = None
        engine._release()
        engine.dit = engine._build_dit()
        latents = []
        for chunk, text, ref in zip(window, conditioning, refs):
            opts = GenerateOptions(gen_seconds=chunk.frames/24000, nfe=nfe,
                                   cfg_strength=2., sway_sampling_coef=-1., seed=2026)
            latent = engine.sample(text, ref, chunk.frames//engine.downsample_rate, opts)
            mx.eval(latent)
            if not bool(mx.all(mx.isfinite(latent))):
                raise ValueError('Invalid model latent')
            latents.append(latent)
        engine.dit = None
        conditioning.clear()
        refs.clear()
        engine._release()
        if engine.vae is None:
            engine.vae = engine._build_vae()
        for offset, (chunk, latent) in enumerate(zip(window, latents)):
            wave = engine.vae.decode(latent)
            mx.eval(wave)
            wave = np.array(wave).reshape(-1)
            if len(wave) != chunk.frames or not np.isfinite(wave).all():
                raise ValueError('Invalid model output')
            sf.write(output/f'chunk-{index+offset:04}.wav', wave, 24000, subtype='FLOAT')
            generated.append(wave)
            print(f'Completed chunk {index+offset+1}/{len(plan)}', flush=True)
        timings.extend([(time.perf_counter()-started)/len(window)]*len(window))
        latents.clear()
        trim_vae()
        index += len(window)
    return generated, timings
