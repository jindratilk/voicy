"""The idle server must not load neural inference frameworks."""
import subprocess,sys,os

def test_api_import_does_not_load_torch_or_mlx(tmp_path):
    result=subprocess.run([sys.executable,'-c','import server.app,sys; assert "torch" not in sys.modules; assert "mlx.core" not in sys.modules'],env={**os.environ,'CLEARVOICE_DATA':str(tmp_path)},capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
