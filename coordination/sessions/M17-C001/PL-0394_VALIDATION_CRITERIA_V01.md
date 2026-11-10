# PL-0394 — Validation Criteria V01

1. Audit exact public `origin/main` and identify the precise revision reviewed.
2. Separately review local M17 source changes that are not yet public; do not claim they are part of the public audit.
3. Inspect credentials/protected files, local-data exclusion, archive/path safety, third-party licenses/attribution, source hashes, synthetic/physical authority boundaries, and CI trigger/publication risks.
4. Run an approved local secret/dependency scan only if it is offline/free and does not expose secret values; record tool/version/scope/result.
5. A named independent security reviewer inspects the actual source diff and returns findings; Codex must not author the review verdict.
6. No Actions, billing, secret disclosure, or public release. Preserve unresolved findings.
