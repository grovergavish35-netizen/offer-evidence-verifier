
from core.pipeline import verify_offer

from core.evidence_trace import (
    EvidenceTrace,
    build_evidence_traces,
    export_evidence_traces,
)

def get_trace(traces, check_name):
    matches = [
        trace
        for trace in traces
        if trace.check_name == check_name
    ]

    assert len(matches) == 1, (
        f"Expected one trace for {check_name}. "
        f"Found {len(matches)}."
    )

    return matches[0]

def test_email_trace_line_number():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@examp1e.com\n"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "email_domain")

    assert trace.line_number == 3
    assert trace.evidence_text == (
        "Email: hr@examp1e.com"
    )
    assert trace.trace_status == "candidate_line_match"

def test_fee_trace_line_number():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Pay registration fee of Rs 2500.\n"
    )

    report = verify_offer(text)
    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "fee_detector")

    assert trace.line_number == 3
    assert "registration fee" in trace.evidence_text.lower()

def test_whatsapp_trace_line_number():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Contact HR on WhatsApp.\n"
    )

    report = verify_offer(text)
    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "urgency_channel")

    assert trace.line_number == 3
    assert "WhatsApp" in trace.evidence_text

def test_negated_whatsapp_not_selected():
    text = (
        "Company: Example Technologies\n"
        "No WhatsApp interviews are conducted.\n"
    )

    report = verify_offer(text)
    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "urgency_channel")

    assert trace.evidence_text is None
    assert trace.line_number is None

def test_all_checks_have_traces():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@example.com\n"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    traces = build_evidence_traces(text, report)

    assert len(traces) == len(report.checks)

    assert all(
        isinstance(trace, EvidenceTrace)
        for trace in traces
    )

def test_trace_preserves_original_findings():
    text = (
        "Company: Example Technologies\n"
        "Email: hr@examp1e.com\n"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    original_findings = [
        result.finding
        for result in report.checks
    ]

    build_evidence_traces(text, report)

    assert [
        result.finding
        for result in report.checks
    ] == original_findings

def test_trace_has_explanation_and_limitation():
    text = (
        "Company: Example Technologies\n"
        "Email: hr@examp1e.com\n"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "email_domain")

    assert trace.reason
    assert trace.limitation
    assert trace.source

def test_export_json_serializable():
    import json

    text = (
        "Company: Example Technologies\n"
        "Email: hr@example.com\n"
    )

    report = verify_offer(text)

    data = export_evidence_traces(text, report)

    serialized = json.dumps(data)

    assert isinstance(serialized, str)
    assert len(data) == len(report.checks)

def test_consistency_not_falsely_line_traced():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
    )

    report = verify_offer(text)
    traces = build_evidence_traces(text, report)

    trace = get_trace(traces, "offer_consistency")

    assert trace.line_number is None
    assert trace.trace_status == "not_line_traced"

def test_trace_status_values():
    text = (
        "Company: Example Technologies\n"
        "Email: hr@example.com\n"
    )

    report = verify_offer(text)
    traces = build_evidence_traces(text, report)

    allowed = {
        "candidate_line_match",
        "not_line_traced",
    }

    assert all(
        trace.trace_status in allowed
        for trace in traces
    )