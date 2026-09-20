"""Convert pinned upstream AuK weights without a full FP32 intermediate.

Run in the isolated MLX environment with AuK/src on PYTHONPATH. Layouts follow
upstream auk_mlx.convert. Quantization uses MLX's own affine q8/group64 routine.
The upstream model loader must subsequently pass strict key/shape validation.
"""
import argparse,json,gc
from pathlib import Path
import numpy as np
import mlx.core as mx
from safetensors import safe_open
from safetensors.numpy import save_file


def put(out,name,t):
    t=t.detach().float().contiguous().numpy()
    if name.endswith('.weight') and t.ndim==2:
        if t.shape[-1]%64:raise ValueError(f'Cannot group-quantize {name}: {t.shape}')
        q,s,b=mx.quantize(mx.array(t),group_size=64,bits=8)
        mx.eval(q,s,b)
        out[name]=np.array(q);out[name[:-6]+'scales']=np.array(s);out[name[:-6]+'biases']=np.array(b)
        del q,s,b
        mx.clear_cache()
    else:out[name]=t.copy()


def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['dit','thinker']);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    a.destination.mkdir(parents=True,exist_ok=True);out={};fusion={};kept=0
    paths=[a.source] if a.kind=='dit' else sorted(a.source.glob('*.safetensors'))
    if not paths:raise ValueError('No source shards')
    for path in paths:
        with safe_open(str(path),framework='pt') as f:
            for k in f.keys():
                if a.kind=='dit':
                    if k.startswith('text_encoder.'):continue
                    t=f.get_tensor(k)
                    if k in ('layer_weights','layer_scale'):
                        fusion[k]=t.float().numpy();continue
                    name=k.removeprefix('transformer.')
                    if name=='rotary_embed.inv_freq':fusion['inv_freq']=t.float().numpy();continue
                    if '.conv1d.' in name and name.endswith('.weight'):t=t.permute(0,2,1)
                    name=name.replace('time_mlp.2.','time_mlp.1.').replace('conv_pos_embed.conv1d.2.','conv_pos_embed.conv1d.1.')
                else:
                    if not k.startswith('thinker.'):continue
                    name=k.removeprefix('thinker.')
                    # This embedding is declared but never read in the pinned HF forward path;
                    # the upstream MLX AudioTower intentionally has no such parameter.
                    if name.startswith('visual.') or name in ('lm_head.weight','audio_tower.audio_bos_eos_token.weight'):continue
                    name=name.removeprefix('model.');t=f.get_tensor(k)
                    if name.startswith('audio_tower.conv') and name.endswith('.weight'):t=t.permute(0,2,1)
                put(out,name,t);del t;kept+=1
                if kept%100==0:print(f'{kept} tensors converted',flush=True)
        gc.collect()
    dst=a.destination/('dit_base.q8.safetensors' if a.kind=='dit' else 'thinker.q8.safetensors')
    save_file(out,str(dst));print(f'Saved {dst}: {dst.stat().st_size/1e9:.3f} GB, {len(out)} tensors',flush=True)
    if a.kind=='dit':
        assert set(fusion)=={'layer_weights','layer_scale','inv_freq'}
        save_file(fusion,str(a.destination/'fusion_base.safetensors'))
    else:
        config=json.loads((a.source/'config.json').read_text())['thinker_config']
        keys={'text':('hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads','intermediate_size','vocab_size','rope_theta','rms_norm_eps','head_dim'),'audio':('d_model','encoder_layers','encoder_attention_heads','encoder_ffn_dim','output_dim','n_window','num_mel_bins','scale_embedding')}
        meta={kind:{k:config[kind+'_config'][k] for k in names if k in config[kind+'_config']} for kind,names in keys.items()}
        (a.destination/'thinker_config.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
