# PL-0366 Offline Release Checklist Policy

The supported interface is the `tools/release/offline_release_checklist.py` CLI. It validates a JSON candidate against the exact clean source commit, current release-train tuple, checked task IDs in root `TASKS.md`, and the latest matching task or M17 audit. Its internal evidence-field helper does not perform source/train binding and is not a public acceptance result. The input shape is in `schemas/release/release-checklist-input.schema.json`.

Every required gate must reference its latest task-specific `*_CHATGPT_AUDIT_VNN.md`, an accepted task ID, a final `AUDITED_PASS` decision, matching current source SHA, and an explicit `Gate Coverage:` entry. Artifact gates also bind SHA-256, byte length, and workflow run ID in that audit. A Codex log, an older audit, a mismatched source, missing field, link/reparse path, or unchecked/unknown task cannot satisfy a gate. `signed_ipa` is required only for `SIGNED_DISTRIBUTION`; unsigned internal intent requires it to be `null`.

M17 acceptance must cite the latest M17 milestone audit and exact source commit before PL-0368 can advance. Formal legal review is deliberately fixed to `PENDING` in this schema/version: a Markdown approval claim cannot authenticate the owner or legal reviewer, and embedding the current commit SHA in the same committed record creates a self-reference. No legal approval is inferred. An authenticated external approval workflow must be designed before this gate can be advanced. Physical validation remains explicitly pending until accepted evidence is provided. Pending states must appear in `known_limitations`; accepted statuses cannot contradict pending limitation codes. The validator emits a checklist outside the repository using exclusive-create semantics, includes blocker codes, and always states `NOT_GRANTED` for release authorization. A checklist pass is not legal clearance, an Apple signing claim, device acceptance, or permission to publish a tag or release.

Invocation requires a clean source checkout and exact current train identity:

```sh
python tools/release/offline_release_checklist.py candidate.json --repo . --output /outside/repo/release-checklist.md
```

The command exits `2` for blocked evidence, nonzero source/train mismatch, or output safety failure. Do not include credentials, signing material, private artifacts, local paths, or private sample data in candidate evidence or audits.
