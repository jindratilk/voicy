"""Exact-order exact-order SnakeBeta fusion with safe Metal math."""
import mlx.core as mx
from auk_mlx.layers import SnakeBeta
from .snake import make_kernel,run_kernel
original=SnakeBeta.__call__
kernel=make_kernel('safe')
def fast(self,x):
    if x.dtype!=mx.float32:return original(self,x)
    alpha=mx.exp(self.alpha) if self.alpha_logscale else self.alpha
    beta=mx.exp(self.beta) if self.alpha_logscale else self.beta
    inverse=1./(beta+1e-9)
    return run_kernel(kernel,x,alpha,inverse)
def install():SnakeBeta.__call__=fast
def restore():SnakeBeta.__call__=original
