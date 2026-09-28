coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
taskId: PL-0175
version: V01
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_PROMPT_V01.md
criteriaPath: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_CRITERIA_V01.md
codexLogPath: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V01.md
auditedBase: 19b784fef1bbdda972dafae10480d99d8448b278
implementationCommit: c29ef39703092672557852ec46279c042cd9aa39
auditedHead: 5090f0b8ba382ea792bff6b6324d68c70d5b2574
---

# PackLab ChatGPT Audit V01 - PL-0175

## Verdict

`CHANGES_REQUIRED`

The bounded dense-stage adapter is present and the implementation/log
publication boundaries are correct, but the semantic configuration boundary is
not fail-closed for all documented OpenMVS option domains. V02 must correct
that boundary and add public negative tests before PL-0175 can be accepted.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- V01 prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_PROMPT_V01.md
- V01 criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_CRITERIA_V01.md
- V01 Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V01.md
- Audited base: `19b784fef1bbdda972dafae10480d99d8448b278`
- Implementation commit: `c29ef39703092672557852ec46279c042cd9aa39`
- Log-only/audited head: `5090f0b8ba382ea792bff6b6324d68c70d5b2574`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/19b784fef1bbdda972dafae10480d99d8448b278...c29ef39703092672557852ec46279c042cd9aa39
- Full audited range: https://github.com/Sekiph82/PackLab/compare/19b784fef1bbdda972dafae10480d99d8448b278...5090f0b8ba382ea792bff6b6324d68c70d5b2574

## Evidence classification

### E1/E2 Codex evidence

The V01 log records the frozen scope, separate implementation and log commits,
required checks, unchanged repository-wide mypy debt, privacy review, remote
visibility, and `AWAITING_AUDIT`. Those claims remain builder evidence until
independently checked.

### E3 independent ChatGPT evidence

- Verified the canonical checkout, `main` branch, expected `origin`, clean
  status, `HEAD == origin/main`, remote SHA, and `0 0` divergence after
  `git fetch origin main --prune`.
- Inspected the live tracker, V01 prompt/criteria/log, actual commit ancestry,
  implementation/test diff, accepted conversion plan, process boundary,
  engine-probe boundary, and protected-file scope.
- Independently ran the focused PL-0175 plus predecessor boundary suites:
  `150 passed`.
- Independently ran the exact locked full suite:
  `567 passed, 5 skipped, 1 deselected, 2 warnings`. The skips are four
  unavailable `cv2` checks and one Windows symlink-privilege limitation;
  warnings are unchanged duplicate-ZIP fixture warnings.
- Independently inspected the pinned OpenMVS v2.4.0 `DensifyPointCloud`
  option declarations and compared their documented value domains with the
  PackLab configuration validator.
- Independently exercised the public configuration boundary. It accepts and
  maps `estimate_colors=3`, `estimate_normals=3`, `fusion_filter=3`, and
  `postprocess_dmaps=8`, although those values are outside the documented
  v2.4.0 domains.

### E4 owner evidence/decision

None required. This is a bounded software-contract correction.

## Criteria matrix

| # | Result | Independent disposition |
|---:|---|---|
| 1 | PASS | The live tracker authorized M07-C001 / PL-0175 / `READY` / `CODEX` before implementation; PL-0174 remained `AUDITED_PASS` and PL-0176+ remained unauthorized. |
| 2 | PASS | The implementation diff contains only `dense_reconstruction.py` and its public test; the separate log is the only evidence artifact. Protected accepted files and tracker were unchanged by Codex. |
| 3 | PASS | The immutable request is derived from one accepted conversion plan and retains safe asset IDs, source revision/digest, plan/configuration digests, OpenMVS `2.4.0`, reconstruction authority, and non-verified scale. |
| 4 | CHANGES_REQUIRED | Probe matching, no discovery/installation, the existing process boundary, and the semantic mapping exist, but the semantic validator permits documented-invalid option values to cross the adapter. |
| 5 | CHANGES_REQUIRED | Complete argv and unsafe-path/key rejection are covered, but invalid semantic option domains are not rejected. |
| 6 | PASS | Execution delegates to `run_reconstruction_stage`; the inspected boundary is shell-free with bounded/redacted evidence and timeout/cancellation propagation. |
| 7 | PASS | Success/failure/cancellation normalization, output suppression on non-success, stage identity, and provenance behavior are present and covered. |
| 8 | PASS | Results remain `RECONSTRUCTION_OBSERVATION` with only relative or metric-unverified scale and explicit non-authority limitations. |
| 9 | CHANGES_REQUIRED | Public tests are sensitive for paths, probes, execution, output, provenance, and predecessor regressions, but omit the invalid documented option-domain cases identified above. |
| 10 | PASS | The exact locked full suite exits 0; environment skips/warnings and the absent OpenMVS executable are truthfully disclosed. |
| 11 | PASS | The inspected diff has no tracker, lock, schema, generated, binary, secret, private-scan, or later-stage changes; builder evidence reports the required lint/type/compile checks. |
| 12 | PASS | The V01 log uses full URLs, records separate publication boundaries, and ends exactly `AWAITING_AUDIT`. |
| 13 | PASS | No mesh/refinement/texture, output-preservation, orchestration, discovery/installation, tracker/audit edit, or PL-0176+ implementation was found. |

## Finding F1 - semantic OpenMVS option domains are not fail-closed

The V01 implementation validates all integer options only as non-negative
integers in `core/src/packlab_core/dense_reconstruction.py:80-96` and
`:137-148`. The public boundary therefore accepts and emits values that the
pinned OpenMVS source documents as outside the option domains:

- `estimate_colors` and `estimate_normals` document `0` disabled, `1` final,
  or `2` estimate;
- `fusion_filter` documents `0`, `1`, or `2`; and
- `postprocess-dmaps` documents the flags `0`, `1`, `2`, and `4`, so values
  containing unsupported bits such as `8` are not valid PackLab semantic
  settings.

The upstream declarations are at:
https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/DensifyPointCloud/DensifyPointCloud.cpp

Independent reproduction through `DensePointCloudConfig.from_overrides`
reported `ACCEPTED` for `estimate_colors=3`, `estimate_normals=3`,
`fusion_filter=3`, and `postprocess_dmaps=8`. This violates criteria 4, 5,
and 9: a PackLab-owned semantic boundary must reject unsupported values
before constructing the exact argv. The current test
`test_command_mapping_is_complete_and_matches_pinned_densifier_options`
covers valid values only and would remain green with this defect.

## Required remediation

V02 is bounded to the configuration validator, public negative/boundary tests,
and the matching V02 log. Preserve the accepted request/result/process
architecture and all valid V01 argv behavior. Reject unsupported bits in the
documented domains through the public configuration boundary, and record the
exact rerun results and final handoff.

## TASKS.md action

PL-0175 remains unchecked. ChatGPT changes the live state to `CHANGES_REQUIRED`,
publishes the V02 remediation prompt and criteria, and keeps PL-0176 and later
unauthorized. Required Actor remains `CODEX`.

## Final conclusion

PL-0175 V01 is not independently accepted. The implementation is a bounded
partial pass, but the semantic configuration option-domain finding must be
closed by PL-0175 V02 before an `AUDITED_PASS` decision.
