import subprocess
import sys
from pathlib import Path

def test_sympy_verifications():
    ev_dir = Path("중간고사대비/v1/.assets/evidence")
    for i in range(2, 6):
        script = ev_dir / f"Q{i}-sympy.py"
        assert script.is_file(), f"Missing {script}"
        res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=Path.cwd())
        assert res.returncode == 0, f"Q{i}-sympy.py failed with exit code {res.returncode}:\nSTDERR:\n{res.stderr}\nSTDOUT:\n{res.stdout}"
        assert "VERIFIED: PASS" in res.stdout, f"Q{i}-sympy.py did not output 'VERIFIED: PASS': {res.stdout}"
        result_file = ev_dir / f"Q{i}-result.txt"
        assert result_file.is_file(), f"Missing result file {result_file}"
        assert len(result_file.read_text(encoding="utf-8").strip()) > 0
