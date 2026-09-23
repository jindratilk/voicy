"""Exact-order fused alias-free upsampling and Snake, retaining FP32 order."""
import mlx.core as mx
from auk_mlx.layers import Activation1d

kernel=mx.fast.metal_kernel(name='voicy_upsnake_exact',
    input_names=['x','filter','alpha','invbeta'],output_names=['out'],
    compile_options={'math_mode':'safe'},source='''
    #pragma clang fp contract(off)
    uint i=thread_position_in_grid.x;
    if(i>=B*2*L*C)return;
    int c=i%C;
    int p=(i/C)%(2*L);
    int b=i/(2*L*C);
    float acc=0.0f;
    for(int k=0;k<12;k++){
        int v=p+15-k;
        if(v%2==0){
            int source=clamp(v/2-5,0,L-1);
            acc=fma(x[(b*L+source)*C+c],filter[k],acc);
        }
    }
    float value=2.0f*acc;
    float s=metal::sin(value*alpha[c]);
    float a=invbeta[c]*s;
    float q=a*s;
    out[i]=value+q;
    ''')
original=Activation1d.__call__
def forward(self,x):
    up=self.upsample
    if (x.ndim!=3 or x.dtype!=mx.float32 or up.causal or up.ratio!=2
            or up.kernel_size!=12 or up.pad!=5 or up.pad_left!=15 or up.pad_right!=15):
        return original(self,x)
    alpha,beta=self.act.alpha,self.act.beta
    if self.act.alpha_logscale:alpha,beta=mx.exp(alpha),mx.exp(beta)
    invbeta=1./(beta+1e-9)
    b,l,c=x.shape
    y=kernel(inputs=[x,up._filter,alpha,invbeta],template=[('B',b),('L',l),('C',c)],
             grid=(b*2*l*c,1,1),threadgroup=(256,1,1),
             output_shapes=[(b,2*l,c)],output_dtypes=[mx.float32])[0]
    return self.downsample(y)
def install():Activation1d.__call__=forward
