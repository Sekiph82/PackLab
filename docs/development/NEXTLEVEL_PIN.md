# NextLevel package pin

Checked: **2026-09-20**. PackLab pins the canonical [`NextLevel/NextLevel`](https://github.com/NextLevel/NextLevel) Swift package at exact version **0.19.1** in `PackLabCapture.xcodeproj/project.pbxproj`.

- Repository: `https://github.com/NextLevel/NextLevel`
- Exact tag: `0.19.1`
- Immutable tag object verified with `git ls-remote`: `3daaa0604f98936a9b79381bc76e89d283ac5028`; peeled source commit: `edb3ba52aed8b49e9e197a275ea5e4846fb8c36d`
- Upstream license: MIT, per the repository [LICENSE](https://github.com/NextLevel/NextLevel/blob/main/LICENSE)
- Pinned-manifest compatibility evidence: the [`0.19.1` `Package.swift`](https://github.com/NextLevel/NextLevel/blob/0.19.1/Package.swift) declares iOS 16 as the package deployment floor. This pinned manifest is the authoritative source for that compatibility fact; it is not inferred from README migration prose.

NextLevel is a camera-control implementation detail behind PackLab-owned camera-service interfaces. Cross-platform contracts and domain code must not expose NextLevel types or depend on its internal API. The package is present in the Xcode package graph but is not imported by the foundation UI in this child.

## Validation boundary

Windows validation checked the repository URL, exact tag/revision, project graph strings, and absence of unrelated Swift dependencies. Native Swift Package Manager/Xcode package resolution and compilation require macOS/Xcode; they are not claimed from this checkout. The project’s Swift setting is aligned to `6.0` because upstream NextLevel 0.19.1 documents Swift 6, while full strict-concurrency settings are handled by PL-0039.
