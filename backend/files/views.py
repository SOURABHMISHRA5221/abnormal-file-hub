from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse, FileResponse
import hashlib
import django_filters
from datetime import datetime
from django.db import transaction
import logging
import os
import sys
from .models import File, FileReference
from .serializers import FileSerializer, FileReferenceSerializer
from .utils import verify_duplicates, calculate_storage_stats

# Get the logger for this app
logger = logging.getLogger('files')

# Add explicit stdout print for stats endpoint
def print_debug(message):
    print(f"***ABNORMAL DEBUG***: {message}", file=sys.stdout)
    sys.stdout.flush()

# Create your views here.

class FileFilter(django_filters.FilterSet):
    """Filter for files with various options"""
    file_type = django_filters.CharFilter(lookup_expr='iexact')
    min_size = django_filters.NumberFilter(field_name='size', lookup_expr='gte')
    max_size = django_filters.NumberFilter(field_name='size', lookup_expr='lte')
    uploaded_after = django_filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_before = django_filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')
    
    class Meta:
        model = File
        fields = ['file_type', 'min_size', 'max_size', 'uploaded_after', 'uploaded_before']

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FileFilter
    search_fields = ['original_filename']
    ordering_fields = ['original_filename', 'size', 'uploaded_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Log all query parameters
        logger.debug(f"Query parameters: {self.request.query_params}")
        
        # Handle various duplicate filter options
        is_duplicates = self.request.query_params.get('is_duplicate')
        show_duplicates = self.request.query_params.get('show_duplicates')
        include_duplicates = self.request.query_params.get('include_duplicates')
        only_duplicates = self.request.query_params.get('only_duplicates')
        
        logger.debug(f"Duplicate filter params: is_duplicate={is_duplicates}, show_duplicates={show_duplicates}, include_duplicates={include_duplicates}, only_duplicates={only_duplicates}")
        
        # Check original filter logic
        if is_duplicates is None:
            if show_duplicates and show_duplicates.lower() == 'true':
                logger.debug("Showing all files including duplicates")
                # Don't filter, return all files
                pass
            elif include_duplicates and include_duplicates.lower() == 'true':
                logger.debug("Including duplicates in results")
                # Don't filter, return all files
                pass
            elif only_duplicates and only_duplicates.lower() == 'true':
                logger.debug("Showing only duplicate files")
                queryset = queryset.filter(is_duplicate=True)
            else:
                logger.debug("Filtering out duplicate files (default behavior)")
                queryset = queryset.filter(is_duplicate=False)
        elif is_duplicates.lower() == 'true':
            logger.debug("Explicitly filtering to show only duplicates")
            queryset = queryset.filter(is_duplicate=True)
        
        # Log the count of files in the resulting queryset
        logger.debug(f"Returning {queryset.count()} files")
        
        # Log all duplicate files in the system for debugging
        duplicate_files = File.objects.filter(is_duplicate=True)
        logger.debug(f"System has {duplicate_files.count()} duplicate files")
        for dup in duplicate_files:
            refs = FileReference.objects.filter(reference_file=dup)
            if refs.exists():
                for ref in refs:
                    logger.debug(f"Duplicate file: {dup.id} ({dup.original_filename}) -> Original: {ref.original_file.id} ({ref.original_file.original_filename})")
            else:
                logger.debug(f"Duplicate file with no reference: {dup.id} ({dup.original_filename})")
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Handle file upload with deduplication
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            logger.warning("File upload failed: No file provided")
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug(f"File upload initiated: {file_obj.name}")
        
        # Calculate file hash for deduplication
        file_hash = self._calculate_file_hash(file_obj)
        logger.debug(f"Calculated hash for {file_obj.name}: {file_hash}")
        
        # Use transaction.atomic to ensure thread-safety
        with transaction.atomic():
            # Select for update to lock the rows until the transaction is complete
            existing_files = File.objects.select_for_update().filter(file_hash=file_hash, is_duplicate=False)
            
            if existing_files.exists():
                # Get the first non-duplicate file with this hash
                original_file = existing_files.first()
                logger.debug(f"Found duplicate file with hash {file_hash}. Original file: {original_file.id}")
                
                # Create a new file entry that will be marked as a duplicate
                data = {
                    'file': file_obj,
                    'original_filename': file_obj.name,
                    'file_type': file_obj.content_type,
                    'size': file_obj.size,
                    'file_hash': file_hash,
                    'is_duplicate': True  # Explicitly mark as duplicate
                }
                
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                duplicate_file = serializer.save()
                
                # Create a reference to the original file
                reference = FileReference.objects.create(
                    original_file=original_file,
                    reference_file=duplicate_file
                )
                
                # Ensure is_duplicate is True - double check
                if not duplicate_file.is_duplicate:
                    logger.debug(f"Fixed is_duplicate flag for file {duplicate_file.id}")
                    duplicate_file.is_duplicate = True
                    duplicate_file.save(update_fields=['is_duplicate'])
                
                # Return response with the duplicate file information
                headers = self.get_success_headers(serializer.data)
                return Response(
                    {**serializer.data, 'is_duplicate': True, 'original_file_id': str(original_file.id)},
                    status=status.HTTP_201_CREATED, 
                    headers=headers
                )
            else:
                # Store the new file
                logger.debug(f"No duplicate found for hash {file_hash}. Creating new original file.")
                data = {
                    'file': file_obj,
                    'original_filename': file_obj.name,
                    'file_type': file_obj.content_type,
                    'size': file_obj.size,
                    'file_hash': file_hash,
                    'is_duplicate': False
                }
                
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                file_instance = serializer.save()
                
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _verify_file_reference_consistency(self):
        """
        Verify the integrity of FileReference records and fix any issues.
        Uses the verify_duplicates utility to ensure consistency.
        """
        logger.debug("Checking file reference consistency")
        results = verify_duplicates()
        if results['fixed_count'] > 0:
            logger.info(f"Fixed {results['fixed_count']} consistency issues")
            logger.debug(f"Current duplicates: {results['current_duplicates']}")
            logger.debug(f"Current references: {results['current_references']}")
        else:
            logger.debug("File references are consistent, no issues found")
        return results['fixed_count']

    def destroy(self, request, *args, **kwargs):
        """
        Custom destroy method to properly handle file deletion, especially for files with duplicates
        or files that are duplicates of other files.
        """
        instance = self.get_object()
        logger.debug(f"Attempting to delete file: {instance.id} ({instance.original_filename})")
        
        with transaction.atomic():
            # Case 1: This is a duplicate file
            if instance.is_duplicate:
                logger.debug(f"Deleting duplicate file {instance.id}")
                
                # Find the reference to the original file and delete it
                try:
                    ref = FileReference.objects.get(reference_file=instance)
                    original_file = ref.original_file
                    logger.debug(f"Found reference to original file {original_file.id}")
                    
                    # Delete the reference first
                    ref.delete()
                    logger.debug("Deleted reference")
                    
                    # Now delete the duplicate file itself
                    file_path = instance.file.path if instance.file else None
                    instance.delete()
                    logger.debug("Deleted duplicate file entry from database")
                    
                    # Delete physical file if it exists and is not used by other records
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted physical file at {file_path}")
                        except OSError as e:
                            logger.error(f"Error deleting physical file: {e}")
                    
                except FileReference.DoesNotExist:
                    logger.warning(f"No reference found for duplicate file {instance.id}")
                    # Still delete the file even if no reference found (cleanup orphaned duplicates)
                    file_path = instance.file.path if instance.file else None
                    instance.delete()
                    
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted physical file at {file_path}")
                        except OSError as e:
                            logger.error(f"Error deleting physical file: {e}")
                
            # Case 2: This is an original file that might have duplicates
            else:
                logger.debug(f"Deleting original file {instance.id}")
                
                # Find all references to this file
                references = FileReference.objects.filter(original_file=instance)
                
                # Check if this file has duplicates
                if references.exists():
                    logger.debug(f"Found {references.count()} references to this file")
                    
                    # Check if this is an attempt to delete an original before its duplicates
                    user_confirm = request.query_params.get('confirm_delete_original', 'false').lower() == 'true'
                    
                    if not user_confirm:
                        # Return an error indicating that duplicates should be deleted first
                        duplicate_ids = [str(ref.reference_file.id) for ref in references]
                        duplicate_filenames = [ref.reference_file.original_filename for ref in references]
                        logger.warning(f"Attempt to delete original with duplicates without confirmation. Duplicates: {duplicate_ids}")
                        return Response({
                            'error': 'Cannot delete original file with duplicates.',
                            'message': 'This file has duplicates. You should delete the duplicates first, or confirm deletion of the original file.',
                            'duplicate_count': references.count(),
                            'duplicate_ids': duplicate_ids,
                            'duplicate_filenames': duplicate_filenames
                        }, status=status.HTTP_409_CONFLICT)
                    
                    # User confirmed deletion despite duplicates, so continue with the deletion
                    logger.info(f"User confirmed deletion of original with duplicates")
                    
                    # Get the first duplicate to promote to original
                    first_reference = references.first()
                    first_duplicate = first_reference.reference_file
                    logger.debug(f"Promoting {first_duplicate.id} to original")
                    
                    # Set this duplicate as the new original
                    first_duplicate.is_duplicate = False
                    first_duplicate.save(update_fields=['is_duplicate'])
                    logger.debug(f"Updated duplicate to be the new original")
                    
                    # Update all other references to point to the new original
                    other_references = references.exclude(id=first_reference.id)
                    for ref in other_references:
                        logger.debug(f"Updating reference {ref.id} to point to new original {first_duplicate.id}")
                        ref.original_file = first_duplicate
                        ref.save(update_fields=['original_file'])
                    
                    # Delete the first reference (between old original and new original)
                    first_reference.delete()
                    logger.debug(f"Deleted reference between old original and new original")
                
                # Now delete the original file entry
                file_path = instance.file.path if instance.file else None
                instance.delete()
                logger.debug(f"Deleted original file entry from database")
                
                # Delete physical file if it exists and is not used by other records
                if file_path and os.path.exists(file_path):
                    other_files_with_same_path = File.objects.filter(file=instance.file.name).exclude(id=instance.id)
                    if not other_files_with_same_path.exists():
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted physical file at {file_path}")
                        except OSError as e:
                            logger.error(f"Error deleting physical file: {e}")
                    else:
                        logger.debug(f"Not deleting physical file because it's used by {other_files_with_same_path.count()} other files")
                
            return Response(status=status.HTTP_204_NO_CONTENT)

    def _calculate_file_hash(self, file_obj):
        """Calculate SHA-256 hash of file contents for deduplication"""
        hasher = hashlib.sha256()
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        for chunk in file_obj.chunks():
            hasher.update(chunk)
            
        # Reset file pointer to beginning for later use
        file_obj.seek(0)
        
        return hasher.hexdigest()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about storage savings from deduplication"""
        print_debug("Calculating storage statistics")
        logger.debug("Calculating storage statistics")
        
        # First verify file reference consistency
        self._verify_file_reference_consistency()
        
        # Use the utility to calculate up-to-date statistics
        stats = calculate_storage_stats()
        
        # Log detailed storage statistics
        print_debug(f"Total files: {stats['total_files']}, Duplicates: {stats['duplicate_files']}, Unique: {stats['unique_files']}")
        logger.info(f"Total files: {stats['total_files']}, Duplicates: {stats['duplicate_files']}, Unique: {stats['unique_files']}")
        
        print_debug(f"Physical storage: {stats['physical_storage_bytes']} bytes, Logical storage: {stats['logical_storage_bytes']} bytes")
        logger.debug(f"Physical storage: {stats['physical_storage_bytes']} bytes, Logical storage: {stats['logical_storage_bytes']} bytes")
        
        print_debug(f"Storage saved: {stats['storage_saved_bytes']} bytes ({stats['storage_saved_percentage']}%)")
        logger.debug(f"Storage saved: {stats['storage_saved_bytes']} bytes ({stats['storage_saved_percentage']}%)")
        
        # Log details about each duplicate file
        for duplicate in File.objects.filter(is_duplicate=True):
            try:
                reference = FileReference.objects.get(reference_file=duplicate)
                original = reference.original_file
                print_debug(f"Duplicate {duplicate.id} ({duplicate.original_filename}) -> Original {original.id} ({original.original_filename})")
                logger.debug(f"Duplicate {duplicate.id} ({duplicate.original_filename}) -> Original {original.id} ({original.original_filename})")
            except FileReference.DoesNotExist:
                print_debug(f"WARNING: Duplicate {duplicate.id} ({duplicate.original_filename}) has no reference to original!")
                logger.warning(f"WARNING: Duplicate {duplicate.id} ({duplicate.original_filename}) has no reference to original!")
        
        return Response(stats)
        
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download a file
        """
        file_instance = self.get_object()
        logger.debug(f"File download requested: {file_instance.original_filename} (ID: {file_instance.id})")
        
        file_path = file_instance.file.path
        
        if not os.path.exists(file_path):
            logger.error(f"File not found on disk: {file_path}")
            return Response({'detail': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
            
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_instance.original_filename}"'
        
        return response
