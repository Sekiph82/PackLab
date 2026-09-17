# PL-0005-C001 — ChatGPT Strict Audit Criteria V02

Task: **PL-0005 — dependency/license register remediation**

These criteria are frozen for Codex prompt V02.

## A. Authorization and exact synchronization

1. Root `TASKS.md` shows PL-0005 as current and `CHANGES_REQUIRED` before material V02 work.
2. Codex verifies Git root is `C:\Users\sekip\Desktop\PackLab`.
3. Codex verifies origin resolves to `Sekiph82/PackLab`.
4. Codex records `git status --porcelain` before material V02 work.
5. Codex runs `git fetch origin main --prune` before material V02 work.
6. Codex runs and records `git rev-list --left-right --count HEAD...origin/main` before any merge.
7. If tracked local changes exist, Codex stops.
8. If local is ahead or diverged, Codex stops.
9. If local is only behind, synchronization uses only `git merge --ff-only origin/main`.
10. No reset, rebase, force-push, destructive checkout, silent stash, or `git clean` is used.
11. Before material V02 validation, local HEAD equals `origin/main`.
12. Before material V02 validation, ahead/behind equals `0 0`.

## B. V01 artifact preservation

13. `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` still exists.
14. It is not rewritten merely to manufacture a new implementation diff.
15. If changed, the V02 log identifies a newly discovered factual defect and exact correction.
16. No dependency is installed, pinned, vendored, bundled, linked, modified, or distribution-cleared by V02.
17. Python OpenCascade binding remains `TBD / NOT SELECTED` unless an owner-authorized later task changes it.
18. PL-0289 remains the binding-selection owner.
19. OpenMVS remains identified as AGPL-3.0 / HIGH LICENSE ATTENTION.
20. COLMAP third-party licensing caveat remains present.
21. OpenCV version-sensitive licensing remains present.
22. PyTorch main-project/package/transitive distinction remains present.
23. OCCT license and Python binding license remain separate.
24. Blender software/output distinction remains present.
25. PySide6/Qt multi-route/module-sensitive licensing remains present.
26. The register still avoids unsupported legal conclusions.

## C. Scope protection

27. Root `TASKS.md` is not modified by Codex.
28. `AGENTS.md`, `CLAUDE.md`, and `IMPLEMENTATION_GUIDE.md` are not modified by Codex.
29. Prior V01 prompt/criteria/log/audit artifacts are not modified.
30. No application/source/schema/runtime file is modified.
31. No PL-0006+ work is implemented.
32. Historical local `.hiveai/` state is not staged or committed.
33. If no new register defect exists, the only V02 tracked addition is `CODEX_LOG_V02.md`.

## D. Validation and evidence

34. `git diff --check` is recorded and passes.
35. Register revalidation explicitly checks all material license distinctions listed in the V02 prompt.
36. Protected-scope validation is recorded.
37. Codex records exact synchronization commands, expected safety behavior, and actual results.
38. Codex records whether a merge was needed.
39. Codex records final HEAD and `origin/main` equality before validation.
40. Codex records final ahead/behind `0 0` before validation.
41. `CODEX_LOG_V02.md` exists.
42. The log points to `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md`.
43. The log does not predeclare the future log-containing commit SHA.
44. Codex safely commits/pushes only authorized V02 changes.
45. Remote visibility is recorded after push.
46. Handoff is exactly `AWAITING_AUDIT`; Codex does not self-assign PASS.
47. No secrets, credentials, signing material, private scans, supplier-confidential content, or proprietary production artwork are committed.

## Closure rule

All 47 mandatory V02 criteria must pass.

If all pass and no new substantive defect is found, ChatGPT may close PL-0005 based on the already accepted V01 register plus corrected V02 process evidence.

If any fail, PL-0005 remains unchecked and another remediation version is required.
