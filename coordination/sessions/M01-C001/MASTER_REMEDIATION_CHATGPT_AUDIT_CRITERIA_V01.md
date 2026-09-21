# M01-C001 — Master Remediation ChatGPT Audit Criteria V01

Repository: https://github.com/Sekiph82/PackLab

All criteria are mandatory.

1. Root TASKS.md authorized M01-REMEDIATION-BATCH-001 / CODEX.
2. Exactly the eleven remediation tasks from MASTER_CHATGPT_AUDIT_V01 were executed.
3. Remediation order respected the dependency-safe master order.
4. Codex did not edit TASKS.md or create ChatGPT audits.
5. No M02 work was started.
6. No destructive Git operation or unsafe divergence was used.
7. Every remediation child has a separate V02 prompt, frozen V02 criteria, implementation/evidence boundary and V02 Codex log.
8. PL-0024 independently passes V02.
9. PL-0025 independently passes V02.
10. PL-0026 independently passes V02.
11. PL-0030 independently passes V02.
12. PL-0031 independently passes V02.
13. PL-0034 independently passes V02.
14. PL-0035 independently passes V02.
15. PL-0037 independently passes V02.
16. PL-0041 independently passes V02.
17. PL-0043 independently passes V02.
18. PL-0036 independently passes V02 current-state revalidation.
19. Accepted sibling tasks PL-0019/20/21/22/23/27/28/29/32/33/38/39/40/42 remain unregressed.
20. Final task runner uses the locked uv toolchain coherently for bootstrap/test/lint/type-check.
21. Final pytest marker validation rejects unknown markers.
22. Final Windows cache/data ownership keeps durable data outside the cache root.
23. Final diagnostics/capability model separates generic GPU/driver evidence from actual CUDA truth.
24. Final subprocess runner owns/cleans descendant processes safely on Windows.
25. Final Xcode graph links NextLevel product into the app target Frameworks phase.
26. Final iOS diagnostics privacy defaults sanitize retained/exported strings.
27. Final hosted XCTest graph has coherent testability/BUNDLE_LOADER/TEST_HOST wiring.
28. Final PackLabCapture plist/project baseline is internally coherent.
29. No secret/private/confidential/signing/cached artifact entered public Git.
30. MASTER_REMEDIATION_CODEX_LOG_V01.md exists, indexes all children accurately and ends REMEDIATION_BATCH_COMPLETED / AWAITING_MILESTONE_AUDIT.
31. Actual GitHub diffs/commits/logs match all remediation claims.
32. M01 has no remaining material defect within its frozen scope.

## Closure

ChatGPT must audit each V02 remediation child separately, persist each V02 ChatGPT audit to GitHub before moving to the next, then perform the final M01 milestone re-audit. M01 closes only if all mandatory criteria pass.
