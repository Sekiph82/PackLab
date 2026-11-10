# PL-0429 Codex Prompt V01 — Remote iPhone Capture Capability Gate

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; inspect local readiness without discovering LAN peers or connecting to devices.

## Objective

Determine whether this Windows workspace has an exact identified iPhone capture target and supported local capability for a future trusted-LAN control contract.

## Allowed scope

- Read-only local PnP/service inventory, summarized without saving unrelated device identifiers.
- Write matching prompt, criteria, blocker log and local task metadata; update root `TASKS.md` for the blocked gate and next dependency-ready task.

## Hard constraints

- Do not scan LAN, connect/pair, send capture commands, access camera/photos or change firewall/trust settings.
- Do not log IP addresses, device IDs, credentials, keys, owner network details or unrelated device names.
- Do not install mobile/Apple tooling or download vendor software.
- Zero Actions/paid CI, no PR, no source push to `main`, no native build or release claim.

## Validation and handoff

Record the exact read-only commands and privacy-minimized result. If no exact usable iPhone target and trusted endpoint are evidenced, mark PL-0429 blocked and continue only with independent local tasks.
