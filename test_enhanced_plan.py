#!/usr/bin/env python
"""
Test script for enhanced trip plan generation
"""
import os
import sys
import django
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce log noise

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from home.models import TripPlanRequest
from home.services import ai_service

def test_enhanced_plan_generation():
    """Test the enhanced trip plan generation functionality"""
    print('Testing enhanced trip plan generation...')
    
    # Get trip request 38
    try:
        trip = TripPlanRequest.objects.get(id=38)
        print(f'Trip: {trip.destination}, {trip.duration} days, {trip.number_of_travelers} travelers, ${trip.budget}')
        
        # Generate initial plan
        print('1. Generating initial plan...')
        initial_plan = ai_service.generate_trip_plan(trip)
        print(f'   Initial plan length: {len(initial_plan)} characters')
        
        # Generate enhanced plan
        print('2. Generating enhanced plan...')
        enhanced_plan = ai_service.generate_enhanced_response(
            initial_plan=initial_plan,
            user=None,  # No user context for this test
            destination=trip.destination,
            number_of_travelers=trip.number_of_travelers
        )
        print(f'   Enhanced plan length: {len(enhanced_plan)} characters')
        
        # Show preview of enhanced plan
        print('3. Enhanced plan preview:')
        print(enhanced_plan[:500])
        print('...')
        
        # Test PDF generation with enhanced plan
        print('4. Testing PDF generation...')
        from home.services import generate_trip_plan_pdf
        pdf_file = generate_trip_plan_pdf(enhanced_plan, trip.destination)
        
        if pdf_file:
            # Save test PDF
            with open('test_enhanced_trip_plan.pdf', 'wb') as f:
                f.write(pdf_file.read())
            
            file_size = os.path.getsize('test_enhanced_trip_plan.pdf')
            print(f'   PDF generated: {file_size:,} bytes')
            
            if file_size > 50000:
                print('   ✅ PDF appears to contain images (large file size)')
            else:
                print('   ⚠️ PDF might not contain images (small file size)')
        else:
            print('   ❌ PDF generation failed')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_plan_generation()
