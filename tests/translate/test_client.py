from __future__ import annotations

import json

import httpx
import pytest
import respx

from bertina.exceptions import BertinaHTTPError, BertinaParseError
from bertina.translate import AsyncBertinaTranslate, BertinaTranslate, Language, TranslationResult

TRANSLATE_URL = "https://translate.bertina.ir/api/translate"


def _mock_body(translated: str, detected: str | None = None) -> str:
    """Build a mock NDJSON body matching the real API stream format."""
    import json
    lines = [json.dumps({"response": translated, "done": False})]
    final: dict = {"response": "", "done": True}
    if detected:
        final["detectedLang"] = detected
    lines.append(json.dumps(final))
    return "\n".join(lines) + "\n"


class TestBertinaTranslate:
    @respx.mock
    def test_basic_translation(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("سلام دنیا"))
        )
        with BertinaTranslate() as client:
            result = client.translate("Hello world", target=Language.FA)
        assert isinstance(result, TranslationResult)
        assert result.translated_text == "سلام دنیا"
        assert result.source_text == "Hello world"
        assert result.target_lang == Language.FA
        assert result.source_lang == Language.AUTO

    @respx.mock
    def test_explicit_source_language(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("Hello world"))
        )
        with BertinaTranslate() as client:
            result = client.translate("سلام دنیا", source=Language.FA, target=Language.EN)
        assert result.source_lang == Language.FA
        assert result.target_lang == Language.EN

    @respx.mock
    def test_detected_lang_populated(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("سلام", detected="en"))
        )
        with BertinaTranslate() as client:
            result = client.translate("Hello", target=Language.FA)
        assert result.detected_lang == Language.EN

    @respx.mock
    def test_no_detected_lang_when_absent(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("سلام"))
        )
        with BertinaTranslate() as client:
            result = client.translate("Hello", target=Language.FA)
        assert result.detected_lang is None

    @respx.mock
    def test_request_payload(self):
        route = respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("مرحبا"))
        )
        with BertinaTranslate() as client:
            client.translate("Hello", source=Language.EN, target=Language.AR)
        body = json.loads(route.calls[0].request.content)
        assert body["text"] == "Hello"
        assert body["source"] == "en"
        assert body["target"] == "ar"

    @respx.mock
    def test_http_error_raises(self):
        respx.post(TRANSLATE_URL).mock(return_value=httpx.Response(500))
        with BertinaTranslate() as client:
            with pytest.raises(BertinaHTTPError) as exc_info:
                client.translate("Hello", target=Language.FA)
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_missing_translated_text_raises_parse_error(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text='{"done":true}\n')
        )
        with BertinaTranslate() as client:
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
    @respx.mock
    async def test_basic_translation(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("سلام دنیا"))
        )
        async with AsyncBertinaTranslate() as client:
            result = await client.translate("Hello world", target=Language.FA)
        assert result.translated_text == "سلام دنیا"
        assert result.target_lang == Language.FA

    @respx.mock
    async def test_detected_lang_populated(self):
        respx.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, text=_mock_body("سلام", detected="en"))
        )
        async with AsyncBertinaTranslate() as client:
            result = await client.translate("Hello", target=Language.FA)
        assert result.detected_lang == Language.EN

    @respx.mock
    async def test_http_error_raises(self):
        respx.post(TRANSLATE_URL).mock(return_value=httpx.Response(503))
        async with AsyncBertinaTranslate() as client:
            with pytest.raises(BertinaHTTPError):
                await client.translate("Hello", target=Language.FA)
