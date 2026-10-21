"""LedgerLens AI - Streamlit Exception Review Dashboard with AI Co-Pilot."""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.engine import ReconciliationEngine
from src.synthetic_data import generate_sample_dataset
from src.models import OrderRecord
from src.paypal_client import PayPalClient
from src.ai_explainer import AIExplainer
from src.db import init_db, save_reconciliation_results, get_all_reviews, update_review_status

st.set_page_config(
    page_title="LedgerLens AI | Audit Dashboard",
    page_icon="🔍",
    layout="wide",
)

init_db()

st.title("🔍 LedgerLens AI")
st.caption("Deterministic Payment Reconciliation & Exception Triage Copilot")

with st.sidebar:
    st.header("Reconciliation Controls")
    
    if st.button("📊 Run Benchmark Reconciliation", use_container_width=True):
        orders, payments = generate_sample_dataset()
        engine = ReconciliationEngine()
        results = engine.reconcile(orders, payments)
        save_reconciliation_results(results)
        st.success(f"Reconciled {len(orders)} orders and {len(payments)} payments.")

    st.markdown("---")
    st.header("Live Gateway Sync")
    st.caption("Test live PayPal Sandbox REST API order creation and state ingestion.")
    
    live_amt = st.number_input("Test Order Amount ($)", min_value=1.0, value=149.99, step=10.0)
    
    if st.button("⚡ Create & Sync Live PayPal Order", use_container_width=True):
        try:
            with st.spinner("Calling PayPal Sandbox API..."):
                client = PayPalClient()
                order_ref = f"ORD-LIVE-{datetime.now().strftime('%H%M%S')}"
                
                paypal_raw = client.create_test_sandbox_order(order_ref, live_amt)
                live_payment = client.normalize_paypal_order_to_payment_record(paypal_raw)
                
                internal_order = OrderRecord(
                    order_id=order_ref,
                    expected_amount=live_amt,
                    currency="USD",
                    customer_id="CUST-SANDBOX-LIVE",
                    created_at=datetime.utcnow().isoformat() + "Z",
                )
                
                engine = ReconciliationEngine()
                results = engine.reconcile([internal_order], [live_payment])
                save_reconciliation_results(results)
                
                st.success(f"Created Live PayPal Order `{live_payment.transaction_id}` (Status: {live_payment.status.value})")
                st.rerun()
        except Exception as e:
            st.error(f"PayPal Gateway Error: {e}")

    st.markdown("---")
    st.markdown("### System Architecture")
    st.markdown("- **Core Engine**: Pure Deterministic Rules")
    st.markdown("- **Audit Log**: SQLite Local Store")
    st.markdown("- **Gateway**: PayPal Sandbox REST API")
    st.markdown("- **AI Explainer**: Google Gemini Pro (Grounded Layer)")

records = get_all_reviews()

if not records:
    st.info("No audit records found. Click **'Run Benchmark Reconciliation'** or **'Create & Sync Live PayPal Order'** in the sidebar.")
else:
    df = pd.DataFrame(records)

    # 1. Top KPI Summary Cards
    total_records = len(df)
    exact_matches = len(df[df["category"] == "EXACT_MATCH"])
    exceptions = total_records - exact_matches
    match_rate = (exact_matches / total_records * 100) if total_records > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Transactions", total_records)
    col2.metric("Exact Matches", exact_matches)
    col3.metric("Exceptions Flagged", exceptions, delta=f"-{exceptions}" if exceptions > 0 else "0", delta_color="inverse")
    col4.metric("Clean Match Rate", f"{match_rate:.1f}%")

    st.markdown("---")

    # 2. Filterable Exception Queue
    st.subheader("Discrepancy & Audit Queue")

    col_filter1, col_filter2 = st.columns([1, 1])
    with col_filter1:
        category_options = ["ALL"] + sorted(list(df["category"].unique()))
        selected_category = st.selectbox("Filter by Category", category_options)
    with col_filter2:
        status_options = ["ALL", "PENDING_REVIEW", "RESOLVED", "ESCALATED_PAYPAL", "WRITTEN_OFF"]
        selected_review_status = st.selectbox("Filter by Review Status", status_options)

    filtered_df = df.copy()
    if selected_category != "ALL":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
    if selected_review_status != "ALL":
        filtered_df = filtered_df[filtered_df["review_status"] == selected_review_status]

    display_cols = ["reference_id", "category", "order_amount", "payment_amount", "variance", "status", "review_status"]
    
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "reference_id": "Reference ID",
            "category": "Classification",
            "order_amount": st.column_config.NumberColumn("Expected Order", format="$%.2f"),
            "payment_amount": st.column_config.NumberColumn("Settled Payment", format="$%.2f"),
            "variance": st.column_config.NumberColumn("Variance", format="$%+.2f"),
            "status": "Processor Status",
            "review_status": "Audit Disposition",
        },
        use_container_width=True,
        hide_index=True,
    )
    
    # NEW: CSV Export for Finance Teams
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Audit Report (CSV)",
        data=csv_data,
        file_name=f"ledgerlens_audit_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # 3. Investigation & Action Workspace
    st.subheader("Exception Investigation & Human Disposition")

    non_match_df = df[df["category"] != "EXACT_MATCH"]
    if non_match_df.empty:
        st.success("All transactions are cleanly matched. No active exceptions to review.")
    else:
        selected_ref = st.selectbox(
            "Select an Exception Reference to Investigate:",
            non_match_df["reference_id"].tolist(),
        )

        selected_row = non_match_df[non_match_df["reference_id"] == selected_ref].iloc[0]

        detail_col1, detail_col2 = st.columns([3, 2])

        with detail_col1:
            st.markdown(f"#### Factual Evidence: `{selected_row['reference_id']}`")
            st.info(f"**Deterministic Finding**: {selected_row['system_notes']}")

            f_col1, f_col2, f_col3 = st.columns(3)
            o_text = f"${selected_row['order_amount']:.2f}" if pd.notnull(selected_row['order_amount']) else "None"
            p_text = f"${selected_row['payment_amount']:.2f}" if pd.notnull(selected_row['payment_amount']) else "None"
            f_col1.write(f"**Expected Order**: {o_text}")
            f_col2.write(f"**Settled Payment**: {p_text}")
            f_col3.write(f"**Variance**: ${selected_row['variance']:+.2f}")

            st.write(f"**Processor Status**: `{selected_row['status']}`")

            st.markdown("---")
            st.markdown("#### 🤖 AI Investigation Co-Pilot (Grounded Gemini Layer)")
            st.caption("Synthesizes deterministic facts into banking root-cause analysis and operational actions.")

            if st.button("Generate Root-Cause Analysis", key=f"ai_btn_{selected_ref}", use_container_width=True):
                with st.spinner("Analyzing with Gemini Co-Pilot..."):
                    explainer = AIExplainer()
                    report = explainer.investigate(dict(selected_row))
                    st.session_state[f"ai_report_{selected_ref}"] = report

            if f"ai_report_{selected_ref}" in st.session_state:
                report = st.session_state[f"ai_report_{selected_ref}"]

                risk_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                st.markdown(f"**Operational Risk**: {risk_colors.get(report.operational_risk, '⚪')} `{report.operational_risk}`")
                st.write(f"**Analysis**: {report.root_cause_analysis}")

                st.markdown("**Actionable Checklist:**")
                for act in report.recommended_actions:
                    st.markdown(f"- [ ] {act}")

        with detail_col2:
            st.markdown("#### Human Review Decision")
            with st.form(key=f"review_form_{selected_ref}"):
                current_status = selected_row["review_status"] if selected_row["review_status"] in ["PENDING_REVIEW", "RESOLVED", "ESCALATED_PAYPAL", "WRITTEN_OFF"] else "PENDING_REVIEW"
                new_status = st.selectbox(
                    "Review Disposition",
                    ["PENDING_REVIEW", "RESOLVED", "ESCALATED_PAYPAL", "WRITTEN_OFF"],
                    index=["PENDING_REVIEW", "RESOLVED", "ESCALATED_PAYPAL", "WRITTEN_OFF"].index(current_status),
                )
                reviewer_notes = st.text_area(
                    "Audit Log Notes",
                    value=selected_row["reviewer_notes"] or "",
                    placeholder="Document root cause, settlement adjustment, or customer outreach...",
                    height=140,
                )
                submitted = st.form_submit_button("Save Audit Disposition", use_container_width=True)
                if submitted:
                    update_review_status(selected_ref, new_status, reviewer_notes)
                    st.success(f"Audit record saved for {selected_ref}!")
                    st.rerun()
