import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models after Django setup
from files.models import File, FileReference

# Print all files
print("\n=== Files in Database ===")
for file in File.objects.all():
    print(f"ID: {file.id}")
    print(f"Filename: {file.original_filename}")
    print(f"Hash: {file.file_hash}")
    print(f"Is Duplicate: {file.is_duplicate}")
    print(f"Size: {file.size} bytes")
    print(f"Type: {file.file_type}")
    print("-" * 50)

# Print file references (duplicates)
print("\n=== File References (Duplicates) ===")
for ref in FileReference.objects.all():
    print(f"Original file: {ref.original_file.original_filename} ({ref.original_file.id})")
    print(f"Duplicate file: {ref.reference_file.original_filename} ({ref.reference_file.id})")
    print("-" * 50)

# Print stats
total_files = File.objects.count()
duplicate_files = File.objects.filter(is_duplicate=True).count()
unique_files = total_files - duplicate_files

# Calculate storage
physical_storage = File.objects.filter(is_duplicate=False).aggregate(total=django.db.models.Sum('size'))['total'] or 0
logical_storage = File.objects.aggregate(total=django.db.models.Sum('size'))['total'] or 0
storage_saved = logical_storage - physical_storage

print("\n=== Stats ===")
print(f"Total files: {total_files}")
print(f"Unique files: {unique_files}")
print(f"Duplicate files: {duplicate_files}")
print(f"Physical storage: {physical_storage} bytes")
print(f"Logical storage: {logical_storage} bytes")
print(f"Storage saved: {storage_saved} bytes")
print(f"Storage saved percentage: {round((storage_saved / logical_storage * 100) if logical_storage > 0 else 0, 2)}%") 