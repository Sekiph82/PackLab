from __future__ import annotations

import json
from dataclasses import replace

import pytest
from tests.core.test_cross_section_overlay import _cube, _scan

from packlab_core.assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    AssemblyGraphError,
    AssemblyRelationshipKind,
    create_parametric_assembly_graph,
    validate_parametric_assembly_graph,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision

PROJECT = "f3343d5e-bf9c-44ab-b519-bbdfca5401a0"
ACTOR = "assembly-fixture-operator"
CREATED = "2026-10-04T13:00:00Z"
ROLE_KIND = {
    AssemblyComponentRole.BODY: FeatureKind.BODY,
    AssemblyComponentRole.CLOSURE: FeatureKind.CAP,
    AssemblyComponentRole.TRIGGER_PUMP: FeatureKind.TRIGGER_PUMP,
    AssemblyComponentRole.DIP_TUBE: FeatureKind.DIP_TUBE,
}


def _components(
    *, scale: ScaleState = ScaleState.METRIC_UNVERIFIED, scan_id: str = "assembly-scan-r1"
) -> tuple[AssemblyComponentInput, ...]:
    base = _scan(_cube(), scale=scale)
    manifest = json.loads(base.manifest_bytes())
    manifest["scan_master_revision_id"] = scan_id
    manifest["scale_provenance_id"] = f"scale-{scale.value}-{scan_id}"
    provenance = manifest.get("scale_provenance")
    if isinstance(provenance, dict):
        provenance["provenance_id"] = manifest["scale_provenance_id"]
        provenance["scale_state"] = scale.value
    scan = ScanMasterRevision(scan_id, PROJECT, base.mesh, manifest)
    binding = bind_design_model_parent(
        scan,
        actor_id=ACTOR,
        reason="Pin a public synthetic assembly graph fixture.",
        created_at_utc=CREATED,
    )
    result = []
    for role, kind in ROLE_KIND.items():
        component_id = f"fixture-{role.value.replace('_', '-')}"
        semantic = f"{role.value}-reference"
        feature = DesignModelFeatureReference(
            stable_feature_id(component_id, kind, semantic), component_id, kind, semantic
        )
        model = create_design_model_revision(
            binding,
            package_family=PackageFamily.OTHER,
            features=(feature,),
            actor_id=ACTOR,
            reason=f"Create synthetic {role.value} component revision.",
            created_at_utc=CREATED,
        )
        result.append(AssemblyComponentInput(role, model, model.revision_id, feature.feature_id))
    return tuple(result)


def _expected(components: tuple[AssemblyComponentInput, ...]) -> dict[AssemblyComponentRole, str]:
    return {item.role: item.model.revision_id for item in components}


def _create(components: tuple[AssemblyComponentInput, ...]):
    return create_parametric_assembly_graph(
        components,
        expected_component_revision_ids=_expected(components),
        actor_id=ACTOR,
        reason="Compose exact body, closure, trigger/pump and dip-tube revisions.",
        created_at_utc=CREATED,
    )


def test_four_role_graph_is_deterministic_immutable_and_preserves_component_parents() -> None:
    components = _components()
    first = _create(components)
    second = _create(tuple(reversed(components)))

    assert first == second
    assert first.revision_id == second.revision_id
    assert tuple(item.role for item in first.components) == tuple(
        sorted(ROLE_KIND, key=lambda role: role.value)
    )
    assert {item.kind for item in first.relationships} == set(AssemblyRelationshipKind)
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.coordinate_unit == "mm_unverified"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False
    payload = first.as_dict()
    assert payload["authority_class"] == "PARAMETRIC_ASSEMBLY_METADATA"
    assert payload["geometry_embedded"] is False
    assert payload["geometry_exported"] is False
    references = {item.role: item for item in first.components}
    for component in components:
        reference = references[component.role]
        assert reference.model_revision_id == component.model.revision_id
        assert reference.feature_id == component.feature_id
        assert reference.parent_binding_revision_id == component.model.parent_binding_revision_id
        assert (
            reference.scan_master_revision_id == component.model.fitted_to_scan_master_revision_id
        )
        assert reference.scan_master_geometry_sha256 == component.model.scan_master_geometry_sha256
        assert reference.scale_provenance_id == component.model.scale_provenance_id
        assert reference.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    validate_parametric_assembly_graph(first, components)
    with pytest.raises((AttributeError, TypeError)):
        first.components = ()  # type: ignore[misc]


def test_missing_and_duplicate_roles_reject() -> None:
    components = _components()
    with pytest.raises(AssemblyGraphError, match="required_component_role_missing"):
        _create(components[:-1])
    with pytest.raises(AssemblyGraphError, match="component_role_duplicate"):
        _create((*components[:-1], components[0]))


def test_stale_model_and_stale_feature_references_reject_without_retargeting() -> None:
    components = _components()
    stale = replace(components[0], expected_model_revision_id="design-model:stale")
    with pytest.raises(AssemblyGraphError, match="component_revision_stale"):
        _create((stale, *components[1:]))

    graph = _create(components)
    stale_current = (replace(components[0], feature_id="packlab-feature:stale"), *components[1:])
    with pytest.raises(AssemblyGraphError, match="component_revision_stale"):
        validate_parametric_assembly_graph(graph, stale_current)


def test_incompatible_scale_states_reject_and_preserve_exact_scan_ancestry() -> None:
    metric = _components()
    relative = _components(scale=ScaleState.RELATIVE, scan_id="assembly-scan-relative-r1")
    mixed = (*metric[:3], relative[3])
    with pytest.raises(AssemblyGraphError, match="unit_or_scale_mismatch"):
        _create(mixed)

    graph = _create(relative)
    assert graph.scale_state is ScaleState.RELATIVE
    assert graph.coordinate_unit == "reconstruction_units"
    assert {item.scan_master_revision_id for item in graph.components} == {
        "assembly-scan-relative-r1"
    }
