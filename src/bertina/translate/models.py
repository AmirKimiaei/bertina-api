from __future__ import annotations

from dataclasses import dataclass

from .languages import Language


@dataclass(slots=True)
class TranslationResult:
    source_text: str
    translated_text: str
    source_lang: Language
    target_lang: Language
    detected_lang: Language | None = None
