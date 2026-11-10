# PL-0414 — Validation Criteria V01

1. The decision tree maps the existing QA evidence (pre-reconstruction QA report, recapture-sector report) to a bounded, ordered set of actions: stop/re-import, full rescan, surface-treatment review, targeted recapture, retake photos, manual review, proceed to review.
2. The tree is deterministic and traceable: the same inputs give the same output, and both inputs are bound by digest.
3. The tree is advisory only. It never mutates captures, never accepts a scan, and never claims reconstruction quality or physical accuracy. Missing evidence never yields "proceed".
4. The document matches the implementation (action order, thresholds) and states retry and escalation rules and owner/site gates.
5. A synthetic dry-run on the real QA producers covers each primary action. No physical, station or Kenya capture is claimed. Thresholds need local re-validation.
