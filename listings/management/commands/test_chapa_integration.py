from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing, Booking, Payment
from listings.services import PaymentService, ChapaService
from decimal import Decimal
import os


class Command(BaseCommand):
    help = 'Test Chapa payment integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test listing and user data',
        )
        parser.add_argument(
            '--test-payment',
            action='store_true',
            help='Test payment initiation and verification',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Chapa Integration Test...')
        )

        if options['create_test_data']:
            self.create_test_data()

        if options['test_payment']:
            self.test_payment_integration()

    def create_test_data(self):
        """Create test data for payment testing"""
        self.stdout.write('Creating test data...')

        # Create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            self.stdout.write(f'Created test user: {user.username}')
        else:
            self.stdout.write(f'Using existing test user: {user.username}')

        # Create test listing
        listing, created = Listing.objects.get_or_create(
            title='Test Villa',
            defaults={
                'description': 'A beautiful test villa for payment testing',
                'price_per_night': Decimal('5000.00'),
                'location': 'Addis Ababa, Ethiopia'
            }
        )
        if created:
            self.stdout.write(f'Created test listing: {listing.title}')
        else:
            self.stdout.write(f'Using existing test listing: {listing.title}')

        self.stdout.write(
            self.style.SUCCESS('Test data created successfully!')
        )

    def test_payment_integration(self):
        """Test the payment integration workflow"""
        self.stdout.write('Testing payment integration...')

        # Check if Chapa API key is configured
        chapa_key = os.getenv('CHAPA_SECRET_KEY')
        if not chapa_key or chapa_key == 'your_chapa_secret_key_here':
            self.stdout.write(
                self.style.WARNING(
                    'Chapa API key not configured. Please set CHAPA_SECRET_KEY in your .env file.'
                )
            )
            return

        try:
            # Get test user and listing
            user = User.objects.get(username='testuser')
            listing = Listing.objects.get(title='Test Villa')

            # Create a test booking
            booking = Booking.objects.create(
                user=user,
                listing=listing,
                start_date='2024-02-01',
                end_date='2024-02-04'
            )
            self.stdout.write(f'Created test booking: {booking.id}')

            # Create payment using PaymentService
            payment_service = PaymentService()
            payment = payment_service.create_payment_for_booking(booking, user)
            self.stdout.write(f'Created payment: {payment.reference}')

            # Test Chapa service directly
            chapa_service = ChapaService()
            
            # Test payment initialization
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

            self.stdout.write('Testing Chapa payment initialization...')
            result = chapa_service.initialize_payment(payment_data)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Chapa payment initialization successful!')
                )
                self.stdout.write(f"Checkout URL: {result.get('checkout_url')}")
                self.stdout.write(f"Transaction Ref: {result.get('transaction_ref')}")

                # Update payment with Chapa transaction reference
                payment.chapa_transaction_ref = result.get('transaction_ref')
                payment.checkout_url = result.get('checkout_url')
                payment.status = 'processing'
                payment.save()

                # Test payment verification
                self.stdout.write('Testing Chapa payment verification...')
                verify_result = chapa_service.verify_payment(payment.chapa_transaction_ref)

                if verify_result['success']:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Chapa payment verification successful!')
                    )
                    self.stdout.write(f"Status: {verify_result.get('status')}")
                    self.stdout.write(f"Amount: {verify_result.get('amount')}")
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Chapa payment verification failed')
                    )
                    self.stdout.write(f"Error: {verify_result.get('error')}")

            else:
                self.stdout.write(
                    self.style.ERROR('❌ Chapa payment initialization failed!')
                )
                self.stdout.write(f"Error: {result.get('error')}")
                self.stdout.write(f"Message: {result.get('message')}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during payment testing: {str(e)}')
            )

        self.stdout.write(
            self.style.SUCCESS('Payment integration test completed!')
        ) 