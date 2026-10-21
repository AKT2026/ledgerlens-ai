"""AI-Assisted Investigation Module for LedgerLens AI using Google Gemini."""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class InvestigationReport(BaseModel):
    root_cause_analysis: str = Field(
        description="Concise, plain-English explanation of why this financial discrepancy occurred from a merchant/banking operations perspective."
    )
    operational_risk: str = Field(
        description="Risk level evaluation: LOW, MEDIUM, or HIGH."
    )
    recommended_actions: List[str] = Field(
        description="Step-by-step checklist for the merchant operations team."
    )
    suggested_audit_status: str = Field(
        description="Suggested disposition: PENDING_REVIEW, RESOLVED, ESCALATED_PAYPAL, or WRITTEN_OFF."
    )


class AIExplainer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = GEMINI_API_KEY if api_key is None else api_key

    def investigate(self, discrepancy_data: Dict[str, Any]) -> InvestigationReport:
        """Analyze a deterministic discrepancy record and generate an auditable investigation report."""
        if not self.api_key or self.api_key.startswith("your_"):
            return self._generate_heuristic_fallback(discrepancy_data)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            system_instruction = (
                "You are an expert financial auditor and merchant payment operations analyst for LedgerLens AI. "
                "Analyze the provided deterministic reconciliation finding. Do not dispute the numbers. "
                "Explain the operational root cause (e.g. processor fees, timing lags, duplicate triggers, checkout abandonment) "
                "and recommend concrete next steps for human sign-off."
            )

            prompt = (
                f"Discrepancy Category: {discrepancy_data.get('category')}\n"
                f"Reference ID: {discrepancy_data.get('reference_id')}\n"
                f"Expected Order Amount: ${discrepancy_data.get('order_amount')}\n"
                f"Settled Payment Amount: ${discrepancy_data.get('payment_amount')}\n"
                f"Variance: ${discrepancy_data.get('variance')}\n"
                f"Processor Gateway Status: {discrepancy_data.get('status')}\n"
                f"Deterministic Engine Notes: {discrepancy_data.get('system_notes')}\n"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=InvestigationReport,
                    temperature=0.2,
                ),
            )

            parsed = json.loads(response.text)
            return InvestigationReport(**parsed)

        except Exception as e:
            fallback = self._generate_heuristic_fallback(discrepancy_data)
            fallback.root_cause_analysis += f" (Note: Gemini API unavailable ({e}); rule-based synthesis used.)"
            return fallback

    def _generate_heuristic_fallback(self, data: Dict[str, Any]) -> InvestigationReport:
        """Deterministic operational heuristic used when API is offline."""
        cat = data.get("category", "")
        variance = data.get("variance", 0.0)
        ref = data.get("reference_id", "")

        if cat == "AMOUNT_MISMATCH":
            return InvestigationReport(
                root_cause_analysis=(
                    f"Variance of ${variance:+.2f} detected on Reference {ref}. "
                    "Typically caused by untracked merchant service fees, partial refunds, or unrecorded promotional discounts."
                ),
                operational_risk="MEDIUM",
                recommended_actions=[
                    "Check PayPal capture breakdown for unrecorded gateway processing fees.",
                    "Verify if a customer promo code or partial credit was applied post-checkout.",
                    "If fees explain the difference, post an adjusting journal entry to Transaction Fees Expense.",
                ],
                suggested_audit_status="PENDING_REVIEW",
            )
        elif cat == "DUPLICATE_PAYMENT":
            return InvestigationReport(
                root_cause_analysis=(
                    f"Multiple transaction authorizations detected for Order {ref}. "
                    "Typically occurs when a customer double-clicks checkout or network timeout triggers an automatic retry."
                ),
                operational_risk="HIGH",
                recommended_actions=[
                    "Check customer account to confirm only one physical fulfillment order exists.",
                    "Verify both transaction capture IDs directly in PayPal Sandbox dashboard.",
                    "Void authorization or initiate partial refund on duplicate capture to prevent chargeback.",
                ],
                suggested_audit_status="ESCALATED_PAYPAL",
            )
        elif cat == "STATUS_PENDING":
            return InvestigationReport(
                root_cause_analysis=(
                    f"Payment for {ref} is currently in PENDING state. "
                    "Funds have been authorized but not yet captured by the processor settlement batch."
                ),
                operational_risk="LOW",
                recommended_actions=[
                    "Do not ship high-value physical goods until status transitions to COMPLETED.",
                    "Re-query PayPal order capture endpoint in 6 to 12 hours.",
                ],
                suggested_audit_status="PENDING_REVIEW",
            )
        elif cat == "STATUS_FAILED":
            return InvestigationReport(
                root_cause_analysis=(
                    f"Payment for {ref} was declined or failed at processor gateway. Order is uncollectible."
                ),
                operational_risk="HIGH",
                recommended_actions=[
                    "Cancel pending order fulfillment immediately to prevent merchandise loss.",
                    "Notify customer of failed billing with a checkout retry link.",
                ],
                suggested_audit_status="RESOLVED",
            )
        elif cat == "UNMATCHED_ORDER":
            return InvestigationReport(
                root_cause_analysis=(
                    f"Order {ref} exists internally but has no corresponding payment authorization. Customer likely dropped off at checkout."
                ),
                operational_risk="LOW",
                recommended_actions=[
                    "Verify if checkout session expired before card entry.",
                    "Send automated abandoned cart notification if contact details are present.",
                ],
                suggested_audit_status="RESOLVED",
            )
        else:
            return InvestigationReport(
                root_cause_analysis=f"Unlinked transaction detected ({ref}). Funds captured without registered order reference.",
                operational_risk="HIGH",
                recommended_actions=[
                    "Perform manual trace in merchant POS / backend to identify missing cart session.",
                    "Hold funds in suspense account pending customer claim.",
                ],
                suggested_audit_status="ESCALATED_PAYPAL",
            )
