"""PayPal Sandbox REST API Client for LedgerLens AI."""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.models import PaymentRecord, PaymentStatus

load_dotenv()

PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")


class PayPalClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        # Fallback to environment variables only if not explicitly provided
        self.client_id = CLIENT_ID if client_id is None else client_id
        self.client_secret = CLIENT_SECRET if client_secret is None else client_secret
        self.base_url = PAYPAL_BASE_URL
        self._access_token: Optional[str] = None

    def get_access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials missing. Check your .env configuration.")

        url = f"{self.base_url}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}

        response = requests.post(
            url,
            auth=(self.client_id, self.client_secret),
            headers=headers,
            data=data,
            timeout=10,
        )

        if response.status_code != 200:
            raise ConnectionError(f"PayPal Auth Failed ({response.status_code}): {response.text}")

        token_data = response.json()
        self._access_token = token_data.get("access_token")
        return self._access_token

    def create_test_sandbox_order(self, order_id: str, amount: float, currency: str = "USD") -> Dict[str, Any]:
        """Create a real sandbox order with full representation return."""
        token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Prefer": "return=representation",
        }
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": order_id,
                    "custom_id": order_id,
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                }
            ],
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code not in (200, 201):
            raise ConnectionError(f"Failed to create PayPal order: {response.text}")
        return response.json()

    def get_order_details(self, paypal_order_id: str) -> Dict[str, Any]:
        """Fetch full order details from PayPal."""
        token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{paypal_order_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to fetch PayPal order: {response.text}")
        return response.json()

    def normalize_paypal_order_to_payment_record(self, raw_order: Dict[str, Any]) -> PaymentRecord:
        """Convert PayPal JSON response into deterministic PaymentRecord model."""
        tx_id = raw_order.get("id", "UNKNOWN_TX")
        status_raw = raw_order.get("status", "FAILED")

        status_map = {
            "COMPLETED": PaymentStatus.COMPLETED,
            "APPROVED": PaymentStatus.PENDING,
            "CREATED": PaymentStatus.PENDING,
            "SAVED": PaymentStatus.PENDING,
            "VOIDED": PaymentStatus.FAILED,
        }
        status = status_map.get(status_raw, PaymentStatus.FAILED)

        purchase_units = raw_order.get("purchase_units", [])
        purchase_unit = purchase_units[0] if purchase_units else {}

        order_ref = purchase_unit.get("custom_id") or purchase_unit.get("reference_id")
        amount_info = purchase_unit.get("amount", {})
        paid_amount = float(amount_info.get("value", 0.0))
        currency = amount_info.get("currency_code", "USD")
        create_time = raw_order.get("create_time", "")

        return PaymentRecord(
            transaction_id=tx_id,
            order_id=order_ref,
            paid_amount=paid_amount,
            currency=currency,
            status=status,
            timestamp=create_time,
        )
