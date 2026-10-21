"""Data models for LedgerLens AI reconciliation engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DiscrepancyCategory(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATUS_PENDING = "STATUS_PENDING"
    STATUS_FAILED = "STATUS_FAILED"
    UNMATCHED_ORDER = "UNMATCHED_ORDER"
    UNMATCHED_PAYMENT = "UNMATCHED_PAYMENT"
    DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    expected_amount: float
    currency: str
    customer_id: str
    created_at: str


@dataclass(frozen=True)
class PaymentRecord:
    transaction_id: str
    order_id: Optional[str]
    paid_amount: float
    currency: str
    status: PaymentStatus
    timestamp: str


@dataclass(frozen=True)
class ReconciliationResult:
    reference_id: str
    category: DiscrepancyCategory
    order_amount: Optional[float]
    payment_amount: Optional[float]
    currency: str
    status: Optional[PaymentStatus]
    system_notes: str
