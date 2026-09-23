"""Real GPU operation regression: compare native float bits, not rounded PCM."""
import unittest
import numpy as np
try:
    import mlx.core as mx
    from auk_mlx.layers import UpSample1d, DownSample1d, SnakeBeta, Activation1d
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


@unittest.skipUnless(HAS_MLX, 'Requires the pinned Apple Silicon runtime')
class ExactOperationsTests(unittest.TestCase):
    def test_operations_and_idempotent_install(self):
        from server.auk_exact import install
        mx.random.seed(104)
        layers = [UpSample1d(), DownSample1d(), SnakeBeta(24), Activation1d(24)]
        inputs = [mx.random.normal((1, 600, 24)) for _ in layers]
        expected = []
        for layer, x in zip(layers, inputs):
            y = layer(x)
            mx.eval(y)
            expected.append(np.array(y).view(np.uint32).copy())
        install()
        method = UpSample1d.__call__
        install()
        self.assertIs(method, UpSample1d.__call__)
        for layer, x, reference in zip(layers, inputs, expected):
            y = layer(x)
            mx.eval(y)
            np.testing.assert_array_equal(reference, np.array(y).view(np.uint32))


if __name__ == '__main__':
    unittest.main()
