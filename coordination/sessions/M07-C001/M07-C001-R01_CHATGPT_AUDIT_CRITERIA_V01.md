# M07-C001-R01 — ChatGPT Remediation Audit Criteria V01

Scope: **PL-0160, PL-0161**

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/CHATGPT_AUDIT_V01.md

All criteria are mandatory.

1. Root `TASKS.md` authorizes M07-C001-R01 / CHANGES_REQUIRED / CODEX before material work.
2. Accepted PL-0158, PL-0159 and PL-0162 through PL-0165 remain unregressed.
3. PL-0135 through PL-0157 remain accepted and unregressed.
4. PL-0068 remains OWNER_REQUIRED.
5. Codex does not edit root `TASKS.md`, ChatGPT audits or ChatGPT criteria.
6. Do not start PL-0166 or any later task.
7. Preserve the exact selected baselines:
   - COLMAP 3.12.6
   - OpenMVS 2.4.0
8. The production COLMAP probe uses a command actually supported by the exact 3.12.6 CLI and does not use the unsupported `--version` command.
9. The production OpenMVS probe uses a command/mode actually supported by the exact 2.4.0 applications and does not use the unsupported `--version` option.
10. Exit-code acceptance is engine/probe-policy specific. Do not globally treat arbitrary non-zero exits as valid.
11. COLMAP probe must distinguish missing, unexecutable, invalid/unparseable, unsupported-version and valid-baseline states.
12. OpenMVS probe must distinguish missing, unexecutable, invalid/unparseable, unsupported-version and valid-baseline states even though the supported help/no-input probe mode may have an expected non-zero application exit.
13. A valid OpenMVS result requires both:
    - a recognized OpenMVS version banner; and
    - an exit code permitted by the explicit OpenMVS probe policy.
14. Non-zero OpenMVS execution without a valid banner must not become valid.
15. Tests must be command-sensitive: injected runners assert the exact argv/probe mode used.
16. Add one upstream-semantic fixture representing actual COLMAP help behavior.
17. Add one upstream-semantic fixture representing actual OpenMVS 2.4.0 help/no-input behavior.
18. Add a deterministic OpenMVS component-suite capability report covering:
    - InterfaceCOLMAP
    - DensifyPointCloud
    - ReconstructMesh
    - RefineMesh
    - TextureMesh
19. The component-suite report identifies each component separately and proves at least:
    - all-valid suite;
    - one missing component;
    - one unsupported-version component;
    - one unexecutable/invalid component.
20. Component-suite behavior reuses the same PackLab-owned probe parser/policy and does not launch reconstruction work.
21. No automatic download, install, PATH-wide arbitrary scan or shell execution is introduced.
22. Focused remediation tests exit 0.
23. Exact full locked suite exits 0.
24. Ruff, targeted mypy, compileall, project/static checks and `git diff --check` pass truthfully.
25. Known unrelated repository-wide mypy debt may be reported, but no changed module may add an error.
26. Dependency/lock, protected-file, secrets/privacy, signing-material and generated/binary reviews pass.
27. Publish a separate remediation log:
    https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V01.md
28. The remediation log uses full GitHub URLs and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Closure requires independent ChatGPT audit. Do not self-audit.
