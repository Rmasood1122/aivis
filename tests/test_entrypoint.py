import subprocess, sys


def test_module_entrypoint_prints_help():
    r = subprocess.run(
        [sys.executable, "-m", "aivis.cli", "--help"],
        capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 0
    assert "Usage" in r.stdout or "Usage" in r.stderr
