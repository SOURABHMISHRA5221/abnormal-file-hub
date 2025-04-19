import os
import django
import hashlib

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models after Django setup
from files.models import File, FileReference

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file contents"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read and update in chunks for memory efficiency
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

# Print initial state
print("\n=== Before Update ===")
for file in File.objects.all():
    print(f"ID: {file.id}")
    print(f"Filename: {file.original_filename}")
    print(f"Hash: {file.file_hash}")
    print("-" * 50)

# Update file hashes
print("\n=== Updating Hashes ===")
for file in File.objects.all():
    # Get the full path to the file
    file_path = os.path.join('media', file.file.name)
    
    if os.path.exists(file_path):
        # Calculate the hash
        file_hash = calculate_file_hash(file_path)
        print(f"Calculated hash for {file.original_filename}: {file_hash}")
        
        # Update the file
        file.file_hash = file_hash
        file.save(update_fields=['file_hash'])
        print(f"Updated hash for {file.original_filename}")
    else:
        print(f"WARNING: File not found at {file_path}")

# Print updated state
print("\n=== After Update ===")
for file in File.objects.all():
    print(f"ID: {file.id}")
    print(f"Filename: {file.original_filename}")
    print(f"Hash: {file.file_hash}")
    print("-" * 50)

# Check for duplicates after fixing hashes
print("\n=== Checking for Duplicates ===")
hashes = {}
for file in File.objects.all():
    if file.file_hash:
        if file.file_hash in hashes:
            original_file = hashes[file.file_hash]
            print(f"Found duplicate: {file.original_filename} is a duplicate of {original_file.original_filename}")
            
            # Mark as duplicate if not already
            if not file.is_duplicate:
                file.is_duplicate = True
                file.save(update_fields=['is_duplicate'])
                
                # Create reference if it doesn't exist
                if not FileReference.objects.filter(reference_file=file).exists():
                    FileReference.objects.create(
                        original_file=original_file,
                        reference_file=file
                    )
                    print(f"Created reference: {file.original_filename} -> {original_file.original_filename}")
        else:
            # Only store non-duplicate files as potential originals
            if not file.is_duplicate:
                hashes[file.file_hash] = file 