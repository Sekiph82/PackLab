# CLAUDE_PEER_REVIEW - PL-0492 oval / flat bottle Design Model (PR #42, head 3ee81b3f)

Independent reviewer, not implementer.

Local tests: oval core+studio 13 passed; label binding, CAD label analysis, labels, package families, measure design, build_model 93 passed. CI passed (attempt 2).

Owner Scan Master (54ea0103..., recon source_digest bc161323...) refit at head: OVAL 61.7 x 33.7 x 166.8, neck 21.4, orientation 114.2 deg, spread 1.0 deg, 5.1 s. Deterministic.

HIGH: none.

MEDIUM
- Claimed 62.4 x 33.5 x 167.1 / 21.3 is NOT reproduced at head (up to 0.7 mm off). Record the head numbers.
- oval_section_fit.py:455 trusts the Scan Master z axis. A 5 deg tilt changes width 61.7 -> 68.2 with no refusal. A centre-drift-vs-z check is missing.
- package_families_view.py:400: the 5-6 s fit runs on the UI thread.

LOW
- package_families.py:_oval_spec scales the neck centre offset by sn, not sx/sy.
- The confirm tick resets only when the family changes, not when the Scan Master changes.
- The test_build_model flake predates this PR (20 s _pump, 3 concurrent builds); not touched here.
- The label_metric_surface_binding.py change only relaxes straight degree-1 edges; corners are still verified. Revolved label tests pass.

Verdict: PASS (with the MEDIUM evidence correction recorded).
