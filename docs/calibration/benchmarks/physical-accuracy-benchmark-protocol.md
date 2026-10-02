# Physical accuracy benchmark protocol v1

This package defines the owner-run record contract for physical measurements of
at least a matte bottle, glossy bottle and jerrycan. It does not contain
physical measurements, acceptance limits, or benchmark results. An empty
template and synthetic contract tests are not physical evidence.

## Before a physical session

1. Assign the benchmark record ID and stable sample IDs to the actual objects.
   Keep one row for every attempted sample. A retry receives a new sample ID;
   retain the earlier rejected, invalid or missing-measurement row.
2. Choose and record the physical dimension IDs for each object. Record
   ground truth with a caliper in millimetres, including the owner-measured
   value, repeated readings, uncertainty, caliper reference, calibration-record
   reference, owner reference and UTC measurement time. Do not substitute
   nominal CAD, packaging, or manufacturer values for a physical reading.
3. Bind every scan and derived measurement to its stable scan ID/revision and
   measurement ID/revision. Missing links stay missing and keep the record
   `OWNER_REQUIRED`.
4. Record the environment and capture setup, including temperature, relative
   humidity, lighting, background/surface, camera-to-object setup, device model
   and lens reference. Do not estimate unavailable values.
5. Record each sample disposition as `ACCEPTED`, `REJECTED`, `INVALID`, or
   `MISSING_MEASUREMENT`. Rejected and invalid rows require a reason. A missing
   measurement row must not link a measurement result.

## Record status and interpretation

`OWNER_REQUIRED` is the blank-template status and remains in force whenever
physical ground truth, scan/measurement lineage, environment/setup metadata,
category coverage, or owner-controlled evidence references are missing.
`READY_FOR_AUDIT` means an owner has supplied complete records for the required
categories and each attempted sample has a retained disposition. It is only
an audit handoff; it does not mean the benchmark passed. The protocol defines
no physical acceptance threshold. Provisional mathematical consistency gates
remain distinct from physical accuracy.

The record digest is deterministic over its canonical UTF-8 JSON representation
with sorted keys and compact separators. It identifies the recorded content; it
does not attest that the content is true.

The three sample IDs in the blank JSON file contain `UNRECORDED`; they are
template placeholders, not stable IDs for physical objects. The owner must
replace them with stable IDs assigned to actual samples before recording any
physical evidence.

## Evidence and privacy

The record stores safe opaque references or SHA-256 digests only. Keep raw scan
bytes, photographs, unnecessary device identifiers, signatures, personal names,
serial numbers and confidential supplier information in the owner's private
evidence store. Do not place them in public Git. Public copies may contain only
authorized safe references, hashes, non-sensitive setup metadata, revisions
and measurements the owner has authorized for publication. AI visual
references, synthetic fixtures and nominal geometry never provide ground-truth
authority.

## Versioned contract

The executable validation contract is
`packlab_core.physical_accuracy_benchmark`; the public blank JSON template is
`physical-benchmark-record-template.json`, with its structural schema in
`physical-benchmark-record.schema.json`. Contract tests validate incomplete and
rejected-record behavior only. They do not create or imply any physical
measurement or acceptance threshold.
