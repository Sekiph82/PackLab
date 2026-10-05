# PL-0337 - ChatGPT Audit Criteria V01

Task: **Supplier drawings, quotations and notes attachments**

All criteria are mandatory.

1. Explicit/injected library root and content-addressed local attachment storage exist.
2. Canonical records use safe relative paths, digest/length and role metadata; original absolute paths are absent.
3. Attachments are opaque bytes; no document execution/network fetch or hidden parsing pipeline.
4. Symlink/traversal/tampered/oversized inputs fail closed; writes are atomic.
5. Asset/component/SKU linkage is exact and optional; stale references reject where required.
6. Tests cover duplicate-content deduplication, digest mismatch, unsafe paths and no-Git/ambient-path identity.

7. Scope remains inside PL-0337 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0337_CODEX_PROMPT_V01.md
