# PL-0425 Codex Prompt V01 — Bluetooth Turntable Capability Gate

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; inspect local feasibility before any actuator implementation.

## Objective

Determine whether the current PackLab Windows environment exposes a present, identifiable Bluetooth turntable target and record the safe boundary for a later protocol adapter.

## Allowed scope

- Read-only local device inventory that does not enumerate or log owner device identifiers unnecessarily.
- Write this prompt, matching criteria/log and local task metadata. Update `TASKS.md` to record exact blocked state and next dependency-ready task.

## Hard constraints

- Do not pair, connect, send commands, move, calibrate or otherwise actuate any device.
- Do not infer compatibility or safety controls from generic Bluetooth availability.
- No device credentials, owner personal-device inventory, network capture or vendor software download.
- Zero Actions/paid CI, no PR, no source push to `main`, no native builds and no release claim.

## Validation and handoff

Record the exact read-only inventory command/result and whether an exact compatible target is present. If absent, preserve PL-0425/PL-0426 as blocked and continue only with a task that can be completed without hardware actuation.
