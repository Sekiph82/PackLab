# PL-0347 - ChatGPT Audit Criteria V02

Task: **Configured-source mypy remediation + real hosted Windows quality PASS**

All criteria are mandatory.

1. Live TASKS authorization and M16 partial audit V01 are read; root TASKS is not edited by Codex.
2. Existing production workflow remains least-privilege and retains the hard command `uv run --locked mypy core apps tools`.
3. Final configured-source mypy result is **zero errors** locally and on a fresh real hosted Windows Actions run.
4. No `# type: ignore`, mypy exclude/baseline/error-code disable, scope narrowing, soft-fail or unchecked Any-cast is introduced to hide debt.
5. Dynamic/JSON parsing fixes use explicit runtime validation/typed helpers and preserve existing fail-closed behavior.
6. Optional Design Model/Scan Master authority values are handled truthfully; missing authority is never replaced by a fabricated identifier and captured/standalone provenance semantics are preserved.
7. Engineering export Scan Master vs Design Model branches are statically distinct without changing export authority/format behavior.
8. Packaging Library parsing validates exact field types before domain construction and malformed state still fails closed.
9. Focused tests cover each behaviorally touched seam; Ruff/format, compile, locked full pytest and dependency/scope/privacy checks pass.
10. Fresh hosted Windows run passes lock validation/install, Ruff lint, changed-file format, mypy and pytest. Hosted run URL/ID and exact final test count are recorded.
11. Scope is limited to the 12 blocker files plus directly required tests/helpers and the PL-0347 workflow/test seam if necessary; PL-0348+ and M17+ are not implemented.
12. Implementation/evidence and V02 log publication are distinct; V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0347_CODEX_PROMPT_V02.md
