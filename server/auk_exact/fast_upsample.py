"""Exact-order exact-order stride-2, 12-tap depthwise upsampling kernel."""
import mlx.core as mx
from auk_mlx.layers import UpSample1d,DownSample1d
from .depthwise import make_kernel,direct
from .downsample import direct as direct_down

original=UpSample1d.__call__
kernel=make_kernel(reverse=False,fused=True)
def fast(self,x):
    if x.dtype!=mx.float32 or self.ratio!=2 or self.kernel_size!=12:
        return original(self,x)
    if self.pad:
        x=mx.pad(x,[(0,0),(self.pad,self.pad),(0,0)],mode='edge')
    y=self.ratio*direct(x,self._filter,kernel)
    if self.causal:
        return y[:,:-(self.kernel_size-self.stride),:]
    return y[:,self.pad_left:-self.pad_right,:]

def install():
    UpSample1d.__call__=fast
    DownSample1d.__call__=fast_down

original_down=DownSample1d.__call__
def fast_down(self,x):
    if x.dtype!=mx.float32 or self.ratio!=2 or self.kernel_size!=12 or x.size<10000:
        return original_down(self,x)
    x=mx.pad(x,[(0,0),(self.pad_left,self.pad_right),(0,0)],mode='edge')
    return direct_down(x,self._filter)
