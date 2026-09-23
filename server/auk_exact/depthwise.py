"""Exact-order sparse stride-2 depthwise transposed convolution."""
import mlx.core as mx
from auk_mlx.layers import UpSample1d

def make_kernel(reverse=True,fused=True):
    order='11-j' if reverse else 'j'
    operation='acc = fma(value, filter[k], acc);' if fused else 'acc = acc + value * filter[k];'
    source=f'''
    uint index=thread_position_in_grid.x;
    if(index >= B*O*C) return;
    int channel=index % C;
    int position=(index / C) % O;
    int batch=index / (C*O);
    float acc=0.0f;
    for(int j=0;j<12;j++) {{
        int k={order};
        int v=position-k;
        if(v>=0 && v%2==0 && v/2<L) {{
            float value=inp[(batch*L+v/2)*C+channel];
            {operation}
        }}
    }}
    out[index]=acc;
    '''
    return mx.fast.metal_kernel(name=f'voicy_dw_{int(reverse)}_{int(fused)}',
        input_names=['inp','filter'],output_names=['out'],source=source)

def direct(x,filter,kernel):
    b,l,c=x.shape;o=(l-1)*2+12
    return kernel(inputs=[x,filter],template=[('B',b),('C',c),('L',l),('O',o)],
        grid=(b*o*c,1,1),threadgroup=(256,1,1),
        output_shapes=[(b,o,c)],output_dtypes=[mx.float32])[0]
