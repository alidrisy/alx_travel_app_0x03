import requests
import os
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class ChapaService:
    """Service class to handle Chapa API operations"""
    
    def __init__(self):
        self.secret_key = os.getenv('CHAPA_SECRET_KEY')
        self.base_url = os.getenv('CHAPA_BASE_URL', 'https://api.chapa.co/v1')
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initialize_payment(self, payment_data):
        """
        Initialize a payment with Chapa API
        
        Args:
            payment_data (dict): Payment information including amount, email, etc.
            
        Returns:
            dict: Response from Chapa API with checkout URL and transaction reference
        """
        try:
            url = f"{self.base_url}/transaction/initialize"
            
            payload = {
                "amount": str(payment_data['amount']),
                "currency": payment_data.get('currency', 'ETB'),
                "email": payment_data['email'],
                "first_name": payment_data.get('first_name', ''),
                "last_name": payment_data.get('last_name', ''),
                "tx_ref": payment_data['reference'],
                "callback_url": payment_data.get('callback_url', ''),
                "return_url": payment_data.get('return_url', ''),
                "customization": {
                    "title": "ALX Travel App Payment",
                    "description": f"Payment for booking: {payment_data.get('booking_reference', '')}"
                }
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Payment initialized successfully: {data}")
            
            return {
                'success': True,
                'checkout_url': data.get('data', {}).get('checkout_url'),
                'transaction_ref': data.get('data', {}).get('reference'),
                'status': data.get('status'),
                'message': data.get('message')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initializing payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to initialize payment'
            }
        except Exception as e:
            logger.error(f"Unexpected error in payment initialization: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An unexpected error occurred'
            }
    
    def verify_payment(self, transaction_ref):
        """
        Verify payment status with Chapa API
        
        Args:
            transaction_ref (str): Transaction reference from Chapa
            
        Returns:
            dict: Payment verification response
        """
        try:
            url = f"{self.base_url}/transaction/verify/{transaction_ref}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Payment verification successful: {data}")
            
            return {
                'success': True,
                'status': data.get('data', {}).get('status'),
                'amount': data.get('data', {}).get('amount'),
                'currency': data.get('data', {}).get('currency'),
                'transaction_ref': data.get('data', {}).get('reference'),
                'message': data.get('message')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to verify payment'
            }
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An unexpected error occurred'
            }
    
    def get_payment_status(self, transaction_ref):
        """
        Get payment status from Chapa API
        
        Args:
            transaction_ref (str): Transaction reference from Chapa
            
        Returns:
            str: Payment status (success, pending, failed)
        """
        verification_result = self.verify_payment(transaction_ref)
        
        if verification_result['success']:
            chapa_status = verification_result.get('status', '').lower()
            
            # Map Chapa status to our payment status
            status_mapping = {
                'success': 'completed',
                'pending': 'pending',
                'failed': 'failed',
                'cancelled': 'cancelled'
            }
            
            return status_mapping.get(chapa_status, 'pending')
        
        return 'failed'


class PaymentService:
    """Service class to handle payment business logic"""
    
    def __init__(self):
        self.chapa_service = ChapaService()
    
    def create_payment_for_booking(self, booking, user):
        """
        Create a payment record for a booking
        
        Args:
            booking: Booking instance
            user: User instance
            
        Returns:
            Payment: Created payment instance
        """
        from .models import Payment
        from decimal import Decimal
        
        # Calculate total amount
        nights = (booking.end_date - booking.start_date).days
        total_amount = booking.listing.price_per_night * Decimal(nights)
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=total_amount,
            customer_email=user.email,
            customer_name=f"{user.first_name} {user.last_name}".strip() or user.username,
            status='pending'
        )
        
        return payment
    
    def initiate_payment(self, payment):
        """
        Initiate payment with Chapa API
        
        Args:
            payment: Payment instance
            
        Returns:
            dict: Payment initiation result
        """
        # Prepare payment data for Chapa
        payment_data = {
            'amount': payment.amount,
            'currency': payment.currency,
            'email': payment.customer_email,
            'reference': payment.reference,
            'first_name': payment.customer_name.split()[0] if payment.customer_name else '',
            'last_name': ' '.join(payment.customer_name.split()[1:]) if payment.customer_name and len(payment.customer_name.split()) > 1 else '',
            'booking_reference': f"BK-{payment.booking.id}",
            'callback_url': f"https://your-domain.com/api/payments/{payment.id}/verify/",
            'return_url': f"https://your-domain.com/payment/success/{payment.reference}/"
        }
        
        # Initialize payment with Chapa
        result = self.chapa_service.initialize_payment(payment_data)
        
        if result['success']:
            # Update payment with Chapa transaction reference and checkout URL
            payment.chapa_transaction_ref = result.get('transaction_ref')
            payment.checkout_url = result.get('checkout_url')
            payment.status = 'processing'
            payment.save()
            
            return {
                'success': True,
                'checkout_url': result.get('checkout_url'),
                'payment_id': payment.id,
                'reference': payment.reference
            }
        else:
            # Update payment status to failed
            payment.status = 'failed'
            payment.save()
            
            return {
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }
    
    def verify_payment_status(self, payment):
        """
        Verify payment status with Chapa API
        
        Args:
            payment: Payment instance
            
        Returns:
            dict: Payment verification result
        """
        if not payment.chapa_transaction_ref:
            return {
                'success': False,
                'error': 'No Chapa transaction reference found',
                'message': 'Payment verification failed'
            }
        
        # Verify with Chapa
        result = self.chapa_service.verify_payment(payment.chapa_transaction_ref)
        
        if result['success']:
            # Update payment status
            new_status = self.chapa_service.get_payment_status(payment.chapa_transaction_ref)
            payment.status = new_status
            payment.save()
            
            return {
                'success': True,
                'status': new_status,
                'amount': result.get('amount'),
                'currency': result.get('currency')
            }
        else:
            return {
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            } 