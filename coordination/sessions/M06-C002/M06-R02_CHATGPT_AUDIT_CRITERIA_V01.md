# M06-R02 — ChatGPT Remediation Audit Criteria V01

Scope: **PL-0150, PL-0151, PL-0157**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/CHATGPT_AUDIT_V01.md

All criteria are mandatory.

1. Root `TASKS.md` authorizes `M06-R02 / CHANGES_REQUIRED / CODEX` before material work.
2. PL-0135 through PL-0149 remain accepted and unregressed.
3. PL-0152 through PL-0156 remain accepted and unregressed.
4. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
5. Codex does not edit root `TASKS.md`, ChatGPT audit files or ChatGPT criteria files.
6. No new M07/M09/later-milestone implementation is introduced.
7. PL-0150 adds real filesystem symlink coverage in addition to traversal-string coverage. An escaping symlink must be classified unsafe. A safe in-project path/link case must remain portable where supported. Windows privilege/policy limitations may skip only the actual symlink-creation test with an explicit capability reason; traversal coverage must still run.
8. PL-0150 remains read-only: no external asset copying/rewriting and no raw mutation. Portable output remains redacted.
9. PL-0151 compares at least two genuinely executable or meaningfully testable PySide6-compatible viewport approaches on the available host.
10. PL-0151 executes representative synthetic point and triangle/mesh workloads for every candidate that can actually render them. An unavailable native/OpenGL path may be retained as a capability probe, but it cannot count as the sole second measured candidate if no comparable geometry workload executes.
11. PL-0151 records comparable startup/initialization, geometry setup/load, render or interaction proxy, memory observation, dependency footprint/weight, licensing, Windows/Python/PySide6 compatibility, headless/native/GPU capability and limitations.
12. If a candidate cannot execute on the host, its metrics are marked unavailable rather than fabricated.
13. The PL-0151 ADR/evidence is updated so the selected backend and rationale match the new measured comparison. Any new selected dependency must be declared/locked/license-reviewed before use.
14. PL-0157 benchmark evidence includes representative synthetic **point-cloud and mesh** cases at multiple sizes.
15. PL-0157 mesh and point cases record source/display primitive counts, deterministic LOD plan, initialization/setup time, display-representation time, render/interaction proxy, memory observation and backend/runtime metadata.
16. PL-0157 LOD affects display representations only and never overwrites authoritative source geometry.
17. Performance/native/GPU claims remain limited to actually executed evidence.
18. Focused remediation tests pass.
19. Exact full locked suite exits 0.
20. Ruff, targeted/relevant mypy for changed modules, compileall, project/static checks and `git diff --check` pass truthfully.
21. Existing unrelated repository-wide mypy debt may be reported, but no new errors may be introduced in changed modules.
22. Dependency/lock/license, protected-file, secrets/privacy, signing-material and generated/binary reviews pass.
23. Publish a separate:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CODEX_LOG_V01.md
with exact changed files, focused/full test results, benchmark/spike evidence, commit SHAs and residual limitations.
24. The R02 log uses full GitHub URLs and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Closure requires independent ChatGPT `AUDITED_PASS`. Do not self-audit.
