# PackLab GitHub Actions artifact retention

PackLab's repository is private and the product is proprietary internal factory software. Workflow artifacts are temporary, owner-private engineering evidence unless an explicitly approved internal deployment candidate is retained. No artifact is a public release, legal sign-off, or factory rollout authorization.

## Retention classes

| Class | Purpose | Retention | Size and count | Durable source of truth |
| --- | --- | --- | --- | --- |
| A. Accepted internal Installer candidate | One exact, SHA-verified, unsigned Installer approved for controlled owner-internal evaluation | 60 days for the current PL-0350 warm candidate; one active retained candidate, at most 1,000,000,000 bytes | At most one installer-sized archive; no per-build long retention | Private GitHub Actions artifact plus its origin manifest and committed reports |
| B. Source, notices, and license evidence | Corresponding source, NOTICE/license mapping, and compliance evidence | Persist in reviewed private Git history; generated workflow copies at most 14 days | Prefer text-only, bounded to 100 MiB in packaging gates | Versioned source tree and immutable commit SHA; legal review remains required |
| C. OCCT SDK / OCP runtime checkpoints | Recovery/transient checkpoints and exact provenance | Ordinary workflow artifacts 1 day; explicit recovery-only SDK/quarantine evidence up to 14 days; controlled cache uses its separate cache policy and exact key/manifest | Existing run budget limits; no routine long-lived duplicate runtime archives | Pinned source lock, cache key, producer run, payload manifest and hashes |
| D. Smoke diagnostics | Small sanitized logs/manifests needed to diagnose a run | 3 days | Small per-run diagnostic bundle, no customer scans or private business data | Focused run links and committed test harness |
| E. Disposable staging | Native staging, pre-clearance and temporary packaging outputs | 1 day, or no upload where unneeded; quarantine is a recovery-only exception capped at 14 days | Existing per-run byte caps; fail if required evidence is absent | Rebuildable from pinned source and committed locks; no native rebuild merely to renew retention |

GitHub's live repository setting was read as **90 days**, with `maximum_allowed_days=400`. The one-time candidate uses 60 days, within that live setting. The account billing/storage allowance and current spend could not be read with the available token: GitHub returned 404 for billing endpoints and stated that account-level billing usage requires an additional `user` token scope. GitHub's published shared artifact/Packages storage rate is **$0.25 USD per GB-month**; at the exact Installer payload size, 60 days would be about **$0.41 gross** before any included plan allowance or billing-cycle rounding. The actual account charge is unverified. This policy therefore uses a conservative 5,000,000,000-byte active-artifact cap for the one transfer and records live artifact/cache inventory, but does not claim a billing quote or free quota. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Security and recovery

- Repository must remain private. Workflows have least-privilege `actions: read` and `contents: read`; no write token, secret, certificate, customer/media file, or signed artifact is included.
- Only the exact PL-0350 source run, artifact ID, artifact ZIP digest/length, and Installer EXE digest/length pinned in the PL-0352 verifier can be transferred. The bridge is manual, `main`-only, serialized, no-build, fails closed on expiry, wrong source, wrong repository visibility, wrong digest, missing evidence, duplicate target, or the active storage cap.
- The retained archive has a distinct outer SHA-256 from the source archive. The nested Installer SHA-256 remains the exact verified EXE. Record the retained artifact ID, digest, size, expiry, run, and source chain in the PL-0352 log.
- The PL-0351 smoke may migrate to a retained artifact only after the bridge artifact is live and its Installer/source metadata is verified. It must preserve both the original producer identity and the retention-transfer origin.
- GitHub cache entries are not durable Installer retention. The existing OCP cache remains a separately keyed, content-verified acceleration cache; artifact retention does not silently lengthen cache life.
- Monitor artifact expiry before each controlled commissioning window. Renew only by an owner-authorized run of the no-build verifier against the same approved source, after checking privacy, storage cap, exact hashes, and remaining duration. Never rebuild OCCT/OCP or the Installer merely to reset an expiry clock.
- Deleting an artifact requires explicit owner authorization. If private Actions retention cannot meet the commissioning horizon or storage/billing is not acceptable, document the exact gap and seek an owner-approved private vault destination; do not upload elsewhere automatically.
- `legal_review_required=true`, `public_release_authorized=false`, and `factory_rollout_authorized=false` remain in force.
