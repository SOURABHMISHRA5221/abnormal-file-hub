import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models and utilities after Django setup
from files.models import File, FileReference
from files.utils import rebuild_file_references, verify_duplicates, calculate_storage_stats

def main():
    print("=== Starting deduplication fix ===")
    
    # Step 1: Rebuild file references from scratch
    print("\n=== Rebuilding file references ===")
    results = rebuild_file_references()
    print(f"Total files: {results['total_files']}")
    print(f"Unique files: {results['unique_files']}")
    print(f"Duplicate files: {results['duplicate_files']}")
    
    # Step 2: Verify and fix any inconsistencies
    print("\n=== Verifying duplicates and fixing inconsistencies ===")
    fix_results = verify_duplicates()
    print(f"Fixed {fix_results['fixed_count']} inconsistencies")
    print(f"Current duplicates: {fix_results['current_duplicates']}")
    print(f"Current references: {fix_results['current_references']}")
    
    # Step 3: Calculate and display storage statistics
    print("\n=== Updated Stats ===")
    stats = calculate_storage_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Unique files: {stats['unique_files']}")
    print(f"Duplicate files: {stats['duplicate_files']}")
    print(f"Physical storage: {stats['physical_storage_bytes']} bytes")
    print(f"Logical storage: {stats['logical_storage_bytes']} bytes")
    print(f"Storage saved: {stats['storage_saved_bytes']} bytes")
    print(f"Storage saved percentage: {stats['storage_saved_percentage']}%")
    
    # Print final state of files for debugging if needed
    if '--verbose' in sys.argv:
        print("\n=== Final File States ===")
        for file in File.objects.all().order_by('file_hash', '-uploaded_at'):
            print(f"ID: {file.id}")
            print(f"Filename: {file.original_filename}")
            print(f"Hash: {file.file_hash}")
            print(f"Is Duplicate: {file.is_duplicate}")
            print("-" * 50)
        
        print("\n=== File References ===")
        for ref in FileReference.objects.all():
            print(f"Original file: {ref.original_file.original_filename} ({ref.original_file.id})")
            print(f"Duplicate file: {ref.reference_file.original_filename} ({ref.reference_file.id})")
            print("-" * 50)

if __name__ == "__main__":
    main() 