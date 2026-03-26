import os
import subprocess
import sys
from pathlib import Path


def run_cli(
    workdir: Path,
    *args: str,
    input_text: str | None = None,
    timeout_s: float = 10,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workdir)

    return subprocess.run(
        [sys.executable, str(workdir / "pw_manager.py"), *args],
        cwd=str(workdir),
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )

