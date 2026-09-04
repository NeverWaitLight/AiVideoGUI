"""Incrementally parse objects from a JSON array in LLM streaming output."""

from __future__ import annotations

import json
import re
from typing import Any


class StreamingJsonArrayParser:
    """Scan streaming LLM output for complete objects inside a named JSON array."""

    def __init__(self, array_key: str) -> None:
        self._array_key = array_key
        self._buffer = ""
        self._array_start: int | None = None
        self._scan_pos = 0

    @property
    def buffer(self) -> str:
        return self._buffer

    def feed(self, chunk: str) -> list[dict[str, Any]]:
        self._buffer += chunk
        self._locate_array_start()
        return self._extract_new_objects()

    def _clean_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _locate_array_start(self) -> None:
        if self._array_start is not None:
            return
        cleaned = self._clean_text(self._buffer)
        pattern = rf'"{re.escape(self._array_key)}"\s*:\s*\['
        match = re.search(pattern, cleaned)
        if match:
            self._array_start = match.end()
            self._scan_pos = self._array_start
            self._buffer = cleaned

    def _extract_new_objects(self) -> list[dict[str, Any]]:
        if self._array_start is None:
            return []

        results: list[dict[str, Any]] = []
        pos = self._scan_pos
        buf = self._buffer

        while pos < len(buf):
            while pos < len(buf) and buf[pos] in " \t\n\r,":
                pos += 1
            if pos >= len(buf):
                break
            if buf[pos] == "]":
                break
            if buf[pos] != "{":
                pos += 1
                continue

            end = self._find_object_end(buf, pos)
            if end is None:
                break

            obj_str = buf[pos:end]
            try:
                decoder = json.JSONDecoder(strict=False)
                obj, _ = decoder.raw_decode(obj_str)
            except json.JSONDecodeError:
                break

            if isinstance(obj, dict):
                results.append(obj)
            pos = end

        self._scan_pos = pos
        return results

    @staticmethod
    def _find_object_end(text: str, start: int) -> int | None:
        depth = 0
        in_string = False
        escape = False
        i = start
        while i < len(text):
            ch = text[i]
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\" and in_string:
                escape = True
                i += 1
                continue
            if ch == '"':
                in_string = not in_string
            elif not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return i + 1
            i += 1
        return None
