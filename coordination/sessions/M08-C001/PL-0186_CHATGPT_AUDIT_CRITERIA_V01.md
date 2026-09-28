# PL-0186 - ChatGPT Audit Criteria V01

Task: **Implement the selected license-cleared local PyTorch segmentation backend**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. The live tracker authorized the complete M08-C001 batch and this exact child frontier before implementation; predecessor evidence and mandatory pre-reads were present.
2. The implementation is PackLab-owned, deterministic, provenance-bound and limited to the frozen scope: Implement one explicitly selected and license-cleared local backend behind the PL-0184 contract, or stop with a truthful unavailable/license blocker if PL-0185 did not establish a safe selection. Probe capabilities rather than assuming them, normalize coordinates to source pixels, preserve model/checkpoint/runtime provenance, bound outputs and fail closed on missing runtime/model/checkpoint.
3. Required negative, boundary, failure and regression behavior is tested through the public boundary: Test capability available/unavailable behavior, fake/local runner boundary, supported prompt modes, coordinate transforms, malformed output rejection, provenance digests, source preservation and no-install behavior.
4. RAW_CAPTURE/source bytes, prior accepted authority contracts, revision identity and workspace/provenance boundaries remain intact.
5. No unreviewed model/runtime/dependency, private data, generated unsafe output, UI-owned domain truth, native/physical claim or later-child/later-milestone scope is included.
6. Required focused/full/static/security/scope/remote checks and the child log are complete and truthful; the log ends exactly with READY_FOR_INDEPENDENT_AUDIT.

Audit must independently inspect the actual GitHub diff/source and evidence. Builder validation is not acceptance. A failed or blocked child stops the M08-C001 frontier.
