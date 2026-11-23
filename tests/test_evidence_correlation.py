import json
from types import SimpleNamespace

from core.evidence_correlation import correlate_evidence, export_correlations


def report(*pairs):
    return SimpleNamespace(checks=[
        SimpleNamespace(check_name=name, finding_type=kind)
        for name, kind in pairs
    ])


def ids(result):
    return {item.observation_id for item in correlate_evidence(result)}


def test_fee_and_urgency():
    r = report(("fee_detector", "risk_signal"), ("urgency_channel", "risk_signal"))
    assert "fee_and_urgency" in ids(r)


def test_fee_alias():
    r = report(("fee_request", "risk_signal"), ("urgency_channel", "risk_signal"))
    assert "fee_and_urgency" in ids(r)


def test_no_correlation_from_unknown_fee():
    r = report(("fee_detector", "unknown"), ("urgency_channel", "risk_signal"))
    assert "fee_and_urgency" not in ids(r)


def test_no_correlation_from_only_fee():
    assert not correlate_evidence(report(("fee_detector", "risk_signal")))


def test_domain_conflict_and_fee():
    r = report(("email_domain", "contradiction"), ("fee_detector", "risk_signal"))
    assert "domain_conflict_with_risk" in ids(r)


def test_domain_support_not_conflict():
    r = report(("email_domain", "supporting_evidence"), ("fee_detector", "risk_signal"))
    assert "domain_conflict_with_risk" not in ids(r)


def test_mixed_support_and_contradiction():
    r = report(("email_domain", "contradiction"), ("domain_intelligence", "supporting_evidence"))
    assert "mixed_support_and_contradiction" in ids(r)


def test_no_mixed_evidence_from_risk_only():
    r = report(("email_domain", "risk_signal"), ("fee_detector", "risk_signal"))
    assert "mixed_support_and_contradiction" not in ids(r)


def test_deduplicates_check_names():
    r = report(("fee_detector", "risk_signal"), ("fee_detector", "risk_signal"),
               ("urgency_channel", "risk_signal"))
    item = correlate_evidence(r)[0]
    assert item.related_checks == ("fee_detector", "urgency_channel")


def test_json_export():
    r = report(("fee_detector", "risk_signal"), ("urgency_channel", "risk_signal"))
    data = export_correlations(r)
    assert data[0]["related_checks"] == ["fee_detector", "urgency_channel"]
    assert json.loads(json.dumps(data)) == data


def test_empty_report():
    assert correlate_evidence(report()) == []


def test_enum_compatible():
    from enum import Enum
    class Finding(Enum):
        RISK = "risk_signal"
    r = report(("fee_detector", Finding.RISK), ("urgency_channel", Finding.RISK))
    assert "fee_and_urgency" in ids(r)
