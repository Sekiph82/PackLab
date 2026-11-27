from __future__ import annotations

import hashlib

from packlab_studio.project_layout import ProjectLayout
from packlab_studio.provenance import ArtifactStatus, ProvenanceManager


def test_direct_transitive_unrelated_and_parameter_invalidation(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    manager = ProvenanceManager(layout)
    manager.register(
        "a",
        "derived/a.bin",
        input_digests={"working/source.bin": "digest"},
        project_revision=1,
        parameters={"quality": 1},
    )
    manager.register(
        "b", "derived/b.bin", upstream=("a",), project_revision=1, parameters={"quality": 1}
    )
    manager.register(
        "c",
        "derived/c.bin",
        input_digests={"working/other.bin": "digest"},
        project_revision=1,
        parameters={"quality": 1},
    )
    changed = manager.invalidate(changed_inputs={"working/source.bin"})
    assert {record.artifact_id for record in changed} == {"a", "b"}
    assert manager.get("c").status is ArtifactStatus.FRESH
    manager.invalidate(changed_parameters={"quality": 2})
    assert manager.get("a").status is ArtifactStatus.STALE


def test_missing_or_tampered_input_is_invalid_and_raw_unchanged(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    source = layout.path("raw", "source.bin")
    source.write_bytes(b"authoritative")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manager = ProvenanceManager(layout)
    manager.register(
        "artifact",
        "derived/artifact.bin",
        input_digests={"raw/source.bin": digest},
        project_revision=1,
    )
    source.write_bytes(b"tampered")
    invalid = manager.refresh_integrity()
    assert invalid[0].status is ArtifactStatus.INVALID
    assert source.read_bytes() == b"tampered"


def test_concurrent_builds_never_drop_each_others_records(tmp_path) -> None:
    import threading

    layout = ProjectLayout.create(tmp_path / "project")
    managers = [ProvenanceManager(layout) for _ in range(4)]  # one per build, loaded up front

    def register(index: int) -> None:
        for step in range(15):
            managers[index].register(
                f"build-{index}-{step}", f"derived/{index}.bin", project_revision=1
            )

    threads = [threading.Thread(target=register, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    records = {record.artifact_id for record in ProvenanceManager(layout).records()}
    assert records == {f"build-{index}-{step}" for index in range(4) for step in range(15)}
