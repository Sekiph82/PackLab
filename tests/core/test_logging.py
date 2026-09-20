import json
import logging
from io import StringIO
from pathlib import Path

from packlab_core.logging import configure_logger, correlation_context, log_event


def test_structured_logging_propagates_correlation_and_defaults():
    stream = StringIO()
    logger = configure_logger("packlab-test-structured", stream=stream)
    with correlation_context(session_id="session-1", task_id="task-1", job_id="job-1"):
        log_event(logger, logging.INFO, "capture.started", "started", phase="capture")
    record = json.loads(stream.getvalue())
    assert record["event"] == "capture.started"
    assert record["session_id"] == "session-1"
    assert record["task_id"] == "task-1"
    assert record["job_id"] == "job-1"
    assert record["fields"] == {"phase": "capture"}


def test_logging_redacts_secrets_and_private_paths():
    stream = StringIO()
    logger = configure_logger("packlab-test-redaction", stream=stream)
    log_event(
        logger,
        logging.WARNING,
        "config.warning",
        "token=<PACKLAB_TEST_TOKEN_REDACTED>",
        api_key="real-looking-value",
        path=str(Path("C:/Users/owner/private/scan.packscan")),
    )
    text = stream.getvalue()
    assert "real-looking-value" not in text
    assert "C:/Users/owner" not in text
    assert "REDACTED" in text


def test_human_formatter_is_available_without_global_configuration():
    stream = StringIO()
    logger = configure_logger("packlab-test-human", stream=stream, structured=False)
    log_event(logger, logging.INFO, "test.event", "hello")
    assert "INFO test.event" in stream.getvalue()
