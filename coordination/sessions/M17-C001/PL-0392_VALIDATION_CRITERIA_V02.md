# PL-0392 — Validation Criteria V02

1. The disposable package fixture has an explicitly synthetic ID/name, no supplier identity and UNKNOWN status; its two SKU fixtures have synthetic IDs/names and DRAFT status. These markers are asserted in the test source.
2. Two distinct POVU SKU IDs reference exactly the same asset and immutable geometry revision.
3. Artwork revision/content references differ; serialized output includes no geometry or artwork bytes and asserts geometry is not copied or mutated. The exact geometry-reference key set is checked.
4. No claim is made about real Kenya inventory or production.
5. Tests remain unrun until the consolidated M17 validation checkpoint.
