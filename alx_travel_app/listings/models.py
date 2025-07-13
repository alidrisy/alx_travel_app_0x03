from django.db import models
from django.contrib.auth.models import User
import uuid


class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Booking(models.Model):
    listing = models.ForeignKey(
        Listing, related_name="bookings", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name="bookings", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} booked {self.listing.title}"


class Review(models.Model):
    listing = models.ForeignKey(
        Listing, related_name="reviews", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} rated {self.listing.title} - {self.rating}/5"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    booking = models.ForeignKey(
        Booking, related_name="payments", on_delete=models.CASCADE
    )
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ETB')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    chapa_transaction_ref = models.CharField(max_length=255, blank=True, null=True)
    checkout_url = models.URLField(blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.reference} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(uuid.uuid4())
        super().save(*args, **kwargs)
