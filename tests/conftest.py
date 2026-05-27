from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest


def load_fixture(module: str, name: str) -> str:
    path = Path(__file__).parent / module / "fixtures" / name
    return path.read_text(encoding="utf-8")


async def _noop_sleep(_: float) -> None:
    return


@pytest.fixture(autouse=True)
def no_sleep():
    with patch("bertina._base.time.sleep"), \
         patch("bertina._base.asyncio.sleep", side_effect=_noop_sleep):
        yield
