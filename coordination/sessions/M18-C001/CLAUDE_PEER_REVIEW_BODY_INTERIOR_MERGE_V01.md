# CLAUDE_PEER_REVIEW: PR #34 body-interior merge (PL-0489)
Independent Claude peer, read-only, head 5917e861. CI: both checks PASS. Local: 26 passed (interior, project_parts, closure_placement). Probes: rv-interior/ in the worktree.

## HIGH
- core interior_merge.py:316-335: deepest_covered needs contiguous bands starting at the rim. Probe with a 1.5 mm wall (typical HDPE/PET; fixtures only use 2.5 mm): the 2-4 mm band reaches 0.50 because of the wall margin, so the result is "merged" with deepest = 0 mm although 60 mm was scanned. Same for 1.0 and 0.5 mm walls. The error under-reports (safe direction), but the core metric is wrong.

## MEDIUM
- :317-331: no surface or outlier filter. A scan with only the rim plus floaters still merges, and the floaters are saved as interior. One point per sector counts as coverage.
- A 1.4 mm rim-height offset is within tolerance but cuts coverage to about 0.75, right at the threshold.

## LOW
- The base-thickness bands always show as "Taranmadı" ("not scanned"), and "toplam derinlik" ("total depth") is really the rim height. A re-merge leaves the old artifact orphaned.
- Cancel race, staleness, provenance and the no-fill Turkish wording are OK.

Verdict: CHANGES_REQUIRED
