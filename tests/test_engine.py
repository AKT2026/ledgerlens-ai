"""Automated tests for deterministic reconciliation engine."""

import pytest
from src.engine import ReconciliationEngine
from src.models import (
    DiscrepancyCategory,
    OrderRecord,
    PaymentRecord,
    PaymentStatus,
)
from src.synthetic_data import generate_sample_dataset


@pytest.fixture
def engine() -> ReconciliationEngine:
    return ReconciliationEngine()


def test_exact_match(engine: ReconciliationEngine):
    orders = [OrderRecord("O1", 100.0, "USD", "C1", "2026-10-21T00:00:00Z")]
    payments = [PaymentRecord("T1", "O1", 100.0, "USD", PaymentStatus.COMPLETED, "2026-10-21T00:01:00Z")]
    results = engine.reconcile(orders, payments)
    assert len(results) == 1
    assert results[0].category == DiscrepancyCategory.EXACT_MATCH
    assert results[0].reference_id == "O1"


def test_amount_mismatch(engine: ReconciliationEngine):
    orders = [OrderRecord("O1", 100.0, "USD", "C1", "2026-10-21T00:00:00Z")]
    payments = [PaymentRecord("T1", "O1", 95.0, "USD", PaymentStatus.COMPLETED, "2026-10-21T00:01:00Z")]
    results = engine.reconcile(orders, payments)
    assert len(results) == 1
    assert results[0].category == DiscrepancyCategory.AMOUNT_MISMATCH
    assert results[0].order_amount == 100.0
    assert results[0].payment_amount == 95.0


def test_pending_and_failed_statuses(engine: ReconciliationEngine):
    orders = [
        OrderRecord("O1", 50.0, "USD", "C1", "2026-10-21T00:00:00Z"),
        OrderRecord("O2", 70.0, "USD", "C2", "2026-10-21T00:00:00Z"),
    ]
    payments = [
        PaymentRecord("T1", "O1", 50.0, "USD", PaymentStatus.PENDING, "2026-10-21T00:01:00Z"),
        PaymentRecord("T2", "O2", 70.0, "USD", PaymentStatus.FAILED, "2026-10-21T00:01:00Z"),
    ]
    results = engine.reconcile(orders, payments)
    categories = {r.reference_id: r.category for r in results}
    assert categories["O1"] == DiscrepancyCategory.STATUS_PENDING
    assert categories["O2"] == DiscrepancyCategory.STATUS_FAILED


def test_duplicate_payments(engine: ReconciliationEngine):
    orders = [OrderRecord("O1", 100.0, "USD", "C1", "2026-10-21T00:00:00Z")]
    payments = [
        PaymentRecord("T1", "O1", 100.0, "USD", PaymentStatus.COMPLETED, "2026-10-21T00:01:00Z"),
        PaymentRecord("T2", "O1", 100.0, "USD", PaymentStatus.COMPLETED, "2026-10-21T00:02:00Z"),
    ]
    results = engine.reconcile(orders, payments)
    assert len(results) == 1
    assert results[0].category == DiscrepancyCategory.DUPLICATE_PAYMENT
    assert results[0].payment_amount == 200.0


def test_unmatched_order_and_unmatched_payment(engine: ReconciliationEngine):
    orders = [OrderRecord("O-ORPHAN", 40.0, "USD", "C1", "2026-10-21T00:00:00Z")]
    payments = [PaymentRecord("T-GHOST", "O-NONEXISTENT", 60.0, "USD", PaymentStatus.COMPLETED, "2026-10-21T00:01:00Z")]
    results = engine.reconcile(orders, payments)
    assert len(results) == 2
    cats = {r.category for r in results}
    assert DiscrepancyCategory.UNMATCHED_ORDER in cats
    assert DiscrepancyCategory.UNMATCHED_PAYMENT in cats


def test_full_synthetic_suite(engine: ReconciliationEngine):
    orders, payments = generate_sample_dataset()
    results = engine.reconcile(orders, payments)
    assert len(results) == 7
    found_categories = {r.category for r in results}
    assert DiscrepancyCategory.EXACT_MATCH in found_categories
    assert DiscrepancyCategory.AMOUNT_MISMATCH in found_categories
    assert DiscrepancyCategory.STATUS_PENDING in found_categories
    assert DiscrepancyCategory.STATUS_FAILED in found_categories
    assert DiscrepancyCategory.UNMATCHED_ORDER in found_categories
    assert DiscrepancyCategory.DUPLICATE_PAYMENT in found_categories
    assert DiscrepancyCategory.UNMATCHED_PAYMENT in found_categories
