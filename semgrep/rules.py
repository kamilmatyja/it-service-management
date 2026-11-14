# ai-generated: 100% - Semgrep positive/negative test cases for the two service-specific rules
import os


def test_clock_setting():
    # ruleid: svcdesk-test-clock-toggle
    os.environ.get("SVCDESK_TEST_CLOCK", "")
    # ok: svcdesk-test-clock-toggle
    os.environ.get("FEATURE_FLAG", "")


def broad_error_handler():
    try:
        perform_request()
    # ruleid: svcdesk-broad-exception-handler
    except Exception:
        report_error()

    try:
        perform_request()
    # ok: svcdesk-broad-exception-handler
    except ValueError:
        report_validation_error()


def perform_request():
    return None


def report_error():
    return None


def report_validation_error():
    return None
