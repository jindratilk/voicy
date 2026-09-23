"""Exact-order DiT fusion preserving multiply/add rounding separately."""
import mlx.core as mx
from auk_mlx.dit import AdaLayerNorm,AdaLayerNormFinal,DiTBlock,MMDiTBlock,_layer_norm
from auk_mlx.layers import silu
from .pointwise import affine_kernel,gate_kernel,fused

def affine(x,scale,shift):
    if x.dtype==mx.float32 and x.ndim==3:
        return fused(affine_kernel,x,scale,shift)
    return x*(1+scale[:,None])+shift[:,None]

def gate(x,scale,value):
    if x.dtype==mx.float32 and x.ndim==3:
        return fused(gate_kernel,x,scale,value)
    return x+scale[:,None]*value

def ada(self,x,emb):
    e=self.linear(silu(emb))
    shift,scale,g,ffshift,ffscale,ffg=mx.split(e,6,axis=1)
    return affine(_layer_norm(x),scale,shift),g,ffshift,ffscale,ffg

def final(self,x,emb):
    scale,shift=mx.split(self.linear(silu(emb)),2,axis=1)
    return affine(_layer_norm(x),scale,shift)

def single(self,x,t,rope,mask=None):
    norm,g,shift,scale,ffg=self.attn_norm(x,t)
    x=gate(x,g,self.attn.single(norm,rope,mask))
    norm=affine(_layer_norm(x),scale,shift)
    return gate(x,ffg,self.ff(norm))

def double(self,x,c,t,rope,mask=None):
    cn,cg,cs,cc,cf=self.attn_norm_c(c,t)
    xn,xg,xs,xc,xf=self.attn_norm_x(x,t)
    xa,ca=self.attn.joint(xn,cn,rope,mask)
    c=gate(c,cg,ca)
    c=gate(c,cf,self.ff_c(affine(_layer_norm(c),cc,cs)))
    x=gate(x,xg,xa)
    x=gate(x,xf,self.ff_x(affine(_layer_norm(x),xc,xs)))
    return c,x

ORIGINALS={cls:cls.__call__ for cls in [AdaLayerNorm,AdaLayerNormFinal,DiTBlock,MMDiTBlock]}
def install():
    for cls,method in [(AdaLayerNorm,ada),(AdaLayerNormFinal,final),(DiTBlock,single),(MMDiTBlock,double)]:
        cls.__call__=method
def restore():
    for cls,method in ORIGINALS.items():cls.__call__=method
