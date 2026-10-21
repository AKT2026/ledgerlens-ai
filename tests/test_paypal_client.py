"""Unit tests for PayPal payload normalization and error handling."""

import pytest
from src.paypal_client import PayPalClient
from src.models import PaymentStatus


@pytest.fixture
def client():
    return PayPalClient(client_id="dummy_id", client_secret="dummy_secret")


def test_normalize_paypal_order_created(client):
    raw_payload = {
        "id": "PAYPAL-ORDER-12345",
        "status": "CREATED",
        "create_time": "2026-10-21T12:00:00Z",
        "purchase_units": [
            {
                "reference_id": "ORD-MERCHANT-99",
                "custom_id": "ORD-MERCHANT-99",
                "amount": {
                    "currency_code": "USD",
                    "value": "125.50"
                }
            }
        ]
    }

    record = client.normalize_paypal_order_to_payment_record(raw_payload)
    assert record.transaction_id == "PAYPAL-ORDER-12345"
    assert record.order_id == "ORD-MERCHANT-99"
    assert record.paid_amount == 125.50
    assert record.currency == "USD"
    assert record.status == PaymentStatus.PENDING


def test_normalize_paypal_order_completed(client):
    raw_payload = {
        "id": "PAYPAL-ORDER-67890",
        "status": "COMPLETED",
        "create_time": "2026-10-21T12:05:00Z",
        "purchase_units": [
            {
                "reference_id": "ORD-MERCHANT-100",
                "amount": {
                    "currency_code": "USD",
                    "value": "450.00"
                }
            }
        ]
    }

    record = client.normalize_paypal_order_to_payment_record(raw_payload)
    assert record.transaction_id == "PAYPAL-ORDER-67890"
    assert record.order_id == "ORD-MERCHANT-100"
    assert record.paid_amount == 450.00
    assert record.status == PaymentStatus.COMPLETED


def test_missing_credentials_raises_error():
    client_empty = PayPalClient(client_id="", client_secret="")
    with pytest.raises(ValueError, match="PayPal credentials missing"):
        client_empty.get_access_token()
