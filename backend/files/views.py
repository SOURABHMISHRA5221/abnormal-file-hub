from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
import hashlib
import django_filters
from datetime import datetime
from django.db import transaction
import logging
import os
from .models import File, FileReference
from .serializers import FileSerializer, FileReferenceSerializer

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
        print(f"*** DEBUG *** Query parameters: {self.request.query_params}")
        
        # Handle various duplicate filter options
        is_duplicates = self.request.query_params.get('is_duplicate')
        show_duplicates = self.request.query_params.get('show_duplicates')
        include_duplicates = self.request.query_params.get('include_duplicates')
        only_duplicates = self.request.query_params.get('only_duplicates')
        
        print(f"*** DEBUG *** Duplicate filter params: is_duplicate={is_duplicates}, show_duplicates={show_duplicates}, include_duplicates={include_duplicates}, only_duplicates={only_duplicates}")
        
        # Check original filter logic
        if is_duplicates is None:
            if show_duplicates and show_duplicates.lower() == 'true':
                print("*** DEBUG *** Showing all files including duplicates")
                # Don't filter, return all files
                pass
            elif include_duplicates and include_duplicates.lower() == 'true':
                print("*** DEBUG *** Including duplicates in results")
                # Don't filter, return all files
                pass
            elif only_duplicates and only_duplicates.lower() == 'true':
                print("*** DEBUG *** Showing only duplicate files")
                queryset = queryset.filter(is_duplicate=True)
            else:
                print("*** DEBUG *** Filtering out duplicate files (default behavior)")
                queryset = queryset.filter(is_duplicate=False)
        elif is_duplicates.lower() == 'true':
            print("*** DEBUG *** Explicitly filtering to show only duplicates")
            queryset = queryset.filter(is_duplicate=True)
        
        # Log the count of files in the resulting queryset
        print(f"*** DEBUG *** Returning {queryset.count()} files")
        # Log all duplicate files in the system for debugging
        duplicate_files = File.objects.filter(is_duplicate=True)
        print(f"*** DEBUG *** System has {duplicate_files.count()} duplicate files")
        for dup in duplicate_files:
            refs = FileReference.objects.filter(reference_file=dup)
            if refs.exists():
                for ref in refs:
                    print(f"*** DEBUG *** Duplicate file: {dup.id} ({dup.original_filename}) -> Original: {ref.original_file.id} ({ref.original_file.original_filename})")
            else:
                print(f"*** DEBUG *** Duplicate file with no reference: {dup.id} ({dup.original_filename})")
        
        return queryset

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash for deduplication
        file_hash = self._calculate_file_hash(file_obj)
        
        # Debug the hash calculation
        print(f"*** DEDUPLICATION *** Calculated hash for {file_obj.name}: {file_hash}")
        
        # Use transaction.atomic to ensure thread-safety
        with transaction.atomic():
            # Select for update to lock the rows until the transaction is complete
            existing_files = File.objects.select_for_update().filter(file_hash=file_hash, is_duplicate=False)
            
            if existing_files.exists():
                # Get the first non-duplicate file with this hash
                original_file = existing_files.first()
                print(f"*** DEDUPLICATION *** Found duplicate file with hash {file_hash}. Original file: {original_file.id}")
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
                    print(f"*** DEDUPLICATION *** Fixed is_duplicate flag for file {duplicate_file.id}")
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
                print(f"*** DEDUPLICATION *** No duplicate found for hash {file_hash}. Creating new original file.")
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
    
    def destroy(self, request, *args, **kwargs):
        """
        Custom destroy method to properly handle file deletion, especially for files with duplicates
        or files that are duplicates of other files.
        """
        instance = self.get_object()
        print(f"*** DELETE *** Attempting to delete file: {instance.id} ({instance.original_filename})")
        
        with transaction.atomic():
            # Case 1: This is a duplicate file
            if instance.is_duplicate:
                print(f"*** DELETE *** Deleting duplicate file {instance.id}")
                
                # Find the reference to the original file and delete it
                try:
                    ref = FileReference.objects.get(reference_file=instance)
                    print(f"*** DELETE *** Found reference to original file {ref.original_file.id}")
                    ref.delete()
                    print(f"*** DELETE *** Deleted reference")
                except FileReference.DoesNotExist:
                    print(f"*** DELETE *** No reference found for duplicate file {instance.id}")
                
                # Now delete the actual file
                file_path = instance.file.path if instance.file else None
                instance.delete()
                
                # Delete physical file if it exists and is not used by other records
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"*** DELETE *** Deleted physical file at {file_path}")
                    except OSError as e:
                        print(f"*** DELETE *** Error deleting physical file: {e}")
                
            # Case 2: This is an original file that might have duplicates
            else:
                print(f"*** DELETE *** Deleting original file {instance.id}")
                
                # Find all references to this file
                references = FileReference.objects.filter(original_file=instance)
                
                if references.exists():
                    print(f"*** DELETE *** Found {references.count()} references to this file")
                    
                    # Get the first duplicate to promote to original
                    first_duplicate = references.first().reference_file
                    print(f"*** DELETE *** Promoting {first_duplicate.id} to original")
                    
                    # Set this duplicate as the new original
                    first_duplicate.is_duplicate = False
                    first_duplicate.save(update_fields=['is_duplicate'])
                    
                    # Update references for other duplicates to point to the new original
                    first_ref = references.first()
                    for ref in references.exclude(id=first_ref.id):
                        ref.original_file = first_duplicate
                        ref.save(update_fields=['original_file'])
                    
                    # Delete first reference since it's now an original
                    first_ref.delete()
                    
                    # Now delete the original file
                    file_path = instance.file.path if instance.file else None
                    instance.delete()
                    
                    # Delete physical file if it exists
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"*** DELETE *** Deleted physical file at {file_path}")
                        except OSError as e:
                            print(f"*** DELETE *** Error deleting physical file: {e}")
                else:
                    print(f"*** DELETE *** No references found for original file {instance.id}")
                    
                    # This is a standalone file, just delete it normally
                    file_path = instance.file.path if instance.file else None
                    instance.delete()
                    
                    # Delete physical file if it exists
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"*** DELETE *** Deleted physical file at {file_path}")
                        except OSError as e:
                            print(f"*** DELETE *** Error deleting physical file: {e}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _calculate_file_hash(self, file_obj):
        """Calculate SHA-256 hash of file contents for deduplication"""
        hasher = hashlib.sha256()
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        # Reset file pointer to beginning for later use
        file_obj.seek(0)
        return hasher.hexdigest()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about storage savings from deduplication"""
        # Count all files
        total_files = File.objects.count()
        # Count duplicates
        duplicate_files = File.objects.filter(is_duplicate=True).count()
        # Count unique files
        unique_files = total_files - duplicate_files
        
        # Calculate total physical storage used
        physical_storage = File.objects.filter(is_duplicate=False).aggregate(total=Sum('size'))['total'] or 0
        
        # Calculate total logical storage (what would be used without deduplication)
        logical_storage = File.objects.aggregate(total=Sum('size'))['total'] or 0
        
        # Calculate storage saved
        storage_saved = logical_storage - physical_storage
        
        # Log detailed storage statistics
        print(f"*** STATS *** Total files: {total_files}, Duplicates: {duplicate_files}, Unique: {unique_files}")
        print(f"*** STATS *** Physical storage: {physical_storage} bytes, Logical storage: {logical_storage} bytes")
        print(f"*** STATS *** Storage saved: {storage_saved} bytes ({round((storage_saved / logical_storage * 100) if logical_storage > 0 else 0, 2)}%)")
        
        return Response({
            'total_files': total_files,
            'duplicate_files': duplicate_files,
            'unique_files': unique_files,
            'physical_storage_bytes': physical_storage,
            'logical_storage_bytes': logical_storage,
            'storage_saved_bytes': storage_saved,
            'storage_saved_percentage': round((storage_saved / logical_storage * 100) if logical_storage > 0 else 0, 2)
        })
