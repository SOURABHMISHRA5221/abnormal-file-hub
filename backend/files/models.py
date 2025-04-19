from django.db import models
import uuid
import os
import hashlib
from django.db.models.signals import post_save
from django.dispatch import receiver

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    is_duplicate = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    def save(self, *args, **kwargs):
        # If this is a new file (no ID yet) and file_hash is not set, calculate it
        if not self.file_hash and self.file:
            try:
                self.file.seek(0)
                hasher = hashlib.sha256()
                for chunk in self.file.chunks():
                    hasher.update(chunk)
                self.file_hash = hasher.hexdigest()
                self.file.seek(0)
            except Exception as e:
                print(f"Error calculating hash: {e}")
        
        # Make sure is_duplicate flag is saved properly
        super().save(*args, **kwargs)
    
    @property
    def duplicate_count(self):
        """Get the number of duplicates for this file"""
        if self.is_duplicate:
            return 0
        return FileReference.objects.filter(original_file=self).count()
    
    @property
    def storage_saved(self):
        """Calculate storage saved through deduplication in bytes"""
        return self.size * self.duplicate_count

class FileReference(models.Model):
    """Model to track references to original files (for deduplication)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='references')
    reference_file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='reference')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Reference: {self.reference_file.original_filename} -> {self.original_file.original_filename}"

# Signal to ensure reference_file is_duplicate is set to True
@receiver(post_save, sender=FileReference)
def update_reference_file(sender, instance, created, **kwargs):
    """Ensure reference_file is properly marked as duplicate when a reference is created"""
    if created and not instance.reference_file.is_duplicate:
        instance.reference_file.is_duplicate = True
        instance.reference_file.save(update_fields=['is_duplicate'])
