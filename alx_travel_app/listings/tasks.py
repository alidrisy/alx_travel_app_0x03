from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_payment_confirmation_email(payment_id):
    """
    Send payment confirmation email to user
    
    Args:
        payment_id (int): ID of the payment record
    """
    try:
        from .models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        user = payment.booking.user
        listing = payment.booking.listing
        
        # Email subject and content
        subject = f'Payment Confirmation - {listing.title}'
        
        # HTML content
        html_message = render_to_string('listings/email/payment_confirmation.html', {
            'user': user,
            'payment': payment,
            'booking': payment.booking,
            'listing': listing,
        })
        
        # Plain text content
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent to {user.email} for payment {payment.reference}")
        
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
    except Exception as e:
        logger.error(f"Error sending payment confirmation email: {str(e)}")


@shared_task
def send_booking_confirmation_email(booking_id):
    """
    Send booking confirmation email to user
    
    Args:
        booking_id (int): ID of the booking record
    """
    try:
        from .models import Booking
        
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        listing = booking.listing
        
        # Email subject and content
        subject = f'Booking Confirmation - {listing.title}'
        
        # HTML content
        html_message = render_to_string('listings/email/booking_confirmation.html', {
            'user': user,
            'booking': booking,
            'listing': listing,
        })
        
        # Plain text content
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Booking confirmation email sent to {user.email} for booking {booking.id}")
        
    except Booking.DoesNotExist:
        logger.error(f"Booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Error sending booking confirmation email: {str(e)}")


@shared_task
def send_payment_failed_email(payment_id):
    """
    Send payment failed notification email to user
    
    Args:
        payment_id (int): ID of the payment record
    """
    try:
        from .models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        user = payment.booking.user
        listing = payment.booking.listing
        
        # Email subject and content
        subject = f'Payment Failed - {listing.title}'
        
        # HTML content
        html_message = render_to_string('listings/email/payment_failed.html', {
            'user': user,
            'payment': payment,
            'booking': payment.booking,
            'listing': listing,
        })
        
        # Plain text content
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment failed email sent to {user.email} for payment {payment.reference}")
        
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
    except Exception as e:
        logger.error(f"Error sending payment failed email: {str(e)}")


@shared_task
def update_payment_status(payment_id):
    """
    Update payment status by verifying with Chapa API
    
    Args:
        payment_id (int): ID of the payment record
    """
    try:
        from .models import Payment
        from .services import PaymentService
        
        payment = Payment.objects.get(id=payment_id)
        payment_service = PaymentService()
        
        # Verify payment status
        result = payment_service.verify_payment_status(payment)
        
        if result['success']:
            logger.info(f"Payment status updated for payment {payment.reference}: {result['status']}")
            
            # Send confirmation email if payment is completed
            if result['status'] == 'completed':
                send_payment_confirmation_email.delay(payment_id)
            elif result['status'] == 'failed':
                send_payment_failed_email.delay(payment_id)
        else:
            logger.error(f"Failed to update payment status for payment {payment.reference}: {result.get('error')}")
            
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")


@shared_task
def cleanup_expired_payments():
    """
    Clean up payments that have been pending for too long
    """
    try:
        from .models import Payment
        from django.utils import timezone
        from datetime import timedelta
        
        # Find payments that have been pending for more than 24 hours
        cutoff_time = timezone.now() - timedelta(hours=24)
        expired_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        # Update status to failed
        expired_payments.update(status='failed')
        
        logger.info(f"Cleaned up {expired_payments.count()} expired payments")
        
    except Exception as e:
        logger.error(f"Error cleaning up expired payments: {str(e)}") 