import logging
from django.core.management.base import BaseCommand
from files.models import File, FileReference
from django.db import transaction
from django.db.models import Count

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes all duplicate files from the system while maintaining references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without performing the actual deletion',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Find all files that are duplicates
        duplicate_files = File.objects.filter(is_duplicate=True)
        
        if not duplicate_files.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate files found to delete'))
            return
        
        duplicate_count = duplicate_files.count()
        total_size = sum(duplicate_files.values_list('size', flat=True))
        
        self.stdout.write(
            f"Found {duplicate_count} duplicate files consuming {total_size / (1024*1024):.2f} MB"
        )
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"DRY RUN: Would delete {duplicate_count} files, saving {total_size / (1024*1024):.2f} MB"
            ))
            return
        
        try:
            with transaction.atomic():
                # Count deleted files and freed space
                deleted_count = 0
                freed_space = 0
                
                for duplicate in duplicate_files:
                    logger.info(f"Deleting duplicate file: {duplicate.original_filename} (ID: {duplicate.id})")
                    
                    # Store size before deleting for reporting
                    freed_space += duplicate.size
                    deleted_count += 1
                    
                    # Delete the file object (this also deletes the file from disk)
                    duplicate.delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} duplicate files, freeing up {freed_space / (1024*1024):.2f} MB"
                ))
                
        except Exception as e:
            logger.error(f"Error while deleting duplicate files: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Failed to delete duplicate files: {str(e)}")) 