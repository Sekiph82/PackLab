from packlab_core.capabilities import CapabilityStatus, ProbeResult, discover_capabilities


def test_available_capability_parses_version():
    records = discover_capabilities(
        lambda command: ProbeResult("ok", "COLMAP 3.11.0", "exit code 0")
    )
    assert records["colmap"].status is CapabilityStatus.AVAILABLE
    assert records["colmap"].version == "3.11.0"
    assert records["colmap"].provenance.startswith("executable probe")


def test_missing_capability_is_unavailable():
    records = discover_capabilities(lambda command: ProbeResult("missing", detail="not installed"))
    assert records["cuda"].status is CapabilityStatus.UNAVAILABLE


def test_malformed_version_and_probe_error_are_unknown():
    def probe(command):
        if command[0] == "colmap":
            return ProbeResult("ok", "COLMAP development build", "exit code 0")
        return ProbeResult("error", detail="timeout")

    records = discover_capabilities(probe)
    assert records["colmap"].status is CapabilityStatus.UNKNOWN
    assert records["openmvs"].status is CapabilityStatus.UNKNOWN


def test_opencascade_binding_remains_unselected():
    record = discover_capabilities(lambda command: ProbeResult("missing"))["opencascade"]
    assert record.status is CapabilityStatus.UNKNOWN
    assert "not selected" in record.provenance
