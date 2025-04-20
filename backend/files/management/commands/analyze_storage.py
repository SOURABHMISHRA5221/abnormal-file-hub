import logging
import os
from django.core.management.base import BaseCommand
from files.models import File, FileReference
from django.db.models import Sum, Count, F, Q, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyzes storage usage and deduplication efficiency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed analysis by file type',
        )
        parser.add_argument(
            '--min-duplicates',
            type=int,
            default=1,
            help='Minimum number of duplicates to include in report',
        )

    def handle(self, *args, **options):
        detail = options.get('detail', False)
        min_duplicates = options.get('min_duplicates', 1)
        
        try:
            # Get overall stats
            total_files = File.objects.count()
            original_files = File.objects.filter(is_duplicate=False).count()
            duplicate_files = File.objects.filter(is_duplicate=True).count()
            
            # Get storage stats
            physical_storage = sum(f.size for f in File.objects.filter(is_duplicate=False))
            logical_storage = sum(f.size for f in File.objects.all())
            storage_saved = logical_storage - physical_storage
            
            # Report overall stats
            self.stdout.write("\n=== Storage Analysis Report ===\n")
            self.stdout.write(f"Total Files: {total_files}")
            self.stdout.write(f"Original Files: {original_files}")
            self.stdout.write(f"Duplicate Files: {duplicate_files}")
            self.stdout.write(f"Physical Storage: {self._format_size(physical_storage)}")
            self.stdout.write(f"Logical Storage: {self._format_size(logical_storage)}")
            self.stdout.write(f"Storage Saved: {self._format_size(storage_saved)}")
            
            if total_files > 0:
                duplicates_percent = (duplicate_files / total_files) * 100
                self.stdout.write(f"Duplicate Percentage: {duplicates_percent:.2f}%")
            
            if logical_storage > 0:
                dedup_ratio = logical_storage / physical_storage if physical_storage > 0 else 0
                efficiency = (storage_saved / logical_storage) * 100
                self.stdout.write(f"Deduplication Ratio: {dedup_ratio:.2f}x")
                self.stdout.write(f"Storage Efficiency: {efficiency:.2f}%")
            
            # Check for files with missing physical files
            missing_files = 0
            for file_obj in File.objects.all():
                if file_obj.file and not os.path.exists(file_obj.file.path):
                    missing_files += 1
                    logger.warning(f"Missing physical file: {file_obj.file.path} (ID: {file_obj.id})")
            
            if missing_files > 0:
                self.stdout.write(self.style.WARNING(f"\nWarning: {missing_files} files are missing from storage"))
            
            # Show file type distribution
            if detail:
                self.stdout.write("\n=== File Type Distribution ===\n")
                
                file_types = File.objects.values('file_type').annotate(
                    count=Count('id'),
                    total_size=Sum('size'),
                    originals=Sum(Case(
                        When(is_duplicate=False, then=1),
                        default=0,
                        output_field=IntegerField()
                    )),
                    duplicates=Sum(Case(
                        When(is_duplicate=True, then=1),
                        default=0,
                        output_field=IntegerField()
                    )),
                ).order_by('-count')
                
                for ft in file_types:
                    self.stdout.write(f"File Type: {ft['file_type']}")
                    self.stdout.write(f"  Count: {ft['count']} (Originals: {ft['originals']}, Duplicates: {ft['duplicates']})")
                    self.stdout.write(f"  Total Size: {self._format_size(ft['total_size'])}")
                    if ft['count'] > 0:
                        dup_pct = (ft['duplicates'] / ft['count']) * 100
                        self.stdout.write(f"  Duplicate Percentage: {dup_pct:.2f}%")
                    self.stdout.write("")
                
                # Find files with the most duplicates
                self.stdout.write("\n=== Top Files by Duplicate Count ===\n")
                
                # Get files with duplicates above threshold
                top_files = FileReference.objects.values('original_file').annotate(
                    duplicate_count=Count('reference_file')
                ).filter(duplicate_count__gte=min_duplicates).order_by('-duplicate_count')[:10]
                
                if not top_files:
                    self.stdout.write("No files found with duplicates meeting the minimum threshold.")
                
                for idx, item in enumerate(top_files, 1):
                    try:
                        original = File.objects.get(pk=item['original_file'])
                        storage_saved = original.storage_saved
                        
                        self.stdout.write(f"{idx}. {original.original_filename}")
                        self.stdout.write(f"   Hash: {original.file_hash[:10]}...")
                        self.stdout.write(f"   Size: {self._format_size(original.size)}")
                        self.stdout.write(f"   Duplicates: {item['duplicate_count']}")
                        self.stdout.write(f"   Storage Saved: {self._format_size(storage_saved)}")
                        self.stdout.write("")
                    except File.DoesNotExist:
                        continue
                
        except Exception as e:
            logger.error(f"Error generating storage analysis: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error generating storage analysis: {str(e)}"))
    
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