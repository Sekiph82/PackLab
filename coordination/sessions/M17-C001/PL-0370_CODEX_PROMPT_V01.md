# PL-0370 — Codex Prompt V01

Task: **Create a bounded private local real-packaging reference corpus outside Git**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

The owner clarified on 2026-11-04 that the Kenya factory is not built and no private Kenya scans exist, and directed Codex to create data independently without requesting a path or photos. This prompt narrows “Kenya benchmark dataset” to the locally hosted software-validation corpus and reserves actual Kenya physical validation for the future.

## Scope

- Store full source archives and derived references only in `%LOCALAPPDATA%/PackLab/datasets/M17`, outside Git.
- Use the official YCB Object and Model Set `006_mustard_bottle` and `021_bleach_cleanser` Google 16k scans and a bounded selection of 30 real Berkeley mustard-bottle RGB frames, where the exact source/license and archive integrity are recorded.
- Record archive and extracted-file byte counts/hashes, attribution/license URI, source member names, real-vs-synthetic identity, frame selection, camera-calibration availability, model/photo registration status, and measurement authority.
- Keep YCB data under its upstream CC BY 4.0 terms. Do not treat the owner-authorized internal-use terms for PackLab-created synthetic data as restrictions on YCB data. Do not represent third-party marks as cleared.
- Add a fail-closed validator for the local real-source manifest and test fixtures for malformed paths/provenance. Do not copy real source images/models into Git.
- No Kenya scans, factory captures, real physical measurement or physical acceptance are available. Synthetic inputs and public YCB samples test software behavior only; keep future Kenya validation separately pending.
- Do not modify upstream archive contents or infer unknown photo camera intrinsics, photo-to-mesh registration, physical dimensions or Kenya origin.

## Validation timing

- Verify downloaded archive sizes/hashes, safe bounded extraction, individual file hashes, JPEG/PLY structure, attribution/license metadata, and a standalone local-manifest integrity run.
- Add negative/boundary tests; defer pytest, Tester, lint/typecheck batches and consolidated independent/security reviews to M17 acceptance after PL-0395 or all M17 tasks have reached evidence-supported implemented/blocked state.
- Keep this task locally implemented but pending M17 acceptance until the milestone checks and consolidated audit support it. Never call the YCB corpus Kenya field evidence.

