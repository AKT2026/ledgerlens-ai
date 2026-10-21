"""Automated tests for AI investigation layer and offline fallback."""

import pytest
from src.ai_explainer import AIExplainer, InvestigationReport


@pytest.fixture
def explainer():
    # Use empty key to force deterministic offline engine test
    return AIExplainer(api_key="")


def test_fallback_amount_mismatch(explainer):
    sample_data = {
        "category": "AMOUNT_MISMATCH",
        "reference_id": "ORD-102",
        "order_amount": 200.0,
        "payment_amount": 185.0,
        "variance": -15.0,
        "status": "COMPLETED",
        "system_notes": "Variance of -15.00 (Expected: 200.00, Paid: 185.00).",
    }
    report = explainer.investigate(sample_data)
    assert isinstance(report, InvestigationReport)
    assert report.operational_risk == "MEDIUM"
    assert len(report.recommended_actions) >= 2
    assert "ORD-102" in report.root_cause_analysis


def test_fallback_duplicate_payment(explainer):
    sample_data = {
        "category": "DUPLICATE_PAYMENT",
        "reference_id": "ORD-106",
        "order_amount": 120.0,
        "payment_amount": 240.0,
        "variance": 120.0,
        "status": "COMPLETED",
        "system_notes": "Multiple transactions found.",
    }
    report = explainer.investigate(sample_data)
    assert report.operational_risk == "HIGH"
    assert report.suggested_audit_status == "ESCALATED_PAYPAL"


def test_investigation_report_schema():
    report = InvestigationReport(
        root_cause_analysis="Test analysis",
        operational_risk="LOW",
        recommended_actions=["Action 1", "Action 2"],
        suggested_audit_status="RESOLVED",
    )
    assert report.operational_risk in ["LOW", "MEDIUM", "HIGH"]
    assert len(report.recommended_actions) == 2
