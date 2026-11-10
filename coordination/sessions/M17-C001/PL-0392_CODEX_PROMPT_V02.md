# PL-0392 — Codex Prompt V02

Task: **Demonstrate synthetic SKU geometry reuse without implying Kenya inventory**  
Milestone: **M17** · Cycle: **M17-C001**

V02 closes an independent security-review ambiguity: the original disposable test reused `_asset()` defaults named `kenya-pack-001`, ACTIVE and supplier-declared. Even in a test, those values could be mistaken for actual factory inventory.

## Scope

- Keep the regression entirely in memory with synthetic fixture IDs and labels explicitly saying the asset is a test fixture, not Kenya inventory.
- Remove the sample supplier identity, set package status to UNKNOWN, use synthetic/test-only POVU SKU IDs/display names with DRAFT status, and assert these test-only identity/authority markers.
- Preserve the core requirement: two distinct POVU SKU revisions pin the same immutable geometry revision while retaining distinct artwork references and no copied geometry.
- Do not change real inventory, supplier files or datasets. Do not execute task tests; retain them for the consolidated M17 checkpoint.

Write `PL-0392_CODEX_LOG_V02.md` after independent source/security review. Keep the task incomplete until grouped test evidence is recorded.
