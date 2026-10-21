"""Deterministic reconciliation engine for LedgerLens AI."""

from collections import defaultdict
from typing import Dict, List, Set
from src.models import (
    DiscrepancyCategory,
    OrderRecord,
    PaymentRecord,
    PaymentStatus,
    ReconciliationResult,
)

AMOUNT_TOLERANCE = 0.001


class ReconciliationEngine:
    def reconcile(
        self,
        orders: List[OrderRecord],
        payments: List[PaymentRecord],
    ) -> List[ReconciliationResult]:
        results: List[ReconciliationResult] = []

        payments_by_order: Dict[str, List[PaymentRecord]] = defaultdict(list)
        unlinked_payments: List[PaymentRecord] = []

        for p in payments:
            if p.order_id:
                payments_by_order[p.order_id].append(p)
            else:
                unlinked_payments.append(p)

        matched_order_ids: Set[str] = set()

        for order in orders:
            matched_order_ids.add(order.order_id)
            related_payments = payments_by_order.get(order.order_id, [])

            if not related_payments:
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.UNMATCHED_ORDER,
                        order_amount=order.expected_amount,
                        payment_amount=None,
                        currency=order.currency,
                        status=None,
                        system_notes=f"Order {order.order_id} has no recorded payment.",
                    )
                )
                continue

            if len(related_payments) > 1:
                total_captured = sum(p.paid_amount for p in related_payments)
                tx_ids = ", ".join(p.transaction_id for p in related_payments)
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.DUPLICATE_PAYMENT,
                        order_amount=order.expected_amount,
                        payment_amount=total_captured,
                        currency=order.currency,
                        status=related_payments[0].status,
                        system_notes=(
                            f"Multiple transactions ({tx_ids}) found for Order {order.order_id}. "
                            f"Combined payment: {total_captured:.2f} vs expected {order.expected_amount:.2f}."
                        ),
                    )
                )
                continue

            payment = related_payments[0]

            if order.currency.upper() != payment.currency.upper():
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.CURRENCY_MISMATCH,
                        order_amount=order.expected_amount,
                        payment_amount=payment.paid_amount,
                        currency=f"{order.currency}/{payment.currency}",
                        status=payment.status,
                        system_notes=(
                            f"Currency mismatch: Order is {order.currency}, "
                            f"Payment settled in {payment.currency}."
                        ),
                    )
                )
                continue

            if payment.status == PaymentStatus.PENDING:
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.STATUS_PENDING,
                        order_amount=order.expected_amount,
                        payment_amount=payment.paid_amount,
                        currency=order.currency,
                        status=payment.status,
                        system_notes=f"Payment {payment.transaction_id} is still PENDING at processor.",
                    )
                )
                continue

            if payment.status == PaymentStatus.FAILED:
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.STATUS_FAILED,
                        order_amount=order.expected_amount,
                        payment_amount=payment.paid_amount,
                        currency=order.currency,
                        status=payment.status,
                        system_notes=f"Payment {payment.transaction_id} marked FAILED by processor.",
                    )
                )
                continue

            diff = abs(order.expected_amount - payment.paid_amount)
            if diff > AMOUNT_TOLERANCE:
                results.append(
                    ReconciliationResult(
                        reference_id=order.order_id,
                        category=DiscrepancyCategory.AMOUNT_MISMATCH,
                        order_amount=order.expected_amount,
                        payment_amount=payment.paid_amount,
                        currency=order.currency,
                        status=payment.status,
                        system_notes=(
                            f"Variance of {payment.paid_amount - order.expected_amount:.2f} "
                            f"(Expected: {order.expected_amount:.2f}, Paid: {payment.paid_amount:.2f})."
                        ),
                    )
                )
                continue

            results.append(
                ReconciliationResult(
                    reference_id=order.order_id,
                    category=DiscrepancyCategory.EXACT_MATCH,
                    order_amount=order.expected_amount,
                    payment_amount=payment.paid_amount,
                    currency=order.currency,
                    status=payment.status,
                    system_notes="Matched verified successfully.",
                )
            )

        for order_id, p_list in payments_by_order.items():
            if order_id not in matched_order_ids:
                for p in p_list:
                    results.append(
                        ReconciliationResult(
                            reference_id=p.transaction_id,
                            category=DiscrepancyCategory.UNMATCHED_PAYMENT,
                            order_amount=None,
                            payment_amount=p.paid_amount,
                            currency=p.currency,
                            status=p.status,
                            system_notes=f"Payment {p.transaction_id} references unknown Order {p.order_id}.",
                        )
                    )

        for p in unlinked_payments:
            results.append(
                ReconciliationResult(
                    reference_id=p.transaction_id,
                    category=DiscrepancyCategory.UNMATCHED_PAYMENT,
                    order_amount=None,
                    payment_amount=p.paid_amount,
                    currency=p.currency,
                    status=p.status,
                    system_notes=f"Payment {p.transaction_id} has no order_id reference attached.",
                )
            )

        return results
