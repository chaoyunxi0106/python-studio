from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from python_studio.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
