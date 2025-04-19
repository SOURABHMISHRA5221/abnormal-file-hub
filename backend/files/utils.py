import os
import hashlib
from django.db import transaction, models
from .models import File, FileReference

def recalculate_file_hash(file_instance):
    """Recalculate hash for a file instance"""
    try:
        if file_instance.file:
            file_instance.file.seek(0)
            hasher = hashlib.sha256()
            for chunk in file_instance.file.chunks():
                hasher.update(chunk)
            file_instance.file_hash = hasher.hexdigest()
            file_instance.file.seek(0)
            file_instance.save(update_fields=['file_hash'])
            return True
    except Exception as e:
        print(f"Error calculating hash for {file_instance.id}: {e}")
    return False

def rebuild_file_references():
    """Rebuild all file references based on hashes"""
    with transaction.atomic():
        # Delete existing references
        FileReference.objects.all().delete()
        
        # Reset all duplicate flags
        File.objects.all().update(is_duplicate=False)
        
        # Group files by hash
        files_by_hash = {}
        for file in File.objects.all():
            if file.file_hash:
                if file.file_hash not in files_by_hash:
                    files_by_hash[file.file_hash] = []
                files_by_hash[file.file_hash].append(file)
        
        # For each hash with multiple files, set one as original and others as duplicates
        for file_hash, files in files_by_hash.items():
            if len(files) > 1:
                # The first file of each hash group is the original
                original_file = files[0]
                
                # All others are duplicates
                for duplicate_file in files[1:]:
                    duplicate_file.is_duplicate = True
                    duplicate_file.save(update_fields=['is_duplicate'])
                    
                    # Create a reference to the original file
                    FileReference.objects.create(
                        original_file=original_file,
                        reference_file=duplicate_file
                    )
        
        return {
            'total_files': File.objects.count(),
            'duplicate_files': File.objects.filter(is_duplicate=True).count(),
            'unique_files': File.objects.filter(is_duplicate=False).count(),
        }

def verify_duplicates():
    """Verify and fix any inconsistencies in duplicate flags and references"""
    with transaction.atomic():
        fixed_count = 0
        
        # Find FileReference objects where the reference_file is not marked as duplicate
        inconsistent_references = FileReference.objects.select_related('reference_file').filter(
            reference_file__is_duplicate=False
        )
        
        # Fix these inconsistencies
        for ref in inconsistent_references:
            ref.reference_file.is_duplicate = True
            ref.reference_file.save(update_fields=['is_duplicate'])
            fixed_count += 1
        
        # Find files marked as duplicates but don't have a reference
        orphaned_duplicates = File.objects.filter(
            is_duplicate=True
        ).exclude(
            id__in=FileReference.objects.values_list('reference_file_id', flat=True)
        )
        
        # Fix these by finding the proper original or removing the duplicate flag
        for orphan in orphaned_duplicates:
            if orphan.file_hash:
                original = File.objects.filter(
                    file_hash=orphan.file_hash, 
                    is_duplicate=False
                ).first()
                
                if original:
                    # Create the missing reference
                    FileReference.objects.create(
                        original_file=original,
                        reference_file=orphan
                    )
                else:
                    # No original found, unmark as duplicate
                    orphan.is_duplicate = False
                    orphan.save(update_fields=['is_duplicate'])
            else:
                # No hash, unmark as duplicate
                orphan.is_duplicate = False
                orphan.save(update_fields=['is_duplicate'])
            
            fixed_count += 1
        
        return {
            'fixed_count': fixed_count,
            'current_duplicates': File.objects.filter(is_duplicate=True).count(),
            'current_references': FileReference.objects.count()
        }

def calculate_storage_stats():
    """Calculate storage statistics"""
    # Count all files
    total_files = File.objects.count()
    # Count duplicates
    duplicate_files = File.objects.filter(is_duplicate=True).count()
    # Count unique files
    unique_files = total_files - duplicate_files
    
    # Calculate total physical storage used
    physical_storage = File.objects.filter(is_duplicate=False).aggregate(
        total=models.Sum('size'))['total'] or 0
    
    # Calculate total logical storage (what would be used without deduplication)
    logical_storage = File.objects.aggregate(total=models.Sum('size'))['total'] or 0
    
    # Calculate storage saved
    storage_saved = logical_storage - physical_storage
    
    return {
        'total_files': total_files,
        'duplicate_files': duplicate_files,
        'unique_files': unique_files,
        'physical_storage_bytes': physical_storage,
        'logical_storage_bytes': logical_storage,
        'storage_saved_bytes': storage_saved,
        'storage_saved_percentage': round((storage_saved / logical_storage * 100) 
                                          if logical_storage > 0 else 0, 2)
    } 