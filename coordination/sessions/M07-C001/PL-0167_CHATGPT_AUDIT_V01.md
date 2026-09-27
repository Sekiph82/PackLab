---
coordinationSchema: packlab-coordination/v1
artifactType: chatgpt-audit
cycleId: M07-C001
version: V01
actor: CHATGPT
verdict: CHANGES_REQUIRED
promptPath: coordination/sessions/M07-C001/PL-0167_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_CRITERIA_V01.md
codexLogPath: coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V01.md
auditedBase: 73e1900f4fdde907721a10d0bd79499384cf12ab
auditedHead: 9834264aaca829846b15ecce5f4999e794a76f05
---

# PackLab ChatGPT Independent Audit V01 - PL-0167

## Verdict

`CHANGES_REQUIRED`

The normal PackScan importer path is substantially implemented and the
reported validation gates independently pass. Two fail-closed gaps remain in
the reusable camera-prior boundary and ambiguous-metadata handling, so
PL-0167 remains open and PL-0168 is not authorized.

## Scope audited

- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`
- Live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_CRITERIA_V01.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V01.md
- Authorization/base commit: `73e1900f4fdde907721a10d0bd79499384cf12ab`
- Implementation commit: `12f630461fdadaa7cad8607ace10771b99353b69`
- Audited remote head / log-only commit: `9834264aaca829846b15ecce5f4999e794a76f05`
- Implementation diff: https://github.com/Sekiph82/PackLab/compare/73e1900f4fdde907721a10d0bd79499384cf12ab...12f630461fdadaa7cad8607ace10771b99353b69
- Full audited range: https://github.com/Sekiph82/PackLab/compare/73e1900f4fdde907721a10d0bd79499384cf12ab...9834264aaca829846b15ecce5f4999e794a76f05

## Evidence classification

### E1/E2 Codex evidence

- The matching log reports the implementation commit, separate log-only
  publication, exact commands, test results, limitations, and the required
  `READY_FOR_INDEPENDENT_AUDIT` marker.
- The log reports `14 passed` focused tests, `59 passed` relevant boundary
  tests, and `339 passed, 5 skipped, 1 deselected` for the locked full suite.

### E3 independent ChatGPT evidence

- Verified repository root, `main`, origin URL, clean status, fetch result,
  `HEAD == origin/main`, and divergence `0 0` at the audited head.
- Inspected the actual implementation/test/log diff. The pre-audit range
  contains only the three authorized implementation files, the new focused
  test file, and the matching Codex log; no tracker, audit artifact,
  dependency/lock file, binary, generated artifact, private scan, or secret
  was included.
- Independently reran the relevant boundary suite: `59 passed, 1 warning`.
- Independently reran `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked
  pytest -q -rs`: `339 passed, 5 skipped, 1 deselected, 2 warnings`.
  The skips are the existing OpenCV and Windows symlink capability limits.
- Independently reran Ruff, targeted mypy for the changed implementation
  modules, compileall, and `git diff --check`; all passed.
- Independently exercised the two failure cases below with the checked-out
  production functions.

### E4 owner evidence/decision

- None required for this software-boundary remediation. Native Apple/ARKit,
  physical calibration, and external-engine behavior remain outside this
  audit and are not claimed.

## Criteria matrix

| # | Result | Evidence / finding |
|---:|---|---|
| 1 | PASS | The live tracker authorized M07-C001 / READY / CODEX for PL-0167 before the implementation range; PL-0158 through PL-0166 are accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0168+ is not authorized. |
| 2 | PASS | The OpenReality architecture, ADR-0003, PL-0163 contract, PackScan authority, project/workspace/provenance authorities, and accepted PL-0166 seam remain intact in the audited range. |
| 3 | PASS | `ProjectManager.import_reconstruction_camera_priors` routes through the project-owned workspace manager, which revalidates RAW_CAPTURE and binds ordinary imported priors to exact PL-0166 working IDs. |
| 4 | FAIL | Normal schema/convention validation passes, but duplicate metadata is not always fail-closed. `_find_prior_payloads` removes a key on the second duplicate and can add it again on a third duplicate, allowing an ambiguous candidate to survive. |
| 5 | PASS | The importer preserves ignored, initialization-only, fixed, refined, and rejected modes and does not claim capture pose or intrinsics as M09 metric authority. Degraded poses are blocked for fixed/refined use. |
| 6 | FAIL | `assess_camera_priors` only compares `source_revision` and `source_digest` when those fields are present. An otherwise-valid prior with both fields absent is accepted for a matching working image, so the generic backend boundary does not require exact source/revision binding. |
| 7 | FAIL | The focused tests cover ordinary mapping, schema failures, modes, and one mismatch, but do not prove rejection of an unbound prior or three-way duplicate metadata. The missing tests allowed both defects through. |
| 8 | PASS | No feature extraction, matching, reconstruction engine, segmentation, UI, metric calibration, model, or PL-0168+ implementation was added. |
| 9 | PASS | The focused and locked full suites independently exited 0 with the results recorded above. |
| 10 | PASS | Ruff, targeted mypy, compileall, diff checks, protected-file/scope review, dependency/lock review, and privacy/secrets review passed; unchanged repository mypy debt is not misrepresented as clean. |
| 11 | PASS | The V01 Codex log exists at the required URL, uses full GitHub URLs, records exact evidence and limitations, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`. |
| 12 | PASS | Codex did not edit `TASKS.md`, create ChatGPT audit artifacts, assign an audit verdict, or start PL-0168; implementation and log publication commits are separately reviewable. |

## Findings

### High - missing generic prior binding

In `core/src/packlab_core/reconstruction.py`,
`assess_camera_priors` uses conditional mismatch checks:

```text
elif prior.source_revision is not None and ...
elif prior.source_digest is not None and ...
```

Independent reproduction with a valid 3x3 prior and no source digest or
revision returned:

```text
{'prior_valid': True, 'resolved_use': 'initialization-only', 'warnings': (),
 'source_digest': None, 'source_revision': None}
```

That permits a caller using the backend-neutral `ReconstructionJobSpec`
boundary to pass a prior without the exact source-package and working-set
identity required by criterion 6. The importer populates these fields, but
the reusable assessment boundary must fail closed when they are absent.

### High - ambiguous duplicate payload selection

In `apps/windows-studio/src/packlab_studio/reconstruction_workspace.py`,
duplicate candidate handling uses `candidates.pop(key)` and later allows the
same key to be inserted again. Independent reproduction with three uniquely
named, same-image intrinsics payloads returned one surviving candidate and
only one duplicate warning:

```text
{'candidates': {('intrinsics', 'photo-0001'):
 'metadata/intrinsics/photo-0001.json'},
 'warnings': ['duplicate camera metadata rejected: metadata/intrinsics/photo-0001.intrinsic.json']}
```

An ambiguous source package must not select any prior for that image/kind,
regardless of whether the duplicate count is two, three, or greater.

## Architecture / regression / security review

- Architecture boundaries: the PackLab-owned importer and PL-0166 working-set
  authority are correctly used; the defects are fail-closed contract gaps,
  not an authority relocation.
- Regression risk: the remediation must preserve valid unique-payload imports,
  all five use modes, dimension normalization, RAW_CAPTURE immutability, and
  the accepted PL-0166 workspace behavior.
- Test sensitivity: current tests use only unique metadata payloads and test a
  mismatch, not absence, at the generic prior-assessment boundary. New tests
  must exercise production entry points and the exact ambiguous candidate
  path.
- Security/privacy: no secret, private scan, supplier file, signing material,
  binary, or dependency/lock change was found.
- Scope leakage: no future-task implementation was found.

## TASKS.md action

Root `TASKS.md` remains unchecked for PL-0167 and is updated in the following
audit publication to `CHANGES_REQUIRED`, with Required Actor `CODEX` and the
V02 remediation prompt/criteria as the next action. PL-0168 remains
unauthorized.

## Remediation

The bounded V02 correction is:

1. Require non-rejected priors crossing `assess_camera_priors` to carry the
   exact source digest and source revision, and the source image identity
   needed by the importer; reject missing binding fields with an explicit
   warning/reason.
2. Change duplicate candidate tracking so once a `(kind, photo_id)` key is
   ambiguous it cannot be reintroduced or selected. Keep valid unique
   payloads working.
3. Add production-boundary tests for an unbound prior and for three or more
   same-image metadata payloads, while retaining the existing valid,
   malformed, mode, normalization, mismatch, and immutability coverage.
4. Rerun the V02 required focused/full/static/protected-file checks and publish
   the matching V02 Codex log ending `READY_FOR_INDEPENDENT_AUDIT`.

No schema, dependency, lock, UI, engine, model, metric-calibration,
PL-0168+, TASKS, or ChatGPT-audit edits are authorized for the remediation.

## Final conclusion

`CHANGES_REQUIRED`. The implementation is not independently accepted. The
same permanent PL-0167 ID remains open at the current frontier until the
bounded V02 remediation is implemented, logged, and freshly audited.
