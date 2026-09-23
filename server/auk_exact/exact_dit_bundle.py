"""Combine prior exact pointwise/tail pruning with scoped text reuse and RoPE."""
from auk_mlx.infer import AukMLX
from .final_block import PrunedFinal
from .exact_pointwise import install as pointwise
from .exact_rope import install as rope

def install():
    pointwise();rope()
    original=AukMLX.sample
    def sample(self,text,ref,gen_len,opts):
        last=self.dit.single_transformer_blocks[-1]
        last.__class__=PrunedFinal
        last.cut=text.shape[1]+ref.shape[1]
        project=self.dit.project_text
        had_override='project_text' in self.dit.__dict__
        prior_override=self.dit.__dict__.get('project_text')
        cache={}
        def memo(value,drop_text=False):
            if value is not text:return project(value,drop_text=drop_text)
            if drop_text not in cache:
                cache[drop_text]=project(value,drop_text=drop_text)
            return cache[drop_text]
        self.dit.project_text=memo
        try:return original(self,text,ref,gen_len,opts)
        finally:
            if had_override:self.dit.project_text=prior_override
            else:delattr(self.dit,'project_text')
            cache.clear()
    AukMLX.sample=sample
