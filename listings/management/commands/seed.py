from django.core.management.base import BaseCommand
from listings.models import Listing
from django.utils.crypto import get_random_string
import random

class Command(BaseCommand):
    help = 'Seed the database with sample listings'

    def handle(self, *args, **kwargs):
        titles = [
            "Cozy Cabin in the Mountains", "Downtown Apartment", "Beachside Bungalow",
            "Luxury Villa", "Rustic Farmhouse", "Modern Studio"
        ]
        locations = ["New York", "Los Angeles", "San Francisco", "Miami", "Denver", "Austin"]

        for _ in range(20):
            Listing.objects.create(
                title=random.choice(titles),
                description=f"This is a nice place to stay. Code: {get_random_string(5)}",
                price_per_night=random.uniform(50, 500),
                location=random.choice(locations),
            )

        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded listings.'))
