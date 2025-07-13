#!/usr/bin/env python
"""
Test script for Celery integration and email notifications
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from django.contrib.auth.models import User
from listings.models import Listing, Booking
from listings.tasks import send_booking_confirmation_email, debug_task
from alx_travel_app.celery import app


def test_celery_connection():
    """Test if Celery is properly configured and connected"""
    print("Testing Celery connection...")
    
    try:
        # Test the debug task
        result = debug_task.delay()
        print(f"✓ Debug task submitted successfully. Task ID: {result.id}")
        
        # Wait for the task to complete
        result.get(timeout=10)
        print("✓ Debug task completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Celery connection failed: {str(e)}")
        return False


def test_email_task():
    """Test the booking confirmation email task"""
    print("\nTesting email task...")
    
    try:
        # Create a test user if it doesn't exist
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create a test listing if it doesn't exist
        listing, created = Listing.objects.get_or_create(
            title='Test Property',
            defaults={
                'description': 'A test property for testing',
                'location': 'Test City',
                'price_per_night': 100.00,
                'owner': user
            }
        )
        
        # Create a test booking
        booking = Booking.objects.create(
            user=user,
            listing=listing,
            start_date=datetime.now().date() + timedelta(days=7),
            end_date=datetime.now().date() + timedelta(days=10)
        )
        
        print(f"✓ Created test booking with ID: {booking.id}")
        
        # Test the email task
        result = send_booking_confirmation_email.delay(booking.id)
        print(f"✓ Email task submitted successfully. Task ID: {result.id}")
        
        # Wait for the task to complete
        result.get(timeout=30)
        print("✓ Email task completed successfully")
        
        # Clean up test data
        booking.delete()
        listing.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"✗ Email task failed: {str(e)}")
        return False


def test_celery_worker_status():
    """Test if Celery worker is running and responsive"""
    print("\nTesting Celery worker status...")
    
    try:
        # Check active workers
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print("✓ Celery workers are active:")
            for worker, tasks in active_workers.items():
                print(f"  - {worker}: {len(tasks)} active tasks")
        else:
            print("⚠ No active Celery workers found")
            print("  Make sure to start the worker with: celery -A alx_travel_app worker -l info")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Failed to check worker status: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("CELERY INTEGRATION TEST")
    print("=" * 50)
    
    # Test 1: Celery connection
    connection_ok = test_celery_connection()
    
    # Test 2: Worker status
    worker_ok = test_celery_worker_status()
    
    # Test 3: Email task (only if connection is ok)
    email_ok = False
    if connection_ok and worker_ok:
        email_ok = test_email_task()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Celery Connection: {'✓ PASS' if connection_ok else '✗ FAIL'}")
    print(f"Worker Status: {'✓ PASS' if worker_ok else '✗ FAIL'}")
    print(f"Email Task: {'✓ PASS' if email_ok else '✗ FAIL'}")
    
    if connection_ok and worker_ok and email_ok:
        print("\n🎉 All tests passed! Celery integration is working correctly.")
        print("\nTo see email output, check the console where you started the Celery worker.")
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")
        print("\nTroubleshooting tips:")
        print("1. Make sure RabbitMQ is running: sudo systemctl status rabbitmq-server")
        print("2. Start Celery worker: celery -A alx_travel_app worker -l info")
        print("3. Check Django settings for Celery configuration")
        print("4. Verify email settings in settings.py")


if __name__ == "__main__":
    main() 