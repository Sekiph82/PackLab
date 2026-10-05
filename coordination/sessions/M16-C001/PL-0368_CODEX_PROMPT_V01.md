# PL-0368 - Post-M17 Release Gate V01

Task: **Create first internal V0.1 release only after acceptance gates in M17 are satisfied**
Milestone: **M16 - CI/CD, Signing & Distribution**

## Status

`DEFERRED_POST_M17`

This task is intentionally NOT authorized for execution in M16-C001.

## Preconditions

PL-0368 may be activated only after:

1. M16 implementation children PL-0347 through PL-0367 have independent accepted audits;
2. M17 has run through its V1 acceptance gates;
3. required M17 acceptance tasks PL-0385 through PL-0395 have independent accepted evidence or an explicit owner-approved release exception recorded in TASKS;
4. Windows redistribution license/notice gate is closed;
5. release checklist PL-0366 validates all required Windows/iOS/security/provenance evidence;
6. release manifest/changelog are frozen for the intended release candidate;
7. root TASKS.md is explicitly advanced by ChatGPT to authorize PL-0368.

## Forbidden before activation

- no v0.1 tag;
- no GitHub Release;
- no release-ready installer/IPA publication claim;
- no rewriting M17 gates as passed;
- no Codex edit to TASKS.

If this prompt is invoked before activation, do not create a release. Publish only a truthful blocker log if specifically authorized to record the gate.
