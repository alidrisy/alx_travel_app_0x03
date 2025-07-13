from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ListingViewSet, BookingViewSet, ReviewViewSet, UserViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
] 