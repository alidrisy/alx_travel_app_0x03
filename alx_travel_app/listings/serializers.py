from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'price_per_night', 'location', 'created_at']
        read_only_fields = ['created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'listing', 'user', 'rating', 'comment', 'reviewed_at']
        read_only_fields = ['reviewed_at', 'user', 'listing']

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = ['id', 'listing', 'user', 'start_date', 'end_date', 'booked_at']
        read_only_fields = ['booked_at', 'user']

class ListingDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)
    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'price_per_night', 'location', 'created_at', 'reviews', 'bookings']
        read_only_fields = ['created_at']

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'start_date', 'end_date']

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['listing', 'rating', 'comment'] 