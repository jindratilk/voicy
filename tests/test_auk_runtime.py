"""Small real-MLX equality tests; skipped on non-Apple CI hosts."""
import unittest
import numpy as np

try:
    import mlx.core as mx
    from auk_mlx import infer
    from auk_mlx.dit import Flux2Edit, DiTConfig
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


@unittest.skipUnless(HAS_MLX, 'Requires the pinned Apple Silicon AuK environment')
class EmbeddingReuseTests(unittest.TestCase):
    def setUp(self):
        from server.auk_runtime import install_embedding_reuse
        self.original_class = infer.Flux2Edit
        install_embedding_reuse()
        cfg = DiTConfig(dim=64, heads=4, dim_head=16, text_hidden_dim=32,
            latent_dim=8, num_layers=1, num_single_layers=1)
        mx.random.seed(42)
        self.reference = Flux2Edit(cfg)
        self.optimized = infer.Flux2Edit(cfg)
        self.optimized.update(self.reference.parameters())
        self.reference.clear_cache()
        self.optimized.clear_cache()
        self.text = mx.random.normal((1, 3, 32))
        self.ref = mx.random.normal((1, 8, 8))

    def tearDown(self):
        infer.Flux2Edit = self.original_class
        mx.clear_cache()

    def compare(self, ref, cfg=True, cache=True):
        x = mx.random.normal((1, 8, 8));t = mx.array([.4])
        expected = self.reference(x,self.text,t,ref=ref,cfg_infer=cfg,cache=cache)
        actual = self.optimized(x,self.text,t,ref=ref,cfg_infer=cfg,cache=cache)
        mx.eval(expected,actual)
        np.testing.assert_array_equal(np.array(expected),np.array(actual))

    def test_repeated_steps_and_cache_reset(self):
        self.compare(self.ref)
        self.compare(self.ref)
        self.reference.clear_cache();self.optimized.clear_cache()
        self.compare(mx.random.normal((1,8,8)))
        self.assertIsNotNone(self.optimized._reference_pair)
        self.optimized.clear_cache()
        self.assertIsNone(self.optimized._reference_pair)

    def test_changed_reference_is_not_reused(self):
        self.compare(self.ref)
        self.compare(mx.random.normal((1,8,8)))

    def test_no_reference_and_cache_disabled(self):
        self.compare(None)
        self.compare(self.ref,cache=False)

    def test_guidance_switch_does_not_reuse_missing_branch(self):
        self.compare(self.ref,cfg=False)
        self.compare(self.ref,cfg=True)


if __name__ == '__main__':
    unittest.main()
