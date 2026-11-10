# PL-0414: Rescan/recapture decision tree based on QA metrics

**Planning SOP draft. It is not approved for production operation.** No Kenya site, station, sample or real capture has been used. Every threshold below has been checked only against synthetic renders and synthetic poses. Each threshold must be re-validated locally on owner-authorised real captures before any site relies on it (PL-0401, PL-0370 real-data gates).

## Inputs and authority

The tree is implemented as `packlab_core.rescan_decision.decide_rescan` (contract `packlab.rescan-decision.v1`). It reads two inputs:

- the pre-reconstruction QA report (`packlab.pre-reconstruction-qa.v1`): sharpness, pixel exposure, object-surface texture (PL-0375), capture coverage and metadata consistency;
- the recapture-sector report (`packlab.recapture-sector-suggestions.v1`): registration and coverage gaps, plus missing relative view sectors (PL-0378).

The output is advisory only (`advisory_only_operator_confirms_every_action`):

- An operator confirms every action.
- The tree never changes or deletes captures. It never marks a scan as passing or complete, and it never claims reconstruction quality or physical accuracy.
- Both input reports are bound by SHA-256 in `source_evidence`, so a later decision can be traced to the exact evidence it used. The tree does not check that both reports describe the same capture; the operator confirms that.

## Decision order (most severe first)

Every rule that fires is listed in the output. The first one becomes `primary_action`.

| # | Action | Fires when | Operator response |
| --- | --- | --- | --- |
| 1 | `stop_reimport_source` | QA `metadata_consistency` is `failed` (photo records, dimensions or digests do not agree) or `unavailable` (photo metadata missing) | Do not reconstruct or recapture yet. Re-export or re-import the PackScan; quarantine it if the mismatch persists (PL-0413 §source preservation). |
| 2 | `full_rescan` | Guided-orbit QA `coverage` is `warning` (fewer views than declared), or the recapture report decides `full_rescan` (gap with no missing sector, or no geometry anchor). A turntable coverage warning goes to rule 6 instead: one PackScan carries one frame, so frame coverage is a session-level check. | Repeat the complete capture per PL-0400. Keep the failed capture as an immutable record. |
| 3 | `surface_treatment_review` | At least 50 % of the texture-assessed views are `low_object_surface_texture` | Route to the PL-0399 treatment decision (default: no treatment) and the PL-0398 polarisation check. Retaking photos alone will not add texture. Owner/site approval is required before any treatment. |
| 4 | `targeted_recapture` | The recapture report decides `targeted_recapture` | Capture extra views only in the listed `sector_ids` (relative frame; no physical orientation is implied). Then rerun QA. |
| 5 | `retake_flagged_photos` | Any photo has a `sharpness` or `pixel_exposure` warning | Retake the listed `image_paths` with the same station settings. Investigate the lighting if the same views keep failing. |
| 6 | `manual_review_insufficient_evidence` | Any of these: a required QA component is missing, `unavailable` or has an unknown status; the recapture report is missing, `unavailable` or has an unknown decision; `targeted_recapture` lists no sector; texture counts are malformed; only a minority of views are low-texture; there is a turntable coverage warning; or nothing above fired but the evidence is not conclusive | A technical reviewer decides. Missing evidence never counts as a pass. |
| 7 | `proceed_to_reconstruction_review` | All of these hold: nothing above fired; QA `overall` is `no_automated_concern`; every required component is `pass` (texture may be `not_requested`); at least one photo was assessed; and the recapture decision is `no_recapture_indicated` | Continue to reconstruction under human review. This is not an acceptance. For glossy or transparent packages a texture `pass` is not evidence of printed texture: an unclipped reflection can read as texture (PL-0376 documented limit). |

A fully missing object mask makes texture `not_requested`, so rule 3 cannot fire. In that case the reviewer must not infer that the object surface has adequate texture.

## Retry limits and escalation

- If the same primary action recurs on the **third** attempt for one sample, stop and escalate to the independent technical reviewer. Record every attempt's decision digest. The value 3 is a planning value that needs local validation.
- Treatment decisions (rule 3) always need the PL-0399 owner/site approval. The tree cannot authorise treatment.
- Rule 1 failures are data-integrity problems. Never "fix" them by editing metadata by hand.

## Synthetic dry-run evidence

`tests/core/test_rescan_decision.py` runs the tree on outputs from the real QA and recapture producers:

- clean evidence: proceed;
- a single designed missing sector `az05-el00`: targeted recapture of exactly that sector;
- a full orbit with a remaining QA gap: full rescan;
- a low-texture white HDPE render (PL-0375 fixture): surface-treatment review;
- a dark photo: retake by image path;
- a metadata mismatch: stop, ahead of any capture action;
- missing evidence: manual review;
- wrong contracts and non-JSON payloads: rejected;
- adversarial payloads never reach `proceed`: missing, unknown or contradictory components; unknown recapture decisions; a turntable coverage warning; minority low texture; malformed counts; an empty sector list.

All of these are synthetic. No physical capture, factory run or Kenya data is claimed.
