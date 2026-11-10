# PL-0431 Validation Criteria V01 — Scan Master vs Design Model Review Mode

1. The review binding requires immutable Scan Master and Design Model revisions, matching project identity, and exact source IDs/digests.
2. The Design Model preview geometry digest is checked against its supplied digest; the displayed record identifies which exact Design Model revision it represents.
3. Ghosted overlay is rejected unless the Design Model names the exact Scan Master revision and source geometry digest. Side-by-side remains available for unlinked/standalone models and labels that relationship.
4. Side-by-side and ghosted presentations are deterministic, visibly distinguish the two sources, and visibly identify both as review-only/non-authoritative.
5. Neither operation mutates the input revisions or geometry. AI visual reference scene objects are not accepted as comparison inputs.
6. Focused synthetic tests pass in the already installed supported local environment, and `git diff --check` passes.
7. No Actions, paid CI, PR, source push to `main`, native build, Installer build, model download/inference, or release/hosted/device acceptance claim occurs.
