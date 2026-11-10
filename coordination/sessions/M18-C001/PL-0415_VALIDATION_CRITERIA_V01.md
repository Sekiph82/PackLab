# PL-0415 — Validation Criteria V01

1. A supplier change creates a new immutable asset revision. The prior revision, its supplier facts and its geometry links stay readable and referenceable.
2. Geometry is reused only after a recorded equivalence decision. Otherwise the change is routed to PL-0417.
3. Supplier facts carry SUPPLIER_FACT provenance with a source reference. There is no inferred certification, accuracy or manufacturing authorization.
4. SKU migration is explicit. Old SKU revisions stay valid only while the old asset revision is retained, and deletion is refused or flagged.
5. A synthetic dry-run exercises the real PackagingAsset/SKU contracts. No supplier, Kenya or physical evidence is claimed.
