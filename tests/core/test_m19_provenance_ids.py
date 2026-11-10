"""Review F-3: AI-proposal provenance identifiers are opaque IDs, never paths or control text."""

from __future__ import annotations

import pytest

from packlab_core.dimension_fit_proposal import (
    DimensionFitProposalError,
    DimensionFitProposalProvenance,
)
from packlab_core.package_family_suggestion import (
    PackageFamilySuggestionError,
    PackageFamilySuggestionProvenance,
)
from packlab_core.profile_zone_proposal import (
    ProfileZoneProposalError,
    ProfileZoneProposalProvenance,
)

KINDS = (
    (PackageFamilySuggestionProvenance, PackageFamilySuggestionError),
    (ProfileZoneProposalProvenance, ProfileZoneProposalError),
    (DimensionFitProposalProvenance, DimensionFitProposalError),
)
BAD = (
    r"C:\Users\someone\models\weights.pt",
    "/home/someone/checkpoint.bin",
    "models/weights.pt",
    "with space",
    "nul\x00byte",
    "line\nbreak",
    "",
    "-leading-dash",
    "x" * 161,
)


@pytest.mark.parametrize(("provenance", "error"), KINDS)
@pytest.mark.parametrize("field", range(4))
@pytest.mark.parametrize("bad", BAD)
def test_path_or_control_text_is_rejected_in_every_provenance_field(
    provenance: type, error: type, field: int, bad: str
) -> None:
    values = ["fake-backend", "fake-model", "not-selected", "test-v1"]
    values[field] = bad
    with pytest.raises(error):
        provenance(*values)


@pytest.mark.parametrize(("provenance", "error"), KINDS)
def test_opaque_identifiers_are_accepted(provenance: type, error: type) -> None:
    provenance("onnx-runtime", "family-cls:v2.1", "ckpt_2026-11@sha", "1.4.0+local")
