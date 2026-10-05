# PL-0346 - ChatGPT Audit Criteria V01

Task: **Thumbnail and supplier contact-sheet export**

All criteria are mandatory.

1. Deterministic contact-sheet PNG and per-asset thumbnail evidence are produced locally.
2. Tiles include ID/name/supplier/volume/material/closure and provenance cues for estimates.
3. Thumbnail source priority is digest-valid local thumbnail, existing viewport preview, deterministic placeholder; no network.
4. Output image/layout ordering is deterministic for identical inputs.
5. Manifest binds exact asset revisions/output digest without ambient absolute destination identity.
6. Tests cover mixed thumbnail sources, estimate badges, selected/all export, empty set, output digest and path privacy.

7. Scope remains inside PL-0346 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0346_CODEX_PROMPT_V01.md
