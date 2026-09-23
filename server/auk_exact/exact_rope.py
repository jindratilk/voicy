"""Research rotary fusion preserving separate FP32 multiply/add rounding."""
import mlx.core as mx
from auk_mlx.dit import _RopeTable
original=_RopeTable.apply
kernel=mx.fast.metal_kernel(name='voicy_exact_rope',input_names=['x','cosine','sine'],output_names=['out'],
    compile_options={'math_mode':'safe'},source='''
    #pragma clang fp contract(off)
    uint i=thread_position_in_grid.x;
    if(i>=S)return;
    uint table=i%(N*D);
    float rotated=(i%2==0)?-x[i+1]:x[i-1];
    float a=x[i]*cosine[table];
    float b=rotated*sine[table];
    out[i]=a+b;
    ''')
def apply(self,x):
    if x.dtype!=mx.float32 or x.ndim!=4 or x.shape[-1]%2:return original(self,x)
    n=x.shape[-2];self._grow(n)
    return kernel(inputs=[x,self._cos[:n],self._sin[:n]],
        template=[('S',x.size),('N',n),('D',x.shape[-1])],grid=(x.size,1,1),threadgroup=(256,1,1),
        output_shapes=[x.shape],output_dtypes=[mx.float32])[0]
def install():_RopeTable.apply=apply

