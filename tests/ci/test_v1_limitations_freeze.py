"""PL-0395: the frozen V1 limitations / no-direct-mold statement cannot silently regress."""

from __future__ import annotations

import re
from pathlib import Path

from packlab_core.reconstruction import ScaleState

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "development"
    / "V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md"
)
NO_MOLD = (
    "**PackLab V1 outputs must not be sent directly to manufacture a mold, tooling, production "
    "container, closure, or other production part. PackLab does not authorize mold manufacture "
    "or production release.**"
)
CLAIM = re.compile(r"\b(validated|accepted|production[- ]ready|certified|guaranteed)\b", re.I)
QUALIFIER = re.compile(
    r"\b(not|no|never|until|unless|before|without|only|nor|pending|separate\w*|must|do)\b", re.I
)


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_frozen_revision_and_no_mold_statement_are_present() -> None:
    text = _text()
    assert "frozen V1 boundary statement, revision 1.1" in text
    assert NO_MOLD in text
    assert re.search(r"^\| 1\.1 \| 2026-11-10 \|", text, re.M)


def test_every_required_gap_family_is_stated() -> None:
    text = _text().lower()
    for gap in (
        "relative scale",
        "metric-unverified",
        "low-texture",
        "glossy",
        "transparent pet",
        "parametric fit",
        "step round trip",
        "iphone 16",
        "github actions artifact",
        "kenya",
        "regulatory",
        "supplier approval",
    ):
        assert gap in text, gap


def test_scale_vocabulary_matches_the_code() -> None:
    assert {state.value for state in ScaleState} >= {"relative", "metric-unverified"}
    assert "mm_unverified" in _text()


def test_claim_words_are_always_qualified() -> None:
    for sentence in re.split(r"(?<=[.!?])\s+|\n", _text()):
        if CLAIM.search(sentence):
            assert QUALIFIER.search(sentence), sentence.strip()[:160]


FROZEN_SHA256 = "cc8aeb9497858adf078319b3991b00a878aa4ede9bcbcbd3f56873186aa2641f"


def test_frozen_text_is_pinned_by_digest() -> None:
    # Review P3-3: keyword checks alone missed inverted or deleted sentences. Any change to
    # the frozen statement must update this pin together with a new revision-history row.
    import hashlib

    data = DOC.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(data).hexdigest() == FROZEN_SHA256
