"""Eliminate discarded final-block token work without removing context keys."""
import mlx.core as mx
from auk_mlx.dit import DiTBlock, _layer_norm

class PrunedFinal(DiTBlock):
    def __call__(self,x,t,rope,mask=None):
        cut=self.cut
        norm,gate,shift,scale,ffgate=self.attn_norm(x,t)
        attention=self.attn.single(norm,rope,mask)[:,cut:]
        tail=x[:,cut:]+gate[:,None]*attention
        norm=_layer_norm(tail)*(1+scale[:,None])+shift[:,None]
        result=tail+ffgate[:,None]*self.ff(norm)
        return mx.concatenate([mx.zeros_like(x[:,:cut]),result],axis=1)
