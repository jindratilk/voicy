"""Exact-order AuK execution optimizations for the pinned MLX runtime."""
_installed = False

def install():
    global _installed
    if _installed:
        return
    from . import fast_upsample, fast_snake, fused_upsnake, exact_dit_bundle
    fast_upsample.install()
    fast_snake.install()
    fused_upsnake.install()
    exact_dit_bundle.install()
    _installed = True
