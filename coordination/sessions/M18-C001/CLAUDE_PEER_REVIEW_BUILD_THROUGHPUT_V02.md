# CLAUDE_PEER_REVIEW: PR #38 build throughput (V02, head 9474a1c7)

Reviewed the diff d205d05a..9474a1c7 myself. Local run: test_build_model, test_provenance and test_reconstruction_execution, 26 passed. The real COLMAP 4.2.1 test ran on synthetic images and was not skipped. The V01 MEDIUM is fixed: stage and job records now match.

provenance.json: one in-process RLock covers each load, merge and atomic fsync+replace, so register() loses no updates. The new 4x15-thread test checks this.

**LOW**
- invalidate()/refresh_integrity() save without merging and could drop other records. No production code calls them.
- The lock is per process only, as documented.
- `recorded` is captured when a build is queued, not when it starts.
- The 6-image real test may not reorder ids. GPS priors are covered only by the synthetic test.

**Verdict: PASS**
