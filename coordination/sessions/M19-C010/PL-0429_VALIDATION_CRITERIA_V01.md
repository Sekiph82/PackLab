# PL-0429 Validation Criteria V01 — Remote iPhone Capture Capability Gate

1. Checks remain local/read-only and do not enumerate LAN peers, access media or expose device identifiers.
2. Distinguish generic Apple PnP presence from an exact identified iPhone capture target and trusted-LAN endpoint.
3. If unavailable, record `BLOCKED_UNIDENTIFIED_CONNECTED_IPHONE_AND_TRUSTED_LAN_ENDPOINT` and minimum owner input.
4. No install/download, pairing, capture command, Actions, paid CI, PR, main push, native build or release claim.
