from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import datetime
from decimal import Decimal
from rest_framework import serializers

from .models import Listing, Booking, Review, Payment
from .serializers import (
    ListingSerializer,
    ListingDetailSerializer,
    BookingSerializer,
    BookingCreateSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentInitiateSerializer,
    PaymentVerificationSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    UserSerializer,
)
from .services import PaymentService


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Listing model with full CRUD operations.
    """

    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["location", "price_per_night"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["price_per_night", "created_at", "title"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ListingDetailSerializer
        return ListingSerializer

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """Get all reviews for a specific listing."""
        listing = self.get_object()
        reviews = listing.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific listing."""
        listing = self.get_object()
        bookings = listing.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking model with full CRUD operations.
    """

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["listing", "start_date", "end_date"]
    ordering_fields = ["start_date", "end_date", "booked_at"]
    ordering = ["-booked_at"]

    def get_queryset(self):
        """Return bookings for the authenticated user."""
        return Booking.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BookingCreateSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        """Set the user to the current authenticated user and create payment."""
        booking = serializer.save(user=self.request.user)
        
        # Create payment using PaymentService
        payment_service = PaymentService()
        payment = payment_service.create_payment_for_booking(booking, self.request.user)

    @action(detail=False, methods=["get"])
    def my_bookings(self, request):
        """Get all bookings for the current user."""
        bookings = self.get_queryset()
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def listing_details(self, request, pk=None):
        """Get details of the listing associated with this booking."""
        booking = self.get_object()
        serializer = ListingSerializer(booking.listing)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def payment_details(self, request, pk=None):
        """Get payment details for this booking."""
        booking = self.get_object()
        try:
            payment = booking.payments.first()
            if payment:
                serializer = PaymentSerializer(payment)
                return Response(serializer.data)
            else:
                return Response(
                    {"detail": "No payment found for this booking"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {"detail": "Error retrieving payment details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review model with full CRUD operations.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["listing", "rating", "user"]
    ordering_fields = ["rating", "reviewed_at"]
    ordering = ["-reviewed_at"]

    def get_queryset(self):
        """Return reviews, filtered by user if specified."""
        queryset = Review.objects.all()
        user_id = self.request.query_params.get("user", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewCreateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Set the user to the current authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_reviews(self, request):
        """Get all reviews by the current user."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def listing_details(self, request, pk=None):
        """Get details of the listing associated with this review."""
        review = self.get_object()
        serializer = ListingSerializer(review.listing)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User model (read-only).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]

    @action(detail=True, methods=["get"])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific user."""
        user = self.get_object()
        bookings = user.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """Get all reviews by a specific user."""
        user = self.get_object()
        reviews = user.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment model with full CRUD operations and Chapa integration.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["booking", "status", "payment_method"]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return payments for the authenticated user."""
        return Payment.objects.filter(booking__user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PaymentCreateSerializer
        elif self.action == "initiate_payment":
            return PaymentInitiateSerializer
        elif self.action == "verify_payment":
            return PaymentVerificationSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        """Create payment and initiate with Chapa."""
        payment = serializer.save()
        
        # Update customer information
        payment.customer_email = self.request.user.email
        payment.customer_name = f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username
        payment.save()
        
        # Initiate payment with Chapa
        payment_service = PaymentService()
        result = payment_service.initiate_payment(payment)
        
        if not result['success']:
            raise serializers.ValidationError(result.get('message', 'Payment initiation failed'))

    @action(detail=True, methods=["post"])
    def initiate_payment(self, request, pk=None):
        """Initiate payment with Chapa API."""
        payment = self.get_object()
        
        # Validate request data
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update payment with additional information
        if serializer.validated_data.get('payment_method'):
            payment.payment_method = serializer.validated_data['payment_method']
        if serializer.validated_data.get('customer_phone'):
            payment.customer_phone = serializer.validated_data['customer_phone']
        payment.save()
        
        # Initiate payment with Chapa
        payment_service = PaymentService()
        result = payment_service.initiate_payment(payment)
        
        if result['success']:
            return Response({
                'success': True,
                'checkout_url': result['checkout_url'],
                'payment_id': result['payment_id'],
                'reference': result['reference'],
                'message': 'Payment initiated successfully. Please complete payment using the checkout URL.'
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def verify_payment(self, request, pk=None):
        """Verify payment status with Chapa API."""
        payment = self.get_object()
        
        payment_service = PaymentService()
        result = payment_service.verify_payment_status(payment)
        
        if result['success']:
            return Response({
                'success': True,
                'status': result['status'],
                'amount': result.get('amount'),
                'currency': result.get('currency'),
                'message': f'Payment status: {result["status"]}'
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def my_payments(self, request):
        """Get all payments for the current user."""
        payments = self.get_queryset()
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def payment_status(self, request, pk=None):
        """Get current payment status."""
        payment = self.get_object()
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
