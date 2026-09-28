# PL-0184 - ChatGPT Audit Criteria V01

Task: **Define replaceable segmentation backend and mask/provenance contracts**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. The live tracker authorized the complete M08-C001 batch and this exact child frontier before implementation; predecessor evidence and mandatory pre-reads were present.
2. The implementation is PackLab-owned, deterministic, provenance-bound and limited to the frozen scope: Create PackLab-owned, model-neutral SegmentationBackend, capability report, request/result, MaskArtifact, MaskSetRevision and PromptEvidence contracts. Record source image identity/digest, dimensions, top-left origin and pixel convention, resize/transform metadata, backend/model/checkpoint/runtime provenance, prompt kind/data, confidence, post-processing version, timestamp and manual ancestry. Keep RAW_CAPTURE immutable and place masks in governed working/derived storage. Prove fake-backend substitution, coordinate round-trip, resized-input mapping and provenance separation.
3. Required negative, boundary, failure and regression behavior is tested through the public boundary: Test fake backend replacement, coordinate metadata, transform mapping, source-byte immutability, model/checkpoint provenance, and revision-shaped serialization.
4. RAW_CAPTURE/source bytes, prior accepted authority contracts, revision identity and workspace/provenance boundaries remain intact.
5. No unreviewed model/runtime/dependency, private data, generated unsafe output, UI-owned domain truth, native/physical claim or later-child/later-milestone scope is included.
6. Required focused/full/static/security/scope/remote checks and the child log are complete and truthful; the log ends exactly with READY_FOR_INDEPENDENT_AUDIT.

Audit must independently inspect the actual GitHub diff/source and evidence. Builder validation is not acceptance. A failed or blocked child stops the M08-C001 frontier.
