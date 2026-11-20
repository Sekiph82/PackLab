"""Device regression: buttons sharing a Form/List row must be borderless.

On iOS a tap on a Form/List row fires every default-style button in that row. On the
owner's iPhone the New Scan "Start" button also ran "Cancel" (no scan ever started), and
the same pattern let "Resume" also run "Discard" (deleting the session).
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "apps" / "ios-capture" / "PackLabCapture"
BUTTON = re.compile(r"\bButton\s*(?:\(|\{)")


def _block(text: str, open_brace: int) -> str:
    depth = 0
    for index in range(open_brace, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return text[open_brace : index + 1]
    return text[open_brace:]


def _blocks(text: str, pattern: str) -> list[str]:
    return [_block(text, m.end() - 1) for m in re.finditer(pattern, text)]


def _offending_rows(text: str) -> list[str]:
    offenders = []
    for container in _blocks(text, r"\b(?:List\([^)]*\)\s*(?:\{\s*\w+\s+in)?|Form)\s*\{"):
        for row in _blocks(container, r"\b(?:HStack|VStack)(?:\([^)]*\))?\s*\{"):
            buttons = len(BUTTON.findall(row))
            if buttons >= 2 and row.count(".buttonStyle(.borderless)") < buttons:
                offenders.append(row.splitlines()[0].strip()[:80])
    return offenders


def test_no_list_or_form_row_has_several_default_style_buttons() -> None:
    found = {
        path.name: rows
        for path in sorted(APP.rglob("*.swift"))
        if (rows := _offending_rows(path.read_text(encoding="utf-8")))
    }
    assert found == {}


def test_guard_detects_the_original_device_bugs() -> None:
    new_scan = 'Form { HStack { Button("Cancel") { a() }; Button("Start") { b() } } }'
    resume = (
        'List(items) { item in VStack { Button("Resume") { a() }; Button("Discard") { b() } } }'
    )
    fixed = (
        'Form { HStack { Button("Cancel") { a() }.buttonStyle(.borderless); '
        'Button("Start") { b() }.buttonStyle(.borderless) } }'
    )
    assert _offending_rows(new_scan)
    assert _offending_rows(resume)
    assert _offending_rows(fixed) == []
