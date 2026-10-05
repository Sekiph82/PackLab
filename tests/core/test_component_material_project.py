from __future__ import annotations

import hashlib
import json

import pytest
from tests.core.test_label_zone import COMPONENT_ID, _model

from packlab_core.component_material_project import (
    ComponentMaterialProjectEntry,
    ComponentMaterialProjectError,
    create_component_material_project,
    deserialize_component_material_project,
    remove_component_material_project_entry,
    replace_component_material_project_entry,
)
from packlab_core.component_visual_assignments import (
    GeometryMaterialAssignmentRevision,
    create_component_visual_assignment_state,
    create_content_appearance_assignment,
    create_geometry_material_assignment,
    remove_content_appearance_assignment,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.pcr_material_declarations import (
    PCRDeclarationStatus,
    create_pcr_declaration,
    create_pcr_visual_variant,
)
from packlab_core.visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialRecord,
    create_visual_material_library,
)

SECOND_COMPONENT_ID = "package-cap"
SECOND_FEATURE_ID = stable_feature_id(SECOND_COMPONENT_ID, FeatureKind.CAP, "closure")


def _model_with_two_components(*, include_second: bool = True):
    base = _model(label=f"material-project-{include_second}")
    if not include_second:
        return base
    assert base.standalone_root is not None
    return create_standalone_design_model_revision(
        base.standalone_root,
        package_family=base.package_family,
        parameters=base.parameters,
        features=(
            *base.features,
            DesignModelFeatureReference(
                SECOND_FEATURE_ID, SECOND_COMPONENT_ID, FeatureKind.CAP, "closure"
            ),
        ),
        actor_id="operator-1",
        reason="Add the second component for material project persistence coverage.",
        created_at_utc=base.created_at_utc,
    )


def _library():
    return create_visual_material_library(
        (
            VisualMaterialRecord(
                "material-hdpe",
                MaterialFamily.HDPE,
                "HDPE visual reference",
                (0.8, 0.85, 0.9, 1.0),
                0.0,
                0.4,
                MaterialSourceClass.USER_AUTHORED_VISUAL,
            ),
            VisualMaterialRecord(
                "material-pp",
                MaterialFamily.PP,
                "PP visual reference",
                (0.2, 0.3, 0.4, 1.0),
                0.0,
                0.5,
                MaterialSourceClass.USER_AUTHORED_VISUAL,
            ),
        )
    )


def _entry(model, library, component_id: str, *, with_content: bool = False):
    geometry = create_geometry_material_assignment(model, component_id, library, "material-hdpe")
    content = None
    if with_content:
        content = create_content_appearance_assignment(
            model,
            component_id,
            display_name="Visual content",
            display_color_rgba=(0.2, 0.4, 0.6, 0.5),
            opacity_factor=0.5,
        )
    state = create_component_visual_assignment_state(geometry, content)
    declaration = create_pcr_declaration(
        material_id="material-hdpe",
        recycled_content_percentage=35,
        status=PCRDeclarationStatus.DECLARED,
        design_model_revision_id=model.revision_id,
        component_id=component_id,
    )
    variant = create_pcr_visual_variant(
        declaration,
        variant_id=f"variant-{component_id}",
        display_name="Grey PCR visual swatch",
        appearance_color_rgba=(0.4, 0.4, 0.4, 1.0),
        design_model_revision_id=model.revision_id,
        component_id=component_id,
    )
    return ComponentMaterialProjectEntry(component_id, state, declaration, (variant,))


def test_round_trip_persists_multiple_components_and_optional_channels() -> None:
    model = _model_with_two_components()
    library = _library()
    before_geometry = model.as_dict()
    first = _entry(model, library, COMPONENT_ID, with_content=True)
    second = _entry(model, library, SECOND_COMPONENT_ID)
    document = create_component_material_project(model, library, (second, first))

    restored = deserialize_component_material_project(document.canonical_bytes(), model, library)

    assert restored == document
    assert [item.component_id for item in restored.entries] == [COMPONENT_ID, SECOND_COMPONENT_ID]
    assert restored.entries[0].visual_state.content_appearance_assignment is not None
    assert restored.entries[1].visual_state.content_appearance_assignment is None
    assert restored.entries[0].pcr_declaration is not None
    assert restored.entries[0].pcr_visual_variants[0].material_id == "material-hdpe"
    assert model.as_dict() == before_geometry


def test_storage_is_deterministic_normalized_and_privacy_safe() -> None:
    model = _model_with_two_components()
    library = _library()
    first = _entry(model, library, COMPONENT_ID)
    second = _entry(model, library, SECOND_COMPONENT_ID)
    forward = create_component_material_project(model, library, (first, second))
    reverse = create_component_material_project(model, library, (second, first))

    assert forward == reverse
    assert forward.revision_id == reverse.revision_id
    assert forward.canonical_bytes() == reverse.canonical_bytes()
    assert str(__import__("pathlib").Path.cwd()).encode() not in forward.canonical_bytes()
    assert json.loads(forward.canonical_bytes())["body"]["schema_version"] == 1


def test_replacement_and_removal_create_new_snapshots_without_mutating_model() -> None:
    model = _model(label="material-project-replace")
    library = _library()
    original = _entry(model, library, COMPONENT_ID, with_content=True)
    before = model.as_dict()
    first_document = create_component_material_project(model, library, (original,))

    previous_geometry = original.visual_state.geometry_material_assignment
    assert previous_geometry is not None
    replacement_geometry = create_geometry_material_assignment(
        model,
        COMPONENT_ID,
        library,
        "material-pp",
        previous=previous_geometry,
    )
    assert original.pcr_declaration is not None
    replacement_declaration = create_pcr_declaration(
        material_id="material-pp",
        recycled_content_percentage=35,
        status=PCRDeclarationStatus.DECLARED,
        design_model_revision_id=model.revision_id,
        component_id=COMPONENT_ID,
    )
    replacement_variant = create_pcr_visual_variant(
        replacement_declaration,
        variant_id="variant-replaced",
        display_name="Replacement swatch",
        appearance_color_rgba=(0.1, 0.2, 0.3, 1.0),
        design_model_revision_id=model.revision_id,
        component_id=COMPONENT_ID,
    )
    replacement = ComponentMaterialProjectEntry(
        COMPONENT_ID,
        create_component_visual_assignment_state(
            replacement_geometry, original.visual_state.content_appearance_assignment
        ),
        replacement_declaration,
        (replacement_variant,),
    )
    replaced_document = replace_component_material_project_entry(
        first_document, model, library, replacement
    )
    assert replaced_document.revision_id != first_document.revision_id
    assert first_document.entries[0] == original
    assert (
        replaced_document.entries[0].visual_state.geometry_material_assignment.material_id
        == "material-pp"
    )

    content_assignment = replacement.visual_state.content_appearance_assignment
    assert content_assignment is not None
    removed_content = remove_content_appearance_assignment(content_assignment)
    assert removed_content.status == "REMOVED"
    channel_removed = ComponentMaterialProjectEntry(
        COMPONENT_ID,
        create_component_visual_assignment_state(replacement_geometry),
        replacement_declaration,
        (replacement_variant,),
    )
    channel_removed_document = replace_component_material_project_entry(
        replaced_document, model, library, channel_removed
    )
    assert channel_removed_document.entries[0].visual_state.content_appearance_assignment is None
    assert (
        channel_removed_document.entries[0].visual_state.geometry_material_assignment
        == replacement_geometry
    )

    removed_document = remove_component_material_project_entry(
        channel_removed_document, model, library, COMPONENT_ID
    )
    assert removed_document.entries == ()
    assert removed_document.revision_id != replaced_document.revision_id
    assert model.as_dict() == before


def test_stale_model_component_material_and_ambiguous_entries_fail_closed() -> None:
    model = _model_with_two_components()
    library = _library()
    entry = _entry(model, library, SECOND_COMPONENT_ID)
    with pytest.raises(ComponentMaterialProjectError, match="design_model_stale"):
        deserialize_component_material_project(
            create_component_material_project(model, library, (entry,)).canonical_bytes(),
            _model_with_two_components(include_second=False),
            library,
        )

    duplicate = ComponentMaterialProjectEntry(
        SECOND_COMPONENT_ID, entry.visual_state, entry.pcr_declaration, entry.pcr_visual_variants
    )
    with pytest.raises(ComponentMaterialProjectError, match="component_ambiguous"):
        create_component_material_project(model, library, (entry, duplicate))


def test_assignment_to_missing_component_rejects_even_when_record_is_well_formed() -> None:
    model = _model(label="material-project-stale-component")
    library = _library()
    component_id = "component-deleted"
    identity = {
        "contract": "packlab.geometry-material-assignment.v1",
        "source_design_model_revision_id": model.revision_id,
        "component_id": component_id,
        "material_library_revision_id": library.revision_id,
        "material_id": "material-hdpe",
        "status": "ASSIGNED",
        "previous_revision_id": None,
    }
    revision_id = (
        "geometry-material-assignment:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    geometry = GeometryMaterialAssignmentRevision(
        revision_id,
        model.revision_id,
        component_id,
        library.revision_id,
        "material-hdpe",
        "ASSIGNED",
        None,
    )
    entry = ComponentMaterialProjectEntry(
        component_id, create_component_visual_assignment_state(geometry)
    )

    with pytest.raises(ComponentMaterialProjectError, match="component_stale_or_deleted"):
        create_component_material_project(model, library, (entry,))


def test_schema_version_is_explicit_and_unknown_migration_fails_closed() -> None:
    model = _model(label="material-project-version")
    library = _library()
    document = create_component_material_project(
        model, library, (_entry(model, library, COMPONENT_ID),)
    )
    envelope = json.loads(document.canonical_bytes())
    envelope["body"]["schema_version"] = 2
    envelope["content_sha256"] = hashlib.sha256(
        json.dumps(
            envelope["body"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()

    with pytest.raises(ComponentMaterialProjectError, match="schema_version_unsupported"):
        deserialize_component_material_project(json.dumps(envelope), model, library)

    envelope["body"]["schema_version"] = True
    envelope["content_sha256"] = hashlib.sha256(
        json.dumps(
            envelope["body"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ComponentMaterialProjectError, match="schema_version_unsupported"):
        deserialize_component_material_project(json.dumps(envelope), model, library)


def test_corruption_and_duplicate_json_keys_are_rejected() -> None:
    model = _model(label="material-project-integrity")
    library = _library()
    document = create_component_material_project(
        model, library, (_entry(model, library, COMPONENT_ID),)
    )
    encoded = document.canonical_bytes()
    with pytest.raises(ComponentMaterialProjectError, match="integrity_or_authority_invalid"):
        deserialize_component_material_project(
            encoded.replace(b"material-hdpe", b"material-pp"), model, library
        )
    with pytest.raises(ComponentMaterialProjectError, match="duplicate_key"):
        deserialize_component_material_project(
            b'{"body":{},"body":{},"content_sha256":"' + b"0" * 64 + b'"}',
            model,
            library,
        )


def test_pcr_claim_limitations_survive_project_round_trip() -> None:
    model = _model(label="material-project-pcr-semantics")
    library = _library()
    entry = _entry(model, library, COMPONENT_ID)
    document = deserialize_component_material_project(
        create_component_material_project(model, library, (entry,)).canonical_bytes(),
        model,
        library,
    )
    serialized = document.entries[0].pcr_declaration.as_dict()

    assert serialized["recycled_content_certified"] is False
    assert serialized["external_reference_independently_verified_by_packlab"] is False
    assert serialized["environmental_performance_verified"] is False
    assert serialized["regulatory_approval"] is False
