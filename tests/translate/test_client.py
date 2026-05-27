from __future__ import annotations

import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from bertina.exceptions import BertinaHTTPError, BertinaParseError
from bertina.translate import (
    AsyncBertinaTranslate,
    BertinaTranslate,
    Language,
    TranslationResult,
)

TRANSLATE_URL = "https://translate.bertina.ir/api/translate"


def _mock_body(translated: str, detected: str | None = None) -> str:
    lines = [json.dumps({"response": translated, "done": False})]
    final: dict = {"response": "", "done": True}
    if detected:
        final["detectedLang"] = detected
    lines.append(json.dumps(final))
    return "\n".join(lines) + "\n"


class TestBertinaTranslate:
    def test_basic_translation(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("سلام دنیا"))
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                result = client.translate("Hello world", target=Language.FA)
        assert isinstance(result, TranslationResult)
        assert result.translated_text == "سلام دنیا"
        assert result.source_text == "Hello world"
        assert result.target_lang == Language.FA
        assert result.source_lang == Language.AUTO

    def test_explicit_source_language(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("Hello world"))
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                result = client.translate("سلام دنیا", source=Language.FA, target=Language.EN)
        assert result.source_lang == Language.FA
        assert result.target_lang == Language.EN

    def test_detected_lang_populated(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("سلام", detected="en"))
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                result = client.translate("Hello", target=Language.FA)
        assert result.detected_lang == Language.EN

    def test_no_detected_lang_when_absent(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("سلام"))
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                result = client.translate("Hello", target=Language.FA)
        assert result.detected_lang is None

    def test_request_payload(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("مرحبا"))
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp) as mock_post:
                client.translate("Hello", source=Language.EN, target=Language.AR)
        body = mock_post.call_args.kwargs["json"]
        assert body["text"] == "Hello"
        assert body["source"] == "en"
        assert body["target"] == "ar"

    def test_http_error_raises(self):
        mock_resp = MagicMock(status_code=500)
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                with pytest.raises(BertinaHTTPError) as exc_info:
                    client.translate("Hello", target=Language.FA)
        assert exc_info.value.status_code == 500

    def test_missing_translated_text_raises_parse_error(self):
        mock_resp = MagicMock(status_code=200, text='{"done":true}\n')
        with BertinaTranslate() as client:
            with patch.object(client._client, "post", return_value=mock_resp):
                with pytest.raises(BertinaParseError):
                    client.translate("Hello", target=Language.FA)

    def test_language_enum_count(self):
        assert len(Language) == 34

    def test_auto_language_value(self):
        assert Language.AUTO.value == "auto"

    def test_all_language_values_are_strings(self):
        for lang in Language:
            assert isinstance(lang.value, str)
            assert len(lang.value) >= 2


class TestAsyncBertinaTranslate:
    async def test_basic_translation(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("سلام دنیا"))
        async with AsyncBertinaTranslate() as client:
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
                result = await client.translate("Hello world", target=Language.FA)
        assert result.translated_text == "سلام دنیا"
        assert result.target_lang == Language.FA

    async def test_detected_lang_populated(self):
        mock_resp = MagicMock(status_code=200, text=_mock_body("سلام", detected="en"))
        async with AsyncBertinaTranslate() as client:
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
                result = await client.translate("Hello", target=Language.FA)
        assert result.detected_lang == Language.EN

    async def test_http_error_raises(self):
        mock_resp = MagicMock(status_code=503)
        async with AsyncBertinaTranslate() as client:
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
                with pytest.raises(BertinaHTTPError):
                    await client.translate("Hello", target=Language.FA)
