import os
import hashlib
import tempfile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status
from files.models import File, FileReference
from files.views import FileViewSet


class HashCalculationTest(TestCase):
    """Test cases for file hash calculation"""

    def setUp(self):
        """Set up test data"""
        self.view_instance = FileViewSet()
        
        # Create sample file contents
        self.empty_content = b''
        self.small_content = b'Small file content'
        self.large_content = b'x' * 10000  # 10KB of data
        
        # Calculate expected hashes
        self.empty_hash = hashlib.sha256(self.empty_content).hexdigest()
        self.small_hash = hashlib.sha256(self.small_content).hexdigest()
        self.large_hash = hashlib.sha256(self.large_content).hexdigest()
        
        # Create file objects
        self.empty_file = SimpleUploadedFile('empty.txt', self.empty_content)
        self.small_file = SimpleUploadedFile('small.txt', self.small_content)
        self.large_file = SimpleUploadedFile('large.txt', self.large_content)

    def test_hash_calculation_empty_file(self):
        """Test hash calculation for empty file"""
        calculated_hash = self.view_instance._calculate_file_hash(self.empty_file)
        self.assertEqual(calculated_hash, self.empty_hash)
        
        # Check that file pointer has been reset
        self.assertEqual(self.empty_file.tell(), 0)

    def test_hash_calculation_small_file(self):
        """Test hash calculation for small file"""
        calculated_hash = self.view_instance._calculate_file_hash(self.small_file)
        self.assertEqual(calculated_hash, self.small_hash)
        
        # Check that file pointer has been reset
        self.assertEqual(self.small_file.tell(), 0)

    def test_hash_calculation_large_file(self):
        """Test hash calculation for large file"""
        calculated_hash = self.view_instance._calculate_file_hash(self.large_file)
        self.assertEqual(calculated_hash, self.large_hash)
        
        # Check that file pointer has been reset
        self.assertEqual(self.large_file.tell(), 0)
        
    def test_hash_calculation_file_seek(self):
        """Test that hash calculation properly seeks file position"""
        # Move file pointer to middle
        self.small_file.seek(5)
        
        # Calculate hash (should reset pointer)
        calculated_hash = self.view_instance._calculate_file_hash(self.small_file)
        
        # Hash should match full content
        self.assertEqual(calculated_hash, self.small_hash)
        
        # Pointer should be reset
        self.assertEqual(self.small_file.tell(), 0)


class DeduplicationSystemTest(APITestCase):
    """Test cases for the file deduplication system"""

    def setUp(self):
        """Set up test data"""
        # Create file contents with specific hashes
        self.content1 = b'Content for file 1'
        self.content2 = b'Different content for file 2'
        
        # Calculate hashes
        self.hash1 = hashlib.sha256(self.content1).hexdigest()
        self.hash2 = hashlib.sha256(self.content2).hexdigest()
        
        # Files URL
        self.files_url = '/api/files/'

    def tearDown(self):
        """Clean up after tests"""
        # Delete any created files
        for file_obj in File.objects.all():
            if file_obj.file and os.path.isfile(file_obj.file.path):
                try:
                    os.remove(file_obj.file.path)
                except (FileNotFoundError, PermissionError):
                    pass

    def test_deduplication_new_file(self):
        """Test uploading a new (non-duplicate) file"""
        upload_file = SimpleUploadedFile('file1.txt', self.content1)
        
        response = self.client.post(
            self.files_url,
            {'file': upload_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), 1)
        
        # File should not be marked as duplicate
        file_obj = File.objects.first()
        self.assertEqual(file_obj.file_hash, self.hash1)
        self.assertFalse(file_obj.is_duplicate)
        
        # No references should exist
        self.assertEqual(FileReference.objects.count(), 0)

    def test_deduplication_duplicate_file(self):
        """Test uploading a duplicate file"""
        # First upload the original file
        original_file = SimpleUploadedFile('original.txt', self.content1)
        response = self.client.post(
            self.files_url,
            {'file': original_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Now upload a duplicate with the same content
        duplicate_file = SimpleUploadedFile('duplicate.txt', self.content1)
        response = self.client.post(
            self.files_url,
            {'file': duplicate_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should have two files now
        self.assertEqual(File.objects.count(), 2)
        
        # Get the files
        original = File.objects.filter(is_duplicate=False).first()
        duplicate = File.objects.filter(is_duplicate=True).first()
        
        # Check properties
        self.assertEqual(original.original_filename, 'original.txt')
        self.assertEqual(duplicate.original_filename, 'duplicate.txt')
        self.assertEqual(original.file_hash, self.hash1)
        self.assertEqual(duplicate.file_hash, self.hash1)
        
        # Should have a file reference
        self.assertEqual(FileReference.objects.count(), 1)
        reference = FileReference.objects.first()
        self.assertEqual(reference.original_file, original)
        self.assertEqual(reference.reference_file, duplicate)

    def test_deduplication_multiple_duplicates(self):
        """Test uploading multiple duplicates of the same file"""
        # Upload the original file
        original_file = SimpleUploadedFile('original.txt', self.content1)
        self.client.post(
            self.files_url,
            {'file': original_file},
            format='multipart'
        )
        
        # Upload first duplicate
        dup1_file = SimpleUploadedFile('duplicate1.txt', self.content1)
        self.client.post(
            self.files_url,
            {'file': dup1_file},
            format='multipart'
        )
        
        # Upload second duplicate
        dup2_file = SimpleUploadedFile('duplicate2.txt', self.content1)
        self.client.post(
            self.files_url,
            {'file': dup2_file},
            format='multipart'
        )
        
        # Should have 3 files total (1 original + 2 duplicates)
        self.assertEqual(File.objects.count(), 3)
        self.assertEqual(File.objects.filter(is_duplicate=False).count(), 1)
        self.assertEqual(File.objects.filter(is_duplicate=True).count(), 2)
        
        # Should have 2 file references
        self.assertEqual(FileReference.objects.count(), 2)
        
        # Get the original file
        original = File.objects.filter(is_duplicate=False).first()
        
        # All references should point to the same original
        for ref in FileReference.objects.all():
            self.assertEqual(ref.original_file, original)

    def test_deduplication_mixed_files(self):
        """Test uploading a mix of duplicate and non-duplicate files"""
        # Upload first unique file
        file1 = SimpleUploadedFile('file1.txt', self.content1)
        self.client.post(
            self.files_url,
            {'file': file1},
            format='multipart'
        )
        
        # Upload second unique file (different content)
        file2 = SimpleUploadedFile('file2.txt', self.content2)
        self.client.post(
            self.files_url,
            {'file': file2},
            format='multipart'
        )
        
        # Upload duplicate of first file
        dup1 = SimpleUploadedFile('dup1.txt', self.content1)
        self.client.post(
            self.files_url,
            {'file': dup1},
            format='multipart'
        )
        
        # Upload duplicate of second file
        dup2 = SimpleUploadedFile('dup2.txt', self.content2)
        self.client.post(
            self.files_url,
            {'file': dup2},
            format='multipart'
        )
        
        # Should have 4 files total (2 originals + 2 duplicates)
        self.assertEqual(File.objects.count(), 4)
        self.assertEqual(File.objects.filter(is_duplicate=False).count(), 2)
        self.assertEqual(File.objects.filter(is_duplicate=True).count(), 2)
        
        # Should have 2 file references
        self.assertEqual(FileReference.objects.count(), 2)
        
        # Get the originals
        original1 = File.objects.filter(is_duplicate=False, file_hash=self.hash1).first()
        original2 = File.objects.filter(is_duplicate=False, file_hash=self.hash2).first()
        
        # Check that duplicates reference the correct originals
        dup1_ref = FileReference.objects.filter(reference_file__original_filename='dup1.txt').first()
        dup2_ref = FileReference.objects.filter(reference_file__original_filename='dup2.txt').first()
        
        self.assertEqual(dup1_ref.original_file, original1)
        self.assertEqual(dup2_ref.original_file, original2)


class TransactionHandlingTest(APITestCase):
    """Test cases for transaction handling in file operations"""

    def setUp(self):
        """Set up test data"""
        self.content = b'Test content for transaction testing'
        self.files_url = '/api/files/'

    def tearDown(self):
        """Clean up after tests"""
        # Delete any created files
        for file_obj in File.objects.all():
            if file_obj.file and os.path.isfile(file_obj.file.path):
                try:
                    os.remove(file_obj.file.path)
                except (FileNotFoundError, PermissionError):
                    pass

    def test_transaction_integrity_on_upload(self):
        """Test transaction integrity during file upload"""
        # Create a file upload
        upload_file = SimpleUploadedFile('transaction_test.txt', self.content)
        
        # Count files before
        files_before = File.objects.count()
        
        # Try to simulate a transaction error during upload
        with transaction.atomic():
            # Upload the file within the transaction
            response = self.client.post(
                self.files_url,
                {'file': upload_file},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify file was created within the transaction
            self.assertEqual(File.objects.count(), files_before + 1)
            
            # Force a rollback by raising an exception
            raise Exception("Forced transaction rollback for testing")
            
        # Transaction should have rolled back, so file count should be back to the original
        self.assertEqual(File.objects.count(), files_before) 