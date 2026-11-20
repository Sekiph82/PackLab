"""Device regression: buttons sharing a Form/List row must be borderless.

On iOS a tap on a Form/List row fires every default-style button in that row, so the
New Scan "Start" button also ran "Cancel" and dismissed the wizard on the owner's iPhone.
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "apps" / "ios-capture" / "PackLabCapture"


def _hstack_blocks(text: str) -> list[str]:
    blocks = []
    for match in re.finditer(r"HStack \{", text):
        depth, index = 0, match.end() - 1
        for index in range(match.end() - 1, len(text)):
            depth += {"{": 1, "}": -1}.get(text[index], 0)
            if depth == 0:
                break
        blocks.append(text[match.start() : index + 1])
    return blocks


def test_every_row_with_several_buttons_uses_borderless_buttons() -> None:
    session = (APP / "Services" / "SessionFoundation.swift").read_text(encoding="utf-8")
    offenders = []
    for block in _hstack_blocks(session):
        buttons = block.count('Button("')
        if buttons >= 2 and block.count(".buttonStyle(.borderless)") < buttons:
            offenders.append(block.splitlines()[1].strip())
    assert offenders == []


def test_new_scan_start_and_cancel_are_borderless() -> None:
    session = (APP / "Services" / "SessionFoundation.swift").read_text(encoding="utf-8")
    wizard = session[session.index("public struct NewScanWizard") :]
    row = _hstack_blocks(wizard)[0]
    assert 'Button("Cancel")' in row and 'Button("Start")' in row
    assert row.count(".buttonStyle(.borderless)") == 2
