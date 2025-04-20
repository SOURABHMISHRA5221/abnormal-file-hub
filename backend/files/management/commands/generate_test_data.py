import os
import random
import logging
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from files.models import File, FileReference
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate test data for the file storage application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--unique',
            type=int,
            default=10,
            help='Number of unique files to create'
        )
        parser.add_argument(
            '--duplicates',
            type=int,
            default=20,
            help='Number of duplicate files to create'
        )
        parser.add_argument(
            '--size',
            type=int,
            default=1024,
            help='Base size of files in bytes'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clean']:
            self._clean_test_data()
        
        unique_count = options['unique']
        duplicate_count = options['duplicates']
        base_size = options['size']
        
        # Ensure media directory exists
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'uploads'), exist_ok=True)
        
        self.stdout.write(self.style.SUCCESS(f'Generating {unique_count} unique files and {duplicate_count} duplicates'))
        
        file_types = [
            ('txt', 'text/plain'),
            ('pdf', 'application/pdf'),
            ('jpg', 'image/jpeg'),
            ('png', 'image/png'),
            ('doc', 'application/msword')
        ]
        
        # Create unique files
        unique_files = []
        for i in range(unique_count):
            ext, file_type = random.choice(file_types)
            filename = f'test_file_{i}.{ext}'
            
            # Create random content with some variation in size
            size_variation = random.randint(-int(base_size * 0.2), int(base_size * 0.2))
            content_size = max(base_size + size_variation, 100)  # Minimum 100 bytes
            content = self._generate_random_content(content_size)
            
            try:
                file_obj = File()
                file_obj.file.save(filename, ContentFile(content))
                file_obj.original_filename = filename
                file_obj.file_type = file_type
                file_obj.size = len(content)
                file_obj.save()
                
                unique_files.append(file_obj)
                logger.info(f"Created unique file: {filename} (ID: {file_obj.id})")
                self.stdout.write(f"Created file {i+1}/{unique_count}: {filename}")
            except Exception as e:
                logger.error(f"Error creating file {filename}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Error creating file {filename}: {str(e)}"))
        
        # Create duplicate files
        for i in range(duplicate_count):
            if not unique_files:
                self.stdout.write(self.style.ERROR("No unique files to duplicate"))
                break
                
            # Choose a random original file to duplicate
            original_file = random.choice(unique_files)
            
            # Create a new filename for the duplicate
            name_parts = original_file.original_filename.split('.')
            duplicate_name = f"{name_parts[0]}_dup_{i}.{name_parts[-1]}"
            
            try:
                # Read the content of the original file
                with open(original_file.file.path, 'rb') as f:
                    content = f.read()
                
                # Create a new file with the same content
                duplicate = File()
                duplicate.file.save(duplicate_name, ContentFile(content))
                duplicate.original_filename = duplicate_name
                duplicate.file_type = original_file.file_type
                duplicate.size = len(content)
                duplicate.is_duplicate = True
                duplicate.file_hash = original_file.file_hash
                duplicate.save()
                
                # Create a file reference
                reference = FileReference(
                    original_file=original_file,
                    reference_file=duplicate
                )
                reference.save()
                
                logger.info(f"Created duplicate file: {duplicate_name} (ID: {duplicate.id})")
                self.stdout.write(f"Created duplicate {i+1}/{duplicate_count}: {duplicate_name}")
            except Exception as e:
                logger.error(f"Error creating duplicate {duplicate_name}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Error creating duplicate {duplicate_name}: {str(e)}"))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {unique_count} unique files and {duplicate_count} duplicates"
        ))
        
        # Print storage statistics
        total_files = File.objects.count()
        duplicate_files = File.objects.filter(is_duplicate=True).count()
        unique_files_count = total_files - duplicate_files
        
        physical_storage = sum(f.size for f in File.objects.filter(is_duplicate=False))
        logical_storage = sum(f.size for f in File.objects.all())
        storage_saved = logical_storage - physical_storage
        
        self.stdout.write("\nStorage Statistics:")
        self.stdout.write(f"Total Files: {total_files}")
        self.stdout.write(f"Unique Files: {unique_files_count}")
        self.stdout.write(f"Duplicate Files: {duplicate_files}")
        self.stdout.write(f"Physical Storage Used: {self._format_size(physical_storage)}")
        self.stdout.write(f"Logical Storage: {self._format_size(logical_storage)}")
        self.stdout.write(f"Storage Saved: {self._format_size(storage_saved)}")
        self.stdout.write(f"Deduplication Efficiency: {(storage_saved / logical_storage * 100):.2f}%")
    
    def _clean_test_data(self):
        """Clean existing test data"""
        try:
            # Delete all file references first
            file_reference_count = FileReference.objects.count()
            FileReference.objects.all().delete()
            logger.info(f"Deleted {file_reference_count} file references")
            
            # Delete all files
            file_count = File.objects.count()
            deleted_files = []
            
            # Delete files and their physical storage
            for file_obj in File.objects.all():
                if file_obj.file and os.path.isfile(file_obj.file.path):
                    try:
                        os.remove(file_obj.file.path)
                        deleted_files.append(file_obj.id)
                    except (FileNotFoundError, PermissionError) as e:
                        logger.warning(f"Could not delete file {file_obj.file.path}: {str(e)}")
            
            # Delete all file objects
            File.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS(
                f"Cleaned up {file_count} files and {file_reference_count} references"
            ))
            logger.info(f"Cleaned {file_count} files and {file_reference_count} references")
        except Exception as e:
            logger.error(f"Error cleaning test data: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error cleaning test data: {str(e)}"))
    
    def _generate_random_content(self, size):
        """Generate random binary content of specified size"""
        # Create a mix of ASCII printable characters and some binary data
        return bytes([random.randint(32, 126) for _ in range(size)])
    
    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB" 