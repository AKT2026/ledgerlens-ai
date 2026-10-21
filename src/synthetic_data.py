"""Synthetic data generator for LedgerLens AI test runs."""

from typing import List, Tuple
from src.models import OrderRecord, PaymentRecord, PaymentStatus


def generate_sample_dataset() -> Tuple[List[OrderRecord], List[PaymentRecord]]:
    orders = [
        OrderRecord("ORD-101", 150.00, "USD", "CUST-01", "2026-10-21T10:00:00Z"),
        OrderRecord("ORD-102", 200.00, "USD", "CUST-02", "2026-10-21T10:15:00Z"),
        OrderRecord("ORD-103", 75.50, "USD", "CUST-03", "2026-10-21T10:30:00Z"),
        OrderRecord("ORD-104", 320.00, "USD", "CUST-04", "2026-10-21T10:45:00Z"),
        OrderRecord("ORD-105", 89.99, "USD", "CUST-05", "2026-10-21T11:00:00Z"),
        OrderRecord("ORD-106", 120.00, "USD", "CUST-06", "2026-10-21T11:15:00Z"),
    ]

    payments = [
        PaymentRecord("TXN-PAYPAL-9001", "ORD-101", 150.00, "USD", PaymentStatus.COMPLETED, "2026-10-21T10:02:10Z"),
        PaymentRecord("TXN-PAYPAL-9002", "ORD-102", 185.00, "USD", PaymentStatus.COMPLETED, "2026-10-21T10:17:05Z"),
        PaymentRecord("TXN-PAYPAL-9003", "ORD-103", 75.50, "USD", PaymentStatus.PENDING, "2026-10-21T10:31:00Z"),
        PaymentRecord("TXN-PAYPAL-9004", "ORD-104", 320.00, "USD", PaymentStatus.FAILED, "2026-10-21T10:46:12Z"),
        PaymentRecord("TXN-PAYPAL-9006A", "ORD-106", 120.00, "USD", PaymentStatus.COMPLETED, "2026-10-21T11:16:00Z"),
        PaymentRecord("TXN-PAYPAL-9006B", "ORD-106", 120.00, "USD", PaymentStatus.COMPLETED, "2026-10-21T11:16:05Z"),
        PaymentRecord("TXN-PAYPAL-9999", "ORD-UNKNOWN-888", 45.00, "USD", PaymentStatus.COMPLETED, "2026-10-21T11:30:00Z"),
    ]

    return orders, payments
