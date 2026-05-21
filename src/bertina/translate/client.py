from __future__ import annotations

import logging
from typing import Any

from .._base import AsyncBaseClient, BaseClient
from ..constants import TRANSLATE_BASE
from ..exceptions import BertinaHTTPError, BertinaParseError
from .languages import Language
from .models import TranslationResult

logger = logging.getLogger("bertina.translate")

_TRANSLATE_URL = f"{TRANSLATE_BASE}/api/translate"


def _parse_ndjson(
    body: str,
    source_text: str,
    source_lang: Language,
    target_lang: Language,
) -> TranslationResult:
    """Parse the NDJSON stream returned by the translate API.

    Each line is a JSON object: {"response": "...", "done": false}
    The final line has "done": true and optionally "detectedLang".
    """
    import json as _json

    parts: list[str] = []
    detected_raw: str | None = None

    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        chunk = obj.get("response", "")
        if chunk:
            parts.append(chunk)
        if obj.get("done"):
            detected_raw = obj.get("detectedLang")

    translated = "".join(parts)
    if not translated:
        raise BertinaParseError(f"empty translation in response: {body!r}")

    detected: Language | None = None
    if detected_raw:
        try:
            detected = Language(detected_raw)
        except ValueError:
            logger.debug("unknown detectedLang %r", detected_raw)

    return TranslationResult(
        source_text=source_text,
        translated_text=translated,
        source_lang=source_lang,
        target_lang=target_lang,
        detected_lang=detected,
    )


class BertinaTranslate(BaseClient):
    """Synchronous Bertina translation client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 86400, **kwargs)

    def translate(
        self,
        text: str,
        *,
        target: Language,
        source: Language = Language.AUTO,
    ) -> TranslationResult:
        payload = {"text": text, "source": source.value, "target": target.value}
        logger.debug("translate source=%s target=%s text=%r", source, target, text[:40])
        response = self._client.post(
            _TRANSLATE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 429:
            from ..exceptions import BertinaRateLimitError

            raise BertinaRateLimitError()
        if response.status_code >= 400:
            raise BertinaHTTPError(
                f"HTTP {response.status_code} for {_TRANSLATE_URL}",
                status_code=response.status_code,
            )
        return _parse_ndjson(response.text, text, source, target)


class AsyncBertinaTranslate(AsyncBaseClient):
    """Asynchronous Bertina translation client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 86400, **kwargs)

    async def translate(
        self,
        text: str,
        *,
        target: Language,
        source: Language = Language.AUTO,
    ) -> TranslationResult:
        payload = {"text": text, "source": source.value, "target": target.value}
        logger.debug("translate source=%s target=%s text=%r", source, target, text[:40])
        async with self._semaphore:
            response = await self._client.post(
                _TRANSLATE_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if response.status_code == 429:
            from ..exceptions import BertinaRateLimitError

            raise BertinaRateLimitError()
        if response.status_code >= 400:
            raise BertinaHTTPError(
                f"HTTP {response.status_code} for {_TRANSLATE_URL}",
                status_code=response.status_code,
            )
        return _parse_ndjson(response.text, text, source, target)
