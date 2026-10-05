# PL-0366 - ChatGPT Audit Criteria V01

Task: **Release checklist requiring Windows and iOS audits**

All criteria mandatory.

1. Checklist requires independent ChatGPT audit references for required M16 Windows/iOS gates.
2. Compliance, secrets and artifact provenance are mandatory.
3. Signed IPA requirement is conditional on release artifact intent, not faked when signing unavailable.
4. M17 acceptance is explicitly required before PL-0368.
5. Deferred physical limitations remain visible.
6. Missing/stale evidence fails closed.

7. No M17 implementation or PL-0368 release publication is pulled forward.
8. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0366_CODEX_PROMPT_V01.md
