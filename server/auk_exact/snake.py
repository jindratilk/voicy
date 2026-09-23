"""Test exact-order fusion of the decoder's nonlinear activation."""
import mlx.core as mx

def make_kernel(mode='safe'):
    return mx.fast.metal_kernel(name='voicy_snake_'+mode,input_names=['x','alpha','invbeta'],output_names=['out'],
        compile_options={'math_mode':mode},source='''
        #pragma clang fp contract(off)
        uint i=thread_position_in_grid.x;
        if(i>=S)return;
        uint c=i%C;
        float s=metal::sin(x[i]*alpha[c]);
        float p=invbeta[c]*s;
        float q=p*s;
        out[i]=x[i]+q;
        ''')
def run_kernel(kernel,x,alpha,invbeta):
    return kernel(inputs=[x,alpha,invbeta],template=[('S',x.size),('C',x.shape[-1])],
                  grid=(x.size,1,1),threadgroup=(256,1,1),
                  output_shapes=[x.shape],output_dtypes=[x.dtype])[0]
