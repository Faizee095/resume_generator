import os
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
VENV_PYTHON = (
    PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
    if os.name == "nt"
    else PROJECT_DIR / ".venv" / "bin" / "python"
)


def main():
    if not VENV_PYTHON.exists():
        print(
            "The project .venv is required for the commit hook. "
            "Install requirements-dev.txt into .venv first.",
            file=sys.stderr,
        )
        return 1
    return subprocess.call(
        [str(VENV_PYTHON), "-m", "pytest", "-m", "not browser"],
        cwd=PROJECT_DIR,
    )


if __name__ == "__main__":
    raise SystemExit(main())
