# PL-0001-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0001 — Create canonical repository structure specification and ownership rules.**

These criteria are frozen for Codex prompt V01. ChatGPT will audit actual GitHub state against every numbered item after `CODEX_LOG_V01.md` arrives.

## A. Bootstrap synchronization evidence

1. Codex proves local workspace was `C:\Users\sekip\Desktop\PackLab`.
2. Codex verified Git repository identity before destructive alignment.
3. Codex verified `origin` resolves to `Sekiph82/PackLab` before destructive alignment.
4. `git fetch origin main --prune` was run.
5. First-sync alignment used only the prompt-authorized GitHub-authoritative commands or an equivalent that cannot preserve conflicting tracked local state.
6. `git clean -fdx` was **not** used.
7. Post-bootstrap local HEAD equaled `origin/main` before PL-0001 implementation began.
8. Post-bootstrap ahead/behind was `0 0` before implementation.
9. Post-bootstrap tracked/non-ignored working tree was clean before implementation.
10. Codex log records exact synchronization evidence rather than a bare "synced" claim.

## B. Required artifact

11. `docs/architecture/REPOSITORY_STRUCTURE.md` exists in the audited implementation commit.
12. PL-0001 does not physically create the full future `apps/core/schemas/assets/tests/tools` directory tree; that remains PL-0019.
13. Document identifies the planned monorepo areas: `apps/ios-capture`, `apps/windows-studio`, `core`, `schemas`, `assets`, `tests`, `tools`, `docs/architecture`, `coordination/sessions`.
14. Document identifies generated/runtime/private data classes that should remain local/untracked or explicitly controlled by later policy.

## C. Canonical authority ownership

15. Document states GitHub `main` is repository truth.
16. Document states root `TASKS.md` is the only live H!veAI/project-state tracker.
17. Document states ChatGPT owns prompts, criteria, independent audits and root TASKS lifecycle writes.
18. Document states Codex owns implementation/testing and matching `CODEX_LOG_VNN.md`, but not audit verdicts/TASKS lifecycle.
19. Document states session artifacts are work orders/evidence and do not override live TASKS state.
20. Document does not create a competing current-task/progress tracker.

## D. Application/layer ownership

21. PackLab Capture and PackLab Studio responsibilities are separated.
22. Python/domain core ownership is separated from PySide6 widget/UI ownership.
23. Swift PackLab-owned capture/domain interfaces are separated from NextLevel implementation details.
24. `.packscan` contract/schema ownership is identified as a cross-platform boundary.
25. COLMAP is described as the SfM/sparse reconstruction adapter boundary, not UI/business truth.
26. OpenMVS is described as dense reconstruction/mesh/refinement/texturing adapter boundary.
27. Open3D is described as point-cloud/mesh analysis/cleanup/measurement support boundary.
28. OpenCascade is described as engineering BREP/CAD boundary.
29. Blender is described as UV/material/render presentation boundary and not dimensional source of truth.

## E. Geometry/data ownership

30. Original capture / imported source evidence is identified as immutable or protected source data.
31. Reconstruction intermediates are identified as derived/regenerable where applicable.
32. Scan Master is explicitly distinct from raw reconstruction and Design Model.
33. Design Model is explicitly parameter-driven/editable and distinct from triangle Scan Mesh.
34. Engineering BREP/STEP derives from Design Model rather than being equated to scan mesh.
35. Artwork/material assignments are separated from engineering body geometry.
36. Private Kenya scans/confidential supplier assets are identified as local/private unless explicitly approved for public fixture use.
37. Safe public fixtures are distinguished from private production assets.

## F. Dependency direction

38. Domain/application logic does not depend on PySide6 widgets.
39. PackLab capture/domain contracts do not depend directly on NextLevel internals.
40. External engines are accessed through PackLab-owned adapters/capability boundaries.
41. Scan/reconstruction artifacts do not automatically become CAD truth.
42. Design Model may derive from Scan Master; Scan Master does not depend on Design Model.
43. Rendering may consume geometry/material/artwork data but may not become engineering source of truth.
44. Future structural changes require audited governance/ADR rather than silent ownership inversion.

## G. Scope control and governance

45. Codex did not edit root `TASKS.md`.
46. Codex did not edit ChatGPT prompt/criteria/audit artifacts.
47. Codex did not edit `AGENTS.md`, `CLAUDE.md`, `IMPLEMENTATION_GUIDE.md`, coordination policy/index, `handoff.md`, or root `AUDIT.md` during PL-0001 implementation.
48. Codex did not implement PL-0002+ work opportunistically.
49. No app/source implementation was added under the guise of documentation.
50. The document does not claim future folder/tooling tasks are completed.

## H. Validation and repository quality

51. `git diff --check` passes for the implementation/log diff.
52. `docs/architecture/REPOSITORY_STRUCTURE.md` is readable Markdown with no obvious broken internal path claims.
53. Document is specific enough to resolve ownership disputes, not merely a folder-name list.
54. No secrets, credentials, signing private material, personal tokens, private scans or confidential supplier content were committed.
55. Matching `coordination/sessions/PL-0001-C001/CODEX_LOG_V01.md` exists.
56. Log corresponds to `CODEX_PROMPT_V01.md` and this criteria V01.
57. Log records exact validation commands/results and any failures/fixes.
58. Log records final implementation commit and push evidence.
59. Codex handoff is `AWAITING_AUDIT` and does not self-assign PASS.
60. Actual GitHub diff is limited to the authorized PL-0001 artifact plus matching Codex log, excluding any owner/preexisting changes already present before the Codex implementation commit.

## Audit evidence rule

Codex evidence for items 1-10 and runtime Git commands is E1/E2 implementer evidence unless ChatGPT can independently verify the corresponding GitHub-side state. ChatGPT must say explicitly what it could not independently rerun.

A green `git diff --check` or a complete-looking log does not override a direct ownership/scope violation.

## Closure rule

ChatGPT may mark PL-0001 complete only when all mandatory criteria are satisfied and no material finding remains.

If any mandatory item fails:

- verdict is `CHANGES_REQUIRED` or `AUDITED_FAIL`;
- PL-0001 remains unchecked in root `TASKS.md`;
- ChatGPT updates H!veAI `## Project Status` accordingly;
- ChatGPT publishes `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md` with the frozen remediation set.
