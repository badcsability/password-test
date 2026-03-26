import os
import shutil
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def cli_workdir(tmp_path: Path) -> Path:
    """
    Create an isolated working directory containing a copy of the CLI
    so tests can safely create a local `.env` and password-store JSON file.
    """
    for name in ("pw_manager.py", "pw_class.py", "key_manager.py"):
        shutil.copy2(REPO_ROOT / name, tmp_path / name)

    store_path = tmp_path / "pwstore.json"
    (tmp_path / ".env").write_text(f"PWD_FILE={store_path}\n", encoding="utf-8")
    return tmp_path

