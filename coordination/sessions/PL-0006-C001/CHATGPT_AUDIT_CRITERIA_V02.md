# PL-0006-C001 — ChatGPT Strict Audit Criteria V02

Task: **PL-0006 — semantic versioning policy remediation**

These criteria are frozen for Codex prompt V02.

## A. Authorization and exact synchronization

1. Root `TASKS.md` shows PL-0006 as current and `CHANGES_REQUIRED` before material V02 work.
2. Git root is `C:\Users\sekip\Desktop\PackLab`.
3. `origin` resolves to `Sekiph82/PackLab`.
4. `git status --porcelain` is recorded before material V02 work.
5. `git fetch origin main --prune` runs before material V02 work.
6. Explicit ahead/behind is recorded with `git rev-list --left-right --count HEAD...origin/main` before any merge.
7. Tracked local changes cause STOP.
8. Ahead/diverged local state causes STOP.
9. Behind-only state uses only `git merge --ff-only origin/main`.
10. No reset, rebase, force-push, destructive checkout, silent stash, or `git clean` is used.
11. Local HEAD equals `origin/main` before material V02 validation.
12. Ahead/behind equals `0 0` before material V02 validation.
13. Historical `.hiveai/` is not staged or committed.

## B. V01 policy preservation and revalidation

14. `docs/architecture/VERSIONING_POLICY.md` still exists.
15. It is not rewritten merely to manufacture a new implementation diff.
16. If changed, the V02 log identifies a genuine newly discovered defect and exact correction.
17. Three independent version domains remain defined: StudioVersion, CaptureVersion, PackScanSchemaVersion.
18. The domains remain related but not numerically locked.
19. Studio/Capture MAJOR/MINOR/PATCH semantics remain intact.
20. PackScan schema MAJOR/MINOR/PATCH semantics remain intact.
21. Compatibility matrix requirements remain intact.
22. Reader behavior constraints remain intact.
23. Writer behavior constraints remain intact.
24. Migration remains explicit, versioned, non-destructive, failure-safe, and source/target identified.
25. Future application/schema compatibility declarations remain intact.
26. Git SHA remains provenance rather than semantic version.
27. Original `.packscan` immutability remains intact.
28. Millimetres remain canonical engineering units unless changed by later audited ADR.
29. Coordinate-system semantics remain explicit.
30. Scan Mesh / Scan Master / Design Model separation remains intact.
31. Policy remains not a second project-status tracker.

## C. Scope protection

32. Root `TASKS.md` is not modified by Codex.
33. `AGENTS.md`, `CLAUDE.md`, and `IMPLEMENTATION_GUIDE.md` are not modified by Codex.
34. Prior V01 prompt/criteria/log/audit artifacts are not modified.
35. No application/source/schema/runtime implementation is added.
36. No tag, GitHub release, workflow, release manifest, app version file, schema implementation file, package manifest, lockfile, or executable release tooling is created.
37. No PL-0007+ work is implemented.
38. Historical local `.hiveai/` state is not staged or committed.
39. If no new policy defect exists, the only V02 tracked addition is `CODEX_LOG_V02.md`.

## D. Validation and evidence

40. `git diff --check` is recorded and passes.
41. Policy revalidation explicitly checks all material domains and compatibility boundaries listed in the V02 prompt.
42. Protected-scope validation is recorded.
43. Codex records exact synchronization commands and raw results.
44. Codex records whether a merge was required.
45. Codex records final HEAD and `origin/main` equality before material V02 validation.
46. Codex records final ahead/behind `0 0` before material V02 validation.
47. `CODEX_LOG_V02.md` exists.
48. The log points to `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md`.
49. The log does not predeclare the future log-containing commit SHA.
50. Codex safely commits/pushes only authorized V02 changes.
51. Remote visibility is recorded after push.
52. Handoff is `AWAITING_AUDIT`; Codex does not self-assign PASS.
53. No secrets, credentials, signing material, private scans, confidential supplier content, or proprietary production artwork are committed.

## Closure rule

All **53 mandatory V02 criteria** must pass.

If all pass and no new substantive defect is found, ChatGPT may close PL-0006 based on the substantively accepted V01 policy plus corrected V02 synchronization evidence.

If any criterion fails, PL-0006 remains unchecked and another remediation version is required.
