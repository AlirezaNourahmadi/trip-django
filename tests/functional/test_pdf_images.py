#!/usr/bin/env python
"""
Test script for PDF generation with images
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from home.services import generate_trip_plan_pdf

def test_pdf_with_images():
    """Test PDF generation with locations that should have images"""
    
    # Sample trip plan with recognizable locations that should have photos
    trip_plan_text = """🌟 Amazing Trip to Paris

🗓️ Day 1: Arrival and Exploration
📍 Visit Eiffel Tower
🏨 Check into hotel near Louvre Museum
🍽️ Dinner at local restaurant
💰 Estimated cost: $120

🗓️ Day 2: Cultural Experience  
🎨 Visit Louvre Museum in the morning
📍 Explore Notre-Dame Cathedral
🍕 Lunch at local café
📍 Walk around Arc de Triomphe
⏰ Best time: Morning to avoid crowds
💰 Estimated cost: $80

🗓️ Day 3: Final Day
📍 Visit Sacré-Cœur Basilica
🍽️ Farewell dinner
💰 Estimated cost: $90

💡 Tips: Book tickets in advance for major attractions
"""
    
    print("Testing PDF generation with images...")
    print("Sample trip plan includes locations: Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, Arc de Triomphe, Sacré-Cœur Basilica")
    
    try:
        # Generate PDF
        pdf_file = generate_trip_plan_pdf(trip_plan_text, "Paris")
        
        if pdf_file:
            # Save the PDF to check it
            output_path = "test_trip_plan_with_images.pdf"
            with open(output_path, 'wb') as f:
                f.write(pdf_file.read())
            
            file_size = os.path.getsize(output_path)
            print(f"✅ PDF generated successfully!")
            print(f"📁 File saved as: {output_path}")
            print(f"📏 File size: {file_size:,} bytes")
            
            if file_size > 50000:  # If file is larger than 50KB, likely has images
                print("🖼️ PDF appears to contain images (file size > 50KB)")
            else:
                print("⚠️ PDF might not contain images (file size < 50KB)")
                
        else:
            print("❌ PDF generation failed")
            
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_with_images()
