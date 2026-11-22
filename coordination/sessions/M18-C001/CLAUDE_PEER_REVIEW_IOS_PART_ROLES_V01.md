# CLAUDE_PEER_REVIEW - PL-0482 iOS roles + PL-0489 interior (PR #30, head 0bda00fe) V01

Reviewer: Claude peer subagent (not implementer). Evidence: diff origin/main...0bda00fe; CI 45044981137 (all jobs success: 246/246 XCTests, E2E 2x80 images, receiver "part_role values: ['absent','body']"). Failed runs 45031239553/45036520934 (role row and Start hit points), 45039170274/45041379531 (History menu item). Confirmed: main run 45023213814 tapped History only via XCUITest's "rdar://59288308 center point" fallback.

HIGH: none. MEDIUM: none.

LOW
- SessionFoundation.swift make(): interior refused only for presetID .turntable. Capture mode "turntable" plus matte preset is accepted.
- History: partRole is always draft.role, so legacy sessions show and count as "Assembled". Studio never counts them until assigned.
- Interior preset keeps the base id/version. Only part_role tells it apart.
- coverageRestartedMessage: the test only checks it is non-empty; the resume path is not exercised.

Verified: the 7 roles match the schema enum exactly; assembled omits the key; the mirror test now allows part_role (M2 closed). Rings 55/65/75/85 x16 strict, bands tested. Turntable preset keeps its own orbit. Human labels, no raw code, flexible chips. UI taps use identifiers plus an isSelected wait, with no coordinates. Receiver check is exact; workflow count 243+3.

Verdict: PASS. PL-0482/0489 still need real device scans.
