"""Reproduce the host-dependent MLX wheel selection that broke clean macOS 15."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('runtime_mlx', Path(__file__).parents[1] / 'scripts/pin-runtime-mlx.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def metadata(site, name, tag):
    path = site / (name + '-0.32.2.dist-info')
    path.mkdir()
    (path / 'WHEEL').write_text('Wheel-Version: 1.0\nTag: ' + tag + '\n')


def test_rejects_actual_mac26_wheel_pair_from_failed_installer(tmp_path):
    metadata(tmp_path, 'mlx', 'cp313-cp313-macosx_26_0_arm64')
    metadata(tmp_path, 'mlx_metal', 'py3-none-macosx_26_0_arm64')
    with pytest.raises(RuntimeError, match='deployment platform'):
        runtime.audit(tmp_path)


def test_accepts_baseline_pair_but_rejects_other_incompatible_wheels(tmp_path):
    metadata(tmp_path, 'mlx', 'cp313-cp313-macosx_14_0_arm64')
    metadata(tmp_path, 'mlx_metal', 'py3-none-macosx_14_0_arm64')
    runtime.audit(tmp_path)
    metadata(tmp_path, 'another_dependency', 'cp313-cp313-macosx_15_0_arm64')
    with pytest.raises(RuntimeError, match='another_dependency'):
        runtime.audit(tmp_path)
