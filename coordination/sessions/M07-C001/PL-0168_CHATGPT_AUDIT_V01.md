---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
version: V01
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: coordination/sessions/M07-C001/PL-0168_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_CRITERIA_V01.md
codexLogPath: coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V01.md
auditedBase: fbf72cfacb830a2f580fa14050e3cd9d04f85e22
auditedHead: 5443b5865aeaf6bc60cad8be05b41eb68bff1982
---

# PackLab ChatGPT Independent Audit V01 - PL-0168

## Verdict

`CHANGES_REQUIRED`

The PackLab-owned feature-extraction boundary is substantially implemented and
the required runtime/static gates independently pass. One deterministic
canonicalization defect remains: two supported threshold aliases can target the
same normalized field, and the last mapping entry wins. Equal mappings with
the same key/value pairs can therefore produce different configurations and
digests depending on insertion order. PL-0168 remains open; PL-0169 is not
authorized.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_CRITERIA_V01.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V01.md
- Authorization/base commit: `fbf72cfacb830a2f580fa14050e3cd9d04f85e22`
- Implementation commit: `2cfdfab7dd15f8b21e472d0296f18c7ab40ed53e`
- Audited remote head / log-only commit: `5443b5865aeaf6bc60cad8be05b41eb68bff1982`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/fbf72cfacb830a2f580fa14050e3cd9d04f85e22...2cfdfab7dd15f8b21e472d0296f18c7ab40ed53e
- Full audited range: https://github.com/Sekiph82/PackLab/compare/fbf72cfacb830a2f580fa14050e3cd9d04f85e22...5443b5865aeaf6bc60cad8be05b41eb68bff1982

## Evidence classification

### E1/E2 Codex evidence

- The matching log records the required prompt/criteria, implementation SHA,
  separate log-only publication, exact commands, limitations, and the final
  `READY_FOR_INDEPENDENT_AUDIT` marker.
- The log reports 16 focused tests, 50 reconstruction/engine-boundary tests,
  and `357 passed, 5 skipped, 1 deselected, 2 warnings` for the locked suite.

### E3 independent ChatGPT evidence

- Verified the canonical root, `main` branch, origin URL, clean status, safe
  fetch, divergence `0 0`, `HEAD == origin/main`, and
  `git ls-remote origin refs/heads/main == 5443b5865aeaf6bc60cad8be05b41eb68bff1982`.
- Inspected the actual implementation, test, and log commits. The published
  range contains only the two authorized product files and the required log;
  no tracker, audit artifact, dependency/lock file, binary, generated output,
  private scan, supplier material, or signing material was included.
- Independently reran the focused suite (`16 passed`), relevant boundary suite
  (`50 passed`), Ruff, targeted mypy, compileall, diff-check, and the locked
  full suite (`357 passed, 5 skipped, 1 deselected, 2 warnings`).
- Independently ran the repository-wide mypy check: the same 18 errors remain
  in five unchanged files; `feature_extraction.py` has no mypy error.
- Independently exercised the public override boundary with equal mappings in
  different insertion orders.

### E4 owner evidence/decision

- None required for this software-boundary correction. Native Apple/device,
  physical, clean-machine, and external-engine execution evidence remains
  outside this task and is not claimed.

## Criteria matrix

| # | Result | Evidence / finding |
|---:|---|---|
| 1 | PASS | The live tracker authorized M07-C001 / `READY` / `CODEX` for PL-0168 before implementation. PL-0158 through PL-0167 are accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0169+ remains unauthorized. |
| 2 | PASS | `FeatureExtractionConfig` is a frozen, slot-based PackLab-owned boundary with backend-neutral normalized fields. No UI, tracker, PackScan, RAW_CAPTURE, camera-prior, or future-task authority was changed. |
| 3 | PASS | The immutable `packaged-consumer-goods-v1:1` preset exposes deterministic image-size, feature-count, octave, threshold, edge, and orientation defaults with explicit tradeoff notes and a non-benchmark limitation. |
| 4 | FAIL | Normal unknown/unsupported, absolute-path, non-finite, range, and mutation checks pass, but supported aliases `peak_threshold` and `contrast_threshold` can both normalize to `contrast_peak_threshold` and overwrite one another by insertion order. This is not a deterministic fail-closed override contract. |
| 5 | FAIL | Canonical JSON sorting makes distinct normalized configurations stable, but equivalent mappings are not always order-independent. With `a={'peak_threshold': 0.006, 'contrast_threshold': 0.007}` and the same pairs inserted in reverse order, `a == b` is true while the resulting thresholds are `0.007` and `0.006` and both serialization and SHA-256 digest differ. |
| 6 | PASS | The adapter emits the expected COLMAP 3.12.6 `Feature/SiftExtraction` names and values, rejects other engine versions, lists unsupported options, and contains no process/install/discovery path. |
| 7 | FAIL | The focused tests cover ordinary aliases, order independence for distinct fields, invalid values, paths, immutability, and mapping, but do not cover conflicting aliases targeting one canonical field. The missing sensitivity allowed the defect through. |
| 8 | PASS | The exact locked full suite independently exited 0; the five OpenCV/symlink capability skips and two existing duplicate-ZIP warnings were reported truthfully. |
| 9 | PASS | Ruff, targeted mypy, compileall, diff-check, changed-file/protected-file review, dependency/lock review, privacy/secrets review, and generated/binary review passed. The unchanged repository-wide mypy debt is disclosed. |
| 10 | PASS | The matching Codex log exists at the required URL, uses full GitHub URLs, records exact commands/results/SHAs/limitations and the separate publication boundary, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`. |
| 11 | PASS | No feature-extraction execution, image processing, reconstruction stage, UI workflow, engine installation/execution, neural model, metric calibration, schema/dependency/lock change, physical acceptance, PL-0169+ work, TASKS edit, or ChatGPT audit artifact edit was included in the Codex range. |

## Finding

### High - alias collision breaks order-independent normalization

In `core/src/packlab_core/feature_extraction.py`, `with_overrides` maps both
`peak_threshold` and `contrast_threshold` to
`contrast_peak_threshold`, then assigns each value into one dictionary entry.
The later input item silently wins.

Independent reproduction against the published code:

```text
a = {'peak_threshold': 0.006, 'contrast_threshold': 0.007}
b = {'contrast_threshold': 0.007, 'peak_threshold': 0.006}
a == b                         -> True
from_overrides(a).threshold    -> 0.007
from_overrides(b).threshold    -> 0.006
serialize(a) == serialize(b)   -> False
digest(a) == digest(b)         -> False
```

This is a provenance-relevant defect because the configuration digest is
intended to identify the normalized reconstruction settings. A caller cannot
rely on an equivalent mapping producing one configuration identity.

## Architecture / regression / security review

- The defect is confined to override normalization; no second authority or
  engine execution path was introduced.
- The remediation must preserve valid unique-field overrides, the preset
  identity/defaults, canonical serialization, COLMAP adapter mapping, and all
  current regression behavior.
- No secret, private scan, supplier file, signing material, binary, dependency,
  or lock-file change was found.

## TASKS.md action

Root `TASKS.md` remains unchecked for PL-0168 and is updated by this audit
publication to `CHANGES_REQUIRED`, with Required Actor `CODEX` and the V02
remediation prompt/criteria as the next action. PL-0169 remains unauthorized.

## Remediation

The bounded V02 correction is:

1. Make alias normalization deterministic and fail closed: equivalent mapping
   order must yield one normalized value and digest; conflicting aliases or a
   canonical field supplied alongside a conflicting alias must be rejected
   explicitly, or resolved by a documented order-independent rule.
2. Preserve non-mutating behavior and all existing valid default, override,
   validation, serialization, digest, and adapter behavior.
3. Add behavior-sensitive tests using equal mappings in opposite insertion
   orders, conflicting alias combinations, canonical-plus-alias combinations,
   and the no-mutation guarantee. The tests must exercise `from_overrides` and
   the resulting serialized/digested configuration.
4. Rerun the V02 focused, relevant boundary, full, lint, type, compile,
   protected-file, scope, privacy, and generated/binary checks and publish the
   matching V02 Codex log ending `READY_FOR_INDEPENDENT_AUDIT`.

No schema, dependency, lock, UI, engine, model, metric-calibration, PL-0169+,
or physical/native acceptance work is authorized for this remediation.

## Final conclusion

`CHANGES_REQUIRED`. PL-0168 is not independently accepted. The same
permanent task remains open until the bounded V02 remediation is implemented,
logged, and freshly audited.
