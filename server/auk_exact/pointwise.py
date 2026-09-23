"""Fuse bandwidth-bound DiT pointwise operations with FP contraction disabled.

Verified against complete native-float outputs; retain operation order.
"""
import mlx.core as mx

affine_kernel=mx.fast.metal_kernel(name='voicy_exact_affine',input_names=['x','scale','shift'],output_names=['out'],source='''
    #pragma clang fp contract(off)
    uint i=thread_position_in_grid.x;
    if(i>=B*N*D)return;
    uint channel=i%D;
    uint batch=i/(N*D);
    float factor=1.0f+scale[batch*D+channel];
    float product=x[i]*factor;
    out[i]=product+shift[batch*D+channel];
''')
gate_kernel=mx.fast.metal_kernel(name='voicy_exact_gate',input_names=['x','gate','value'],output_names=['out'],source='''
    #pragma clang fp contract(off)
    uint i=thread_position_in_grid.x;
    if(i>=B*N*D)return;
    uint channel=i%D;
    uint batch=i/(N*D);
    float product=gate[batch*D+channel]*value[i];
    out[i]=x[i]+product;
''')
def fused(kernel,x,*args):
    b,n,d=x.shape
    return kernel(inputs=[x,*args],template=[('B',b),('N',n),('D',d)],
                  grid=(x.size,1,1),threadgroup=(256,1,1),
                  output_shapes=[x.shape],output_dtypes=[x.dtype])[0]
