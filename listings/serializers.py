from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Payment, Review


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price_per_night",
            "location",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "listing", "user", "rating", "comment", "reviewed_at"]
        read_only_fields = ["reviewed_at", "user", "listing"]


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "listing", "user", "start_date", "end_date", "booked_at"]
        read_only_fields = ["booked_at", "user"]


class ListingDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price_per_night",
            "location",
            "created_at",
            "reviews",
            "bookings",
        ]
        read_only_fields = ["created_at"]


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["listing", "start_date", "end_date"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["listing", "rating", "comment"]


class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            "id", 
            "reference",
            "booking", 
            "amount", 
            "currency",
            "status", 
            "payment_method",
            "transaction_id", 
            "chapa_transaction_ref",
            "checkout_url",
            "customer_email",
            "customer_name",
            "customer_phone",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "reference", 
            "transaction_id", 
            "chapa_transaction_ref",
            "checkout_url",
            "created_at",
            "updated_at"
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["booking", "amount", "currency", "payment_method"]


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating payment with Chapa"""
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        required=False
    )
    customer_phone = serializers.CharField(max_length=20, required=False)


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification response"""
    success = serializers.BooleanField()
    status = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    error = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
