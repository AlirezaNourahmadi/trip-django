from django.core.management.base import BaseCommand
from home.models import Destination

class Command(BaseCommand):
    help = 'Populate the database with sample destinations'

    def handle(self, *args, **options):
        destinations = [
            {
                'name': 'Paris',
                'country': 'France',
                'description': 'The City of Light, famous for its art, fashion, gastronomy, and culture.'
            },
            {
                'name': 'Tokyo',
                'country': 'Japan',
                'description': 'A bustling metropolis blending traditional and modern culture.'
            },
            {
                'name': 'New York',
                'country': 'United States',
                'description': 'The Big Apple, known for its skyline, Broadway, and diverse culture.'
            },
            {
                'name': 'London',
                'country': 'United Kingdom',
                'description': 'Historic city with royal palaces, museums, and modern attractions.'
            },
            {
                'name': 'Dubai',
                'country': 'United Arab Emirates',
                'description': 'Modern city known for luxury shopping, architecture, and nightlife.'
            },
            {
                'name': 'Bali',
                'country': 'Indonesia',
                'description': 'Tropical paradise known for beaches, temples, and volcanic landscapes.'
            },
            {
                'name': 'Rome',
                'country': 'Italy',
                'description': 'Eternal City with ancient ruins, Vatican City, and Italian cuisine.'
            },
            {
                'name': 'Barcelona',
                'country': 'Spain',
                'description': 'Vibrant city known for Gaudi architecture, beaches, and culture.'
            }
        ]

        for dest_data in destinations:
            destination, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                country=dest_data['country'],
                defaults={'description': dest_data['description']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created destination: {destination.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Destination already exists: {destination.name}')
                )
