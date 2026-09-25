# PL-0132 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The report implementation is structurally sound:
- it is generated only from an already validated `PackScanReport`;
- includes capture/schema/source/digest/image/photo/capture-mode/device/calibration/optional payload data;
- stores portable relative raw/report locations;
- accepts only caller-supplied non-secret transfer provenance fields;
- persists atomically;
- produces deterministic warning ordering for absent calibration/mask/diagnostics.

The frozen V01 evidence matrix is incomplete.

### Required report variants are not tested

The only PL-0132 report test covers a network import with:
- calibration absent;
- optional mask/diagnostics/calibration absent.

It does not cover:
- manual/drop import report;
- calibration present;
- optional diagnostics present;
- optional mask present;
- report counts for those optional payloads.

The frozen criteria explicitly require golden/report tests for manual and network imports, calibration present/absent, optional diagnostics/masks, warning ordering and privacy redaction.

## Required remediation

Preserve `ImportReport` / `ImportReportStore`. Add deterministic report fixtures/tests for manual and network channels, calibration present and absent, optional mask/diagnostics present and absent, counts/warning ordering, transfer provenance restriction, and privacy redaction.

PL-0132 remains unchecked.

Decision: **CHANGES_REQUIRED**
