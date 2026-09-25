# PL-0150 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0150 satisfies the frozen scope.
6. Implement a portability scanner that identifies external/non-project asset references, missing required files, absolute/private paths and non-portable links.
7. Classify findings as required-missing, external-but-present, regenerable cache/derived, and portable project-owned data.
8. Offer a report/plan only in M06; do not silently copy or rewrite external assets.
9. Ensure raw evidence/project metadata/history integrity is checked without leaking user absolute paths in portable report output.
10. Add tests for fully portable project, missing external asset, present external asset, symlink/path traversal, regenerable derived data and redacted report.
11. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
12. Performance/native/GPU claims are measured and limitations are stated truthfully.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
14. Dependency/lock/license changes are reproducible and compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
