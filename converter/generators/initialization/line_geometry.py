from __future__ import annotations

from typing import List

from rules.initialization_placement_rules import (
    BODY_END,
    BODY_START,
    COMMENT_INDICATORS,
    LINE_WIDTH,
    SEQUENCE_WIDTH,
    STATEMENT_INDENT,
    VALID_INDICATORS,
)


class LineGeometry:

    @staticmethod
    def split(text: str) -> List[str]:
        return (
            str(text or "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

    @staticmethod
    def join(lines: List[str]) -> str:
        return "\n".join(lines)

    @staticmethod
    def is_fixed(line: str) -> bool:
        text = str(line or "")
        if len(text) <= BODY_START:
            return False
        return text[:SEQUENCE_WIDTH].isdigit()

    @classmethod
    def body(cls, line: str) -> str:
        text = str(line or "").rstrip("\r\n")
        if not text:
            return ""
        if cls.is_fixed(text):
            return text[BODY_START:BODY_END].strip()
        return text.strip()

    @classmethod
    def indicator(cls, line: str) -> str:
        text = str(line or "")
        if cls.is_fixed(text):
            return text[SEQUENCE_WIDTH:BODY_START]
        stripped = text.lstrip()
        if stripped[:1] in COMMENT_INDICATORS:
            return stripped[:1]
        return " "

    @classmethod
    def is_comment(cls, line: str) -> bool:
        return cls.indicator(line) in COMMENT_INDICATORS

    @classmethod
    def is_comment_or_blank(cls, line: str) -> bool:
        if cls.is_comment(line):
            return True
        return not cls.body(line)

    @classmethod
    def indent_of(cls, line: str) -> str:
        text = str(line or "").rstrip("\r\n")
        if cls.is_fixed(text):
            region = text[BODY_START:BODY_END]
        else:
            region = text
        stripped = region.lstrip(" ")
        width = len(region) - len(stripped)
        return " " * width if width > 0 else STATEMENT_INDENT

    @classmethod
    def statement(cls, body: str, indent: str = STATEMENT_INDENT) -> str:
        return f"{indent}{str(body or '').strip()}"

    @classmethod
    def replace_body(cls, line: str, body: str) -> str:
        text = str(line or "").rstrip("\r\n")
        clean = str(body or "").strip()
        if not cls.is_fixed(text):
            return cls.statement(clean, cls.indent_of(text))
        left = text[:SEQUENCE_WIDTH]
        mark = text[SEQUENCE_WIDTH:BODY_START]
        if mark not in VALID_INDICATORS:
            mark = " "
        right = text[BODY_END:LINE_WIDTH]
        width = BODY_END - BODY_START
        rendered = f"{cls.indent_of(text)}{clean}"[:width].ljust(width)
        return f"{left}{mark}{rendered}{right}"

    @classmethod
    def logical_bodies(cls, lines: List[str]) -> List[str]:
        return [
            cls.body(line)
            for line in lines
            if not cls.is_comment_or_blank(line)
        ]

    @classmethod
    def logical_text(cls, lines: List[str]) -> str:
        return "\n".join(cls.logical_bodies(lines)).upper()


__all__ = ["LineGeometry"]