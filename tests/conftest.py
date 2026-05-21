from __future__ import annotations

from pathlib import Path



def load_fixture(module: str, name: str) -> str:
    path = Path(__file__).parent / module / "fixtures" / name
    return path.read_text(encoding="utf-8")
