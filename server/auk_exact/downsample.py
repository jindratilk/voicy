"""Exact-order direct depthwise downsampling, isolated numerical/timing probe."""
import mlx.core as mx
from auk_mlx.layers import DownSample1d

kernel=mx.fast.metal_kernel(name='voicy_direct_downsample',input_names=['inp','filter'],output_names=['out'],source='''
    uint index=thread_position_in_grid.x;
    if(index>=B*O*C)return;
    int channel=index%C;
    int position=(index/C)%O;
    int batch=index/(C*O);
    float acc=0.0f;
    for(int k=0;k<12;k++){
        float value=inp[(batch*L+position*2+k)*C+channel];
        acc=fma(value,filter[k],acc);
    }
    out[index]=acc;
''')
def direct(x,filter):
    b,l,c=x.shape;o=(l-12)//2+1
    return kernel(inputs=[x,filter],template=[('B',b),('L',l),('C',c),('O',o)],
                  grid=(b*o*c,1,1),threadgroup=(256,1,1),
                  output_shapes=[(b,o,c)],output_dtypes=[mx.float32])[0]
