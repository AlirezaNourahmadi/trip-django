from django.core.management.base import BaseCommand
from home.models import TripPlanRequest, GeneratedPlan
from home.optimized_services import generate_clean_pdf
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Regenerate PDF for a specific trip plan with enhanced styling'
    
    def add_arguments(self, parser):
        parser.add_argument('trip_id', type=int, help='Trip plan request ID')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if PDF already exists'
        )
    
    def handle(self, *args, **options):
        trip_id = options['trip_id']
        force = options['force']
        
        try:
            trip_request = TripPlanRequest.objects.get(id=trip_id)
            self.stdout.write(f"Found trip request: {trip_request.destination}")
            
            try:
                plan = trip_request.generated_plan
                if not plan.content:
                    self.stdout.write(self.style.ERROR('No trip plan content found'))
                    return
                
                # Check if PDF already exists
                if plan.pdf_file and not force:
                    self.stdout.write(self.style.WARNING('PDF already exists. Use --force to regenerate'))
                    return
                
                self.stdout.write('Generating enhanced PDF...')
                
                # Generate new PDF with enhanced styling
                pdf_content = generate_clean_pdf(plan.content, trip_request.destination)
                
                # Save the PDF
                pdf_filename = f"trip_plan_{trip_id}_enhanced.pdf"
                plan.pdf_file.save(pdf_filename, pdf_content, save=True)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully regenerated PDF for trip {trip_id}'
                    )
                )
                self.stdout.write(f'PDF size: {plan.pdf_file.size} bytes')
                
            except GeneratedPlan.DoesNotExist:
                self.stdout.write(self.style.ERROR('No generated plan found for this trip'))
                
        except TripPlanRequest.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Trip request with ID {trip_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
