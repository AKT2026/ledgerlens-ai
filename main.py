"""Console entrypoint for LedgerLens AI Phase 1 verification."""

from src.engine import ReconciliationEngine
from src.synthetic_data import generate_sample_dataset


def run_reconciliation():
    print("=" * 70)
    print("  LEDGERLENS AI -- DETERMINISTIC RECONCILIATION ENGINE (PHASE 1)")
    print("=" * 70)

    orders, payments = generate_sample_dataset()
    print(f"Loaded {len(orders)} internal orders and {len(payments)} processor payments.\n")

    engine = ReconciliationEngine()
    results = engine.reconcile(orders, payments)

    header = f"{'REF ID':<16} | {'CATEGORY':<20} | {'ORDER':<8} | {'PAID':<8} | {'STATUS':<10}"
    print(header)
    print("-" * len(header))

    for r in results:
        o_val = f"{r.order_amount:.2f}" if r.order_amount is not None else "-"
        p_val = f"{r.payment_amount:.2f}" if r.payment_amount is not None else "-"
        st = r.status.value if r.status else "-"
        print(f"{r.reference_id:<16} | {r.category.value:<20} | {o_val:<8} | {p_val:<8} | {st:<10}")

    print("\n[Audit Trace Summary]")
    for r in results:
        if r.category.value != "EXACT_MATCH":
            print(f"- [{r.category.value}] Ref: {r.reference_id} -> {r.system_notes}")

    print("=" * 70)
    print("Execution complete: 0 unhandled exceptions.")


if __name__ == "__main__":
    run_reconciliation()
