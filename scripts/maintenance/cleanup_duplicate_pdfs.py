#!/usr/bin/env python3
"""
Cleanup script to remove duplicate PDF files
This script keeps only the most recent PDF for each trip request
"""

import os
import django
import re
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from home.models import TripPlanRequest, GeneratedPlan

def cleanup_duplicate_pdfs():
    """Remove duplicate PDF files and keep only one per trip"""
    
    media_path = '/Users/alireza/Desktop/trip-django/media/trip_pdfs/'
    
    if not os.path.exists(media_path):
        print("❌ PDF directory does not exist")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(media_path) if f.endswith('.pdf')]
    print(f"📂 Found {len(pdf_files)} PDF files")
    
    # Group files by trip ID
    trip_files = defaultdict(list)
    for pdf_file in pdf_files:
        # Extract trip ID from filename (e.g., trip_plan_34.pdf or trip_plan_34_xyz.pdf)
        match = re.match(r'trip_plan_(\d+)', pdf_file)
        if match:
            trip_id = int(match.group(1))
            file_path = os.path.join(media_path, pdf_file)
            file_stat = os.stat(file_path)
            trip_files[trip_id].append({
                'filename': pdf_file,
                'path': file_path,
                'size': file_stat.st_size,
                'modified': file_stat.st_mtime
            })
    
    print(f"🔍 Found PDFs for {len(trip_files)} different trips")
    
    # Statistics
    total_files = len(pdf_files)
    files_to_delete = []
    space_to_free = 0
    
    # Process each trip
    for trip_id, files in trip_files.items():
        if len(files) > 1:
            print(f"\n📋 Trip #{trip_id}: {len(files)} PDF files")
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Keep the newest file, mark others for deletion
            keep_file = files[0]
            delete_files = files[1:]
            
            print(f"   ✅ Keeping: {keep_file['filename']} ({keep_file['size']:,} bytes)")
            
            for file_info in delete_files:
                print(f"   🗑️  Delete: {file_info['filename']} ({file_info['size']:,} bytes)")
                files_to_delete.append(file_info)
                space_to_free += file_info['size']
        else:
            print(f"✅ Trip #{trip_id}: 1 PDF file (no duplicates)")
    
    # Summary
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   Total PDF files: {total_files}")
    print(f"   Files to delete: {len(files_to_delete)}")
    print(f"   Space to free: {space_to_free:,} bytes ({space_to_free/1024/1024:.1f} MB)")
    print(f"   Files to keep: {total_files - len(files_to_delete)}")
    
    if files_to_delete:
        # Ask for confirmation
        response = input(f"\n❓ Delete {len(files_to_delete)} duplicate files? (y/N): ")
        
        if response.lower() == 'y':
            deleted_count = 0
            freed_space = 0
            
            for file_info in files_to_delete:
                try:
                    os.remove(file_info['path'])
                    print(f"   🗑️  Deleted: {file_info['filename']}")
                    deleted_count += 1
                    freed_space += file_info['size']
                except Exception as e:
                    print(f"   ❌ Error deleting {file_info['filename']}: {e}")
            
            print(f"\n✅ CLEANUP COMPLETE:")
            print(f"   Deleted: {deleted_count} files")
            print(f"   Space freed: {freed_space:,} bytes ({freed_space/1024/1024:.1f} MB)")
            
            # Update database references
            update_database_references()
        else:
            print("❌ Cleanup cancelled")
    else:
        print("\n✅ No duplicate files found - nothing to clean up!")

def update_database_references():
    """Update GeneratedPlan database references to point to remaining files"""
    print(f"\n🔄 Updating database references...")
    
    updated_count = 0
    for plan in GeneratedPlan.objects.all():
        trip_id = plan.trip_request.id
        expected_filename = f"trip_pdfs/trip_plan_{trip_id}.pdf"
        
        if plan.pdf_file.name != expected_filename:
            # Check if the expected file exists
            expected_path = f"/Users/alireza/Desktop/trip-django/media/{expected_filename}"
            if os.path.exists(expected_path):
                plan.pdf_file.name = expected_filename
                plan.save()
                updated_count += 1
                print(f"   ✅ Updated Trip #{trip_id}: {plan.pdf_file.name}")
    
    print(f"🔄 Updated {updated_count} database references")

if __name__ == "__main__":
    print("🧹 PDF CLEANUP UTILITY")
    print("=" * 50)
    cleanup_duplicate_pdfs()
    print("\n🎉 Cleanup process complete!")
