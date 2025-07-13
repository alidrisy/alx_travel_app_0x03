#!/usr/bin/env python3
"""
Test script for Chapa Payment Integration
This script demonstrates the payment workflow using the ALX Travel App API.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def print_separator(title):
    """Print a formatted separator with title"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request and handle response"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making {method} request to {endpoint}: {e}")
        return None

def test_payment_workflow():
    """Test the complete payment workflow"""
    
    print_separator("CHAPA PAYMENT INTEGRATION TEST")
    print("This script demonstrates the payment workflow using Chapa API")
    print("Make sure the Django server is running on localhost:8000")
    print("Update the AUTH_TOKEN below with a valid authentication token")
    
    # Configuration - Update these values
    AUTH_TOKEN = "your_auth_token_here"  # Replace with actual token
    LISTING_ID = 1  # Replace with actual listing ID
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"\nUsing Listing ID: {LISTING_ID}")
    print(f"Auth Token: {AUTH_TOKEN[:10]}..." if len(AUTH_TOKEN) > 10 else "Auth Token: Not set")
    
    # Step 1: Create a booking
    print_separator("STEP 1: CREATE BOOKING")
    
    # Calculate dates (3 days from now)
    start_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
    
    booking_data = {
        "listing": LISTING_ID,
        "start_date": start_date,
        "end_date": end_date
    }
    
    print(f"Creating booking for {start_date} to {end_date}")
    booking_response = make_request("POST", "/bookings/", booking_data, headers)
    
    if not booking_response:
        print("Failed to create booking. Exiting.")
        return
    
    booking_id = booking_response.get("id")
    print(f"✅ Booking created successfully! ID: {booking_id}")
    print(f"Booking details: {json.dumps(booking_response, indent=2)}")
    
    # Step 2: Get payment details for the booking
    print_separator("STEP 2: GET PAYMENT DETAILS")
    
    payment_response = make_request("GET", f"/bookings/{booking_id}/payment_details/", headers=headers)
    
    if not payment_response:
        print("Failed to get payment details. Exiting.")
        return
    
    payment_id = payment_response.get("id")
    print(f"✅ Payment details retrieved! Payment ID: {payment_id}")
    print(f"Payment status: {payment_response.get('status')}")
    print(f"Amount: {payment_response.get('currency')} {payment_response.get('amount')}")
    print(f"Reference: {payment_response.get('reference')}")
    
    # Step 3: Initiate payment with Chapa
    print_separator("STEP 3: INITIATE PAYMENT WITH CHAPA")
    
    payment_init_data = {
        "payment_method": "card",
        "customer_phone": "+251912345678"
    }
    
    print("Initiating payment with Chapa API...")
    initiate_response = make_request("POST", f"/payments/{payment_id}/initiate_payment/", payment_init_data, headers)
    
    if not initiate_response:
        print("Failed to initiate payment. Exiting.")
        return
    
    if initiate_response.get("success"):
        print("✅ Payment initiated successfully!")
        print(f"Checkout URL: {initiate_response.get('checkout_url')}")
        print(f"Payment Reference: {initiate_response.get('reference')}")
        print("\n📝 Next steps:")
        print("1. Open the checkout URL in a browser")
        print("2. Complete the payment using Chapa's sandbox")
        print("3. Return here and run the verification step")
        
        # Store checkout URL for easy access
        checkout_url = initiate_response.get('checkout_url')
        if checkout_url:
            print(f"\n🔗 Checkout URL: {checkout_url}")
    else:
        print("❌ Payment initiation failed!")
        print(f"Error: {initiate_response.get('error')}")
        print(f"Message: {initiate_response.get('message')}")
        return
    
    # Step 4: Verify payment status
    print_separator("STEP 4: VERIFY PAYMENT STATUS")
    
    print("Verifying payment status with Chapa API...")
    print("Note: This step should be run after completing the payment in the browser")
    
    verify_response = make_request("POST", f"/payments/{payment_id}/verify_payment/", headers=headers)
    
    if not verify_response:
        print("Failed to verify payment. Exiting.")
        return
    
    if verify_response.get("success"):
        print("✅ Payment verification successful!")
        print(f"Status: {verify_response.get('status')}")
        print(f"Amount: {verify_response.get('currency')} {verify_response.get('amount')}")
        print(f"Message: {verify_response.get('message')}")
        
        if verify_response.get("status") == "completed":
            print("🎉 Payment completed successfully!")
            print("User should receive a confirmation email.")
        else:
            print(f"⚠️ Payment status: {verify_response.get('status')}")
    else:
        print("❌ Payment verification failed!")
        print(f"Error: {verify_response.get('error')}")
        print(f"Message: {verify_response.get('message')}")
    
    # Step 5: Get final payment status
    print_separator("STEP 5: GET FINAL PAYMENT STATUS")
    
    final_status = make_request("GET", f"/payments/{payment_id}/payment_status/", headers=headers)
    
    if final_status:
        print("✅ Final payment status retrieved!")
        print(f"Status: {final_status.get('status')}")
        print(f"Amount: {final_status.get('currency')} {final_status.get('amount')}")
        print(f"Reference: {final_status.get('reference')}")
        print(f"Created: {final_status.get('created_at')}")
        print(f"Updated: {final_status.get('updated_at')}")
    else:
        print("❌ Failed to get final payment status")

def test_api_endpoints():
    """Test individual API endpoints"""
    
    print_separator("API ENDPOINTS TEST")
    
    # List available endpoints
    endpoints = [
        ("GET", "/listings/", "List all listings"),
        ("GET", "/bookings/my_bookings/", "Get user's bookings"),
        ("GET", "/payments/my_payments/", "Get user's payments"),
        ("GET", "/reviews/", "List all reviews"),
    ]
    
    print("Testing basic API endpoints...")
    
    for method, endpoint, description in endpoints:
        print(f"\n{method} {endpoint} - {description}")
        response = make_request(method, endpoint)
        
        if response:
            print(f"✅ Success - Response length: {len(str(response))}")
        else:
            print("❌ Failed")

def main():
    """Main function"""
    
    print("ALX Travel App - Chapa Payment Integration Test")
    print("=" * 60)
    
    # Test basic endpoints first
    test_api_endpoints()
    
    # Test payment workflow
    test_payment_workflow()
    
    print_separator("TEST COMPLETED")
    print("Thank you for testing the Chapa Payment Integration!")
    print("\nFor more information, check the README.md file.")

if __name__ == "__main__":
    main() 