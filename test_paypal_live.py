"""Manual verification script for PayPal Sandbox integration."""

import os
from dotenv import load_dotenv
from src.paypal_client import PayPalClient

load_dotenv()

def verify_paypal():
    print("=" * 65)
    print("  LEDGERLENS AI -- PAYPAL SANDBOX CONNECTIVITY TEST")
    print("=" * 65)

    client_id = os.getenv("PAYPAL_CLIENT_ID")
    if not client_id or "copied_client_id" in client_id:
        print("[ERROR] Please enter your real Sandbox credentials in .env first.")
        return

    try:
        client = PayPalClient()
        print("1. Requesting OAuth2 Bearer Token...")
        token = client.get_access_token()
        print(f"   [SUCCESS] Bearer Token generated (first 15 chars: {token[:15]}...)")

        print("\n2. Creating a live test Sandbox Order for 'ORD-LIVE-777' ($199.99)...")
        order_data = client.create_test_sandbox_order("ORD-LIVE-777", 199.99, "USD")
        paypal_id = order_data["id"]
        status = order_data["status"]
        print(f"   [SUCCESS] Live PayPal Order ID: {paypal_id} | Status: {status}")

        print("\n3. Converting to normalized LedgerLens PaymentRecord...")
        record = client.normalize_paypal_order_to_payment_record(order_data)
        print(f"   Record Parsed: ID={record.transaction_id}, Ref={record.order_id}, Amt=${record.paid_amount:.2f}, Status={record.status.value}")

        print("\n[RESULT] PayPal Sandbox API integration is verified and live.")
        print("=" * 65)

    except Exception as e:
        print(f"\n[FAILURE] {e}")

if __name__ == "__main__":
    verify_paypal()
