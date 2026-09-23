"""Fixed-instruction, 12-second audio-only processor.

Uses the existing Whisper feature extractor and fresh waveform features.
Only input-independent token IDs are reused; no recording features are cached.
This deliberately rejects unsupported instructions or durations.
"""
import json
from pathlib import Path
import mlx.core as mx
import numpy as np
import soundfile as sf
import soxr
from omegaconf import OmegaConf
from auk_mlx.infer import AukMLX
BASE=Path(__file__).resolve().parent
PROMPT='Preserve all speakers, remove noise and reverberation, and output clean speech of the same length.'
def load_extractor(qwen_dir):
    from transformers import WhisperFeatureExtractor
    return WhisperFeatureExtractor.from_pretrained(qwen_dir,local_files_only=True)

def initialize(self,mlx_dir,config_path,qwen_dir,bits=8,group_size=64,sequential=True):
    self.mlx_dir=mlx_dir;self.qwen_dir=qwen_dir;self.bits=bits;self.group_size=group_size;self.sequential=sequential
    cfg=OmegaConf.load(config_path)
    self.is_flash=cfg.model.get('name','')=='AuK-Flash';self.variant='flash' if self.is_flash else 'base'
    vae=cfg.model.vae
    self.sample_rate=int(vae.target_sample_rate);self.downsample_rate=int(vae.downsample_rate);self.latent_dim=int(vae.latent_dim)
    self._vae_kwargs=OmegaConf.to_container(vae.model_init_kwargs,resolve=True)
    fusion=mx.load(str(Path(mlx_dir)/f'fusion_{self.variant}.safetensors'))
    self.layer_weights=fusion['layer_weights'];self.layer_scale=fusion['layer_scale'];self._inv_freq=np.array(fusion['inv_freq'])
    self._arch=OmegaConf.to_container(cfg.model.arch,resolve=True);self._arch['latent_dim']=self.latent_dim
    self.audio_token_id=json.loads((Path(qwen_dir)/'config.json').read_text())['thinker_config']['audio_token_index']
    self.feature_extractor=load_extractor(qwen_dir)
    metadata=json.loads((BASE/'frontend/constants.json').read_text())
    if metadata['instruction']!=PROMPT:raise ValueError('Instruction constants mismatch')
    with np.load(BASE/'frontend/constants.npz') as constants:
        self._fixed_input_ids=constants['input_ids'].copy()
    if self._fixed_input_ids.shape!=(1,342) or np.count_nonzero(self._fixed_input_ids==self.audio_token_id)!=300:
        raise ValueError('Unexpected token layout for the pinned model')
    self.vae=self.dit=self.thinker=None
    if not sequential:
        self.vae=self._build_vae()
        self.dit=self._build_dit()
        self.thinker=self._build_thinker()

def features(self,messages):
    if len(messages)!=1 or messages[0]['role']!='user':raise ValueError('Unsupported message')
    content=messages[0]['content']
    if len(content)!=2 or content[0]!={'type':'text','text':PROMPT} or content[1]['type']!='audio':
        raise ValueError('Unsupported instruction; fixed-token reuse is not valid')
    audio,sr=sf.read(content[1]['audio'],dtype='float32',always_2d=True)
    audio=audio.mean(axis=1)
    if sr!=24000 or len(audio)!=288000:raise ValueError('Expected a padded 12-second, 24 kHz chunk')
    audio=soxr.resample(audio,24000,16000,quality='HQ')
    values=self.feature_extractor([audio],sampling_rate=16000,padding='max_length',return_attention_mask=True,return_tensors='np')
    return audio,{'input_ids':self._fixed_input_ids,'input_features':np.asarray(values['input_features']),
                  'feature_attention_mask':np.asarray(values['attention_mask'])}

def encode_text(self,messages):
    _,values=features(self,messages)
    ids=mx.array(values['input_ids'])
    mel=mx.array(values['input_features'].transpose(0,2,1).astype(np.float32))
    length=int(values['feature_attention_mask'].sum())
    audio_mask=mx.array(values['input_ids']==self.audio_token_id)
    hidden=self.thinker(ids,audio_features=mel,audio_token_mask=audio_mask,audio_feature_len=length)
    stacked=mx.stack([mx.fast.layer_norm(h,None,None,1e-5) for h in hidden[1:]],axis=0)
    w=mx.softmax(self.layer_weights,axis=0)
    return (stacked*w[:,None,None,None]).sum(axis=0)*self.layer_scale

def install():
    AukMLX.__init__=initialize
    AukMLX.encode_text=encode_text
