# M16-C001 - ChatGPT Partial Audit V05

Date: 2026-10-06
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**

Independently accepted frontier: **PL-0347 V02 through PL-0349 V03**
Current child: **PL-0350 V03**
PL-0351 through PL-0367: **NOT_STARTED**
PL-0368: **DEFERRED_POST_M17**

## PL-0349 V03

Independent audit:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_V03.md

Decision: `AUDITED_PASS`.

The corrected hosted production stage at commit `9dccd1c00d2122f894b007b39ad33aef25b1ce42` independently proves:

- bounded Qt staged surface;
- real Qt GUI startup;
- real QtSvg + QtPdf technical-drawing PDF parse/render;
- OCP/CAD runtime and bounded CAD operation;
- Open3D 0.20.0 runtime and bounded geometry operation;
- no runtime network;
- exact capability-complete staging inventory.

The overall hosted job later fails only at PL-0350's separate redistribution-clearance gate.

## Owner-machine QtCore evidence

The owner supplied Windows evidence showing:

`ImportError: DLL load failed while importing QtCore: The specified procedure could not be found.`

That evidence was useful and directly influenced PL-0349 V03:

- staged Shiboken/native DLL directories are registered before importing the Studio app;
- unrelated build-environment ICU DLLs are excluded;
- the staged Qt surface is explicitly asserted;
- the corrected hosted frozen smoke passes.

However, the failing owner executable cannot be cryptographically tied to the exact `9dccd1c` stage because PL-0349 intentionally did not publish the uncleared binary bundle.

Therefore PL-0349 V03 remains PASS, but final user-machine/install portability is retained as a mandatory downstream gate rather than dismissed.

## PL-0351 amendment before first execution

PL-0351 prompt and criteria were strengthened before any PL-0351 implementation began.

It now requires:

- a **separate fresh Windows job**;
- download of the exact cleared PL-0350 installer artifact;
- hash/length verification before execution;
- silent isolated installation;
- launch of the **installed** application, not producer-job staging bits;
- sanitized runtime environment excluding checkout/venv/developer Qt/ICU/Shiboken paths;
- real installed Qt GUI/PDF/OCP/Open3D smoke;
- hard failure and diagnostic classification for `DLL load failed`, missing-procedure/entry-point, ICU, plugin, Shiboken or architecture errors;
- uninstall/cleanup even on failure.

This converts the owner-observed loader error into a permanent CI acceptance test.

Updated PL-0351 prompt:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md

Updated PL-0351 criteria:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_CRITERIA_V01.md

## Current continuation

PL-0350 V03 remains active against the exact PL-0349 V03 capability-complete stage.

No installer/public binary may advance unless PL-0350's exact file-level redistribution, license, notice and source-availability engineering gate closes.

If PL-0350 V03 becomes builder-green, the current R04 master may continue to PL-0351, which will read the amended V01 child prompt/criteria at execution time.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

Accepted frontier is PL-0349 V03. Resume at PL-0350 V03. PL-0351's future clean-artifact portability test is already hardened by the owner-machine QtCore evidence.
