# PL-0420 Research — Learned Packaging Feature Recognition

Status: research/design only; no learned feature model or checkpoint selected, installed, downloaded, trained, or enabled.

## Decision summary

Treat shoulder/base/handle recognition as **semantic part labeling of an already captured package**, not as ordinary object segmentation. Keep the current PackLab SAM 2 image-mask backend for object-mask proposals. A later feature recognizer should consume an identified reconstruction revision and return a versioned, human-reviewable feature proposal. It must never edit Scan Master, measurements, calibration, capture coverage, or authoritative geometry.

Recommended path:

1. Establish a small, owner-approved feature-label set and a manual annotation/review workflow before training. Start with `BODY`, `SHOULDER`, `BASE`, `HANDLE`, `HANDLE_OPENING`, and `UNKNOWN_OR_UNOBSERVED`; add `NECK` only where the boundary can be labeled consistently.
2. Use the existing promptable 2D masks and multiview object-mask lifting as annotation assistance, with an explicit human label/correction step. Existing object masks identify an object boundary; they do not themselves identify packaging subparts.
3. Build a deterministic geometry baseline for rotationally symmetric bottle profiles. Keep handle and asymmetric jerrycan proposals separate because a radial profile does not describe their topology.
4. Only after suitable labeled PackLab scans exist, compare a modest point-set segmentation baseline such as PointNet++ against a point-transformer baseline. Select no model/checkpoint until its exact source, weights, training data, license, runtime and deployment path are separately reviewed and accepted.

This sequence gives PackLab an auditable non-learned baseline and useful annotations before taking on a model dependency. The sequence is a PackLab engineering recommendation, not a claim that any cited paper has been validated on PackLab package scans.

## What the current architecture already provides

- `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md` separates model adapters from PackLab-owned requests/results and records source image identity, pixel coordinates, transforms, prompt evidence and provenance.
- `docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md` selects local SAM 2.1 Hiera Base+ for prompted/automatic **image object masks**. It does not select a semantic bottle-part model.
- `core/src/packlab_core/object_mask_lifting.py` lifts versioned image masks into a reconstruction using recorded cameras, source revisions, visibility and support rules. This is an appropriate annotation bridge, not proof that an image mask carries a 3D part label.
- The existing segmentation contract treats mask sets as derived artifacts. A feature-recognition result should be a separate proposal referencing the exact source/reconstruction/mask revisions, with per-region label/confidence and review state; it should not mutate those inputs.
- `docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md` keeps generated visual geometry explicitly non-authoritative. PL-0420 feature proposals must not be confused with that generated geometry lane.

## Compared approaches

| Approach | Useful role | Main limits for PackLab |
| --- | --- | --- |
| Prompted 2D SAM 2 masks plus manual semantic labels | Bootstrap human-assisted labels in captured views; reuse the accepted image mask and provenance path | SAM 2 predicts image masks from prompts. A whole-object mask does not decide which pixels are shoulder/base/handle, and multi-view masks need correspondence and review before lifting. |
| Deterministic profile/geometry baseline | Find candidate transition bands on approximately axisymmetric bottles using the fitted axis, radial profile and local slope/curvature; establish interpretable baselines | Sensitive to missing views, scan noise and asymmetric designs; not an adequate handle/jerrycan topology detector by itself. Thresholds are proposals and require measured geometry or operator review. |
| PointNet++-style point-set segmentation | A relatively direct learned baseline for per-point semantic labels; the paper studies hierarchical local features and sampling-density variation | The paper's benchmark results do not establish performance on packaging. It needs PackLab labels, source/checkpoint licensing review, runtime/resource checks and strict package-family holdouts. |
| Point Transformer V3-style point-cloud model | A later higher-capacity comparison if a real labeled corpus and hardware budget justify it | General point-cloud benchmark performance is not PackLab evidence. Training, inference cost, code license, weight license, datasets and packaged runtime need separate review. Do not select weights from a paper result alone. |

The PointNet++ paper demonstrates hierarchical local point-set feature learning and evaluates segmentation, including sensitivity to nonuniform point sampling. PTv3 reports an efficient point-cloud architecture and downstream results across multiple tasks. These findings justify comparing the model families in a controlled PackLab dataset later; they do not establish which will work best for bottles or handled containers.

## Data and evaluation needed before a learned model

- Define one annotation ontology and boundary guide. Distinguish absent from unobserved; never label an occluded or unscanned surface as negative evidence.
- Obtain owner-approved scans and explicit rights to use each scan for model development. Keep source photos, scans and supplier material private; do not upload them to external services.
- Record package identity/family, scan session, view coverage, reconstruction revision, unit/scale state, source mask revisions, annotator, correction history and label version.
- Split train/validation/test by physical package identity and capture session, not by adjacent views of the same item. Include held-out package families to measure transfer rather than memorization.
- Report per-class precision/recall and IoU, boundary distance in millimetres where scale is verified, abstention/unknown rate, and errors around shoulder/base transitions and handle openings. Report low-texture, reflective, transparent and missing-view cohorts separately.
- Compare to manual annotations and the deterministic baseline. Model confidence is advisory; uncertain, unsupported or out-of-distribution results must abstain for review.

## Authority, privacy and deployment

- Store each result as a proposal tied to immutable source and reconstruction revisions. Accepting a proposal should create a new explicit, auditable feature/annotation revision; it must not rewrite captured bytes or automatically promote geometry.
- No learned region label can satisfy Scan Master acceptance, calibration, a measurement, or capture-coverage requirements.
- The owner wants PackLab to be free to use while source code remains private. This preference does not itself grant a model license. A hosted service is the deployment pattern that can keep server-side code and weights off user devices; a downloadable desktop client cannot guarantee that compiled code or bundled weights are not extracted. The deployment target is not frozen by PL-0420.
- Before any model use, review code and checkpoint terms separately, plus training-data rights, permitted commercial/noncommercial use, attribution/redistribution, acceptable-use restrictions, runtime dependencies and whether inference is local or hosted. Pin the exact model revision and checkpoint digest only after the owner has accepted that candidate's terms. No such candidate is accepted here.

## Sources

### PackLab primary architecture

- [PL-0184 segmentation backend contract](PL-0184_SEGMENTATION_BACKEND_CONTRACT.md)
- [ADR-0004 SAM 2.1 selection](../architecture/adr/ADR-0004-sam2.1-segmentation-backend.md)
- [PackLab dependency/license register](../architecture/DEPENDENCY_LICENSE_REGISTER.md)
- [PL-0435 AI visual-reference authority contract](PL-0435_AI_VISUAL_REFERENCE_LANE.md)

### External primary sources

- Qi et al., [PointNet++: Deep Hierarchical Feature Learning on Point Sets in a Metric Space](https://arxiv.org/abs/1706.02413) — point sets, hierarchical neighborhoods, density variation and segmentation research.
- Wu et al., [Point Transformer V3: Simpler, Faster, Stronger](https://arxiv.org/abs/2312.10035) and the [official project repository](https://github.com/Pointcept/PointTransformerV3) — point-cloud architecture research and implementation entry point. This is not a license clearance for any checkpoint or training data.
- Meta, [Segment Anything Model 2](https://ai.meta.com/research/sam2/) — promptable image/video object segmentation. PackLab's exact SAM 2.1 choice and local runtime are recorded in ADR-0004.
- PointNet++'s [Stanford project page](https://web.stanford.edu/~rqi/pointnet2/) — paper, code and data pointers.

## Limits and next implementation boundary

This report is not a benchmark, model selection, training authorization, license opinion, or proof of accuracy on PackLab scans. The next implementation should first add a versioned feature-label/proposal contract and deterministic baseline tests, then a private owner-approved annotation cohort and benchmark. A learned adapter remains a separate later task with its own licensing/checkpoint gate.
