import os
import io
import hashlib
import json
import logging
import tempfile
from datetime import datetime, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from files.models import File, FileReference
from .fixtures import create_test_file, cleanup_test_files, create_file_pair
from django.test import TestCase, override_settings
from django.utils import timezone

# Set up logging
logger = logging.getLogger(__name__)

# Create a temporary directory for test uploads
TEMP_MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'test_uploads')
os.makedirs(TEMP_MEDIA_ROOT, exist_ok=True)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FileViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create some test files for listing tests
        self.file1 = create_test_file(
            filename='test1.txt', 
            content=b'Test content 1',
            file_type='text/plain'
        )
        self.file2 = create_test_file(
            filename='test2.pdf', 
            content=b'PDF content',
            file_type='application/pdf'
        )
        self.file3 = create_test_file(
            filename='test3.jpg', 
            content=b'JPEG content',
            file_type='image/jpeg'
        )
        
        # Create a duplicate pair
        self.original, self.duplicate, self.reference = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Duplicate content for testing'
        )
        
        logger.debug(f"Test setup complete with {File.objects.count()} files")

    def tearDown(self):
        cleanup_test_files()
        logger.debug("Test cleanup complete")

    def test_get_file_list(self):
        """Test retrieving the list of files."""
        url = reverse('file-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)  # All 4 non-duplicate files
        logger.debug(f"Retrieved {len(response.data['results'])} files")

    def test_get_file_list_with_duplicates(self):
        """Test retrieving the list of files including duplicates."""
        url = reverse('file-list')
        response = self.client.get(url, {'include_duplicates': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # All 5 files including the duplicate
        
        # Check that duplicate flag is correctly set
        duplicates = [f for f in response.data['results'] if f['is_duplicate']]
        self.assertEqual(len(duplicates), 1)
        logger.debug(f"Retrieved {len(response.data['results'])} files with duplicates")

    def test_filter_by_file_type(self):
        """Test filtering files by file type."""
        url = reverse('file-list')
        response = self.client.get(url, {'file_type': 'text/plain'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only the 2 text files
        
        for file in response.data['results']:
            self.assertEqual(file['file_type'], 'text/plain')
        logger.debug(f"Successfully filtered by file_type, got {len(response.data['results'])} files")

    def test_filter_by_size_range(self):
        """Test filtering files by size range."""
        # Create a larger file
        large_file = create_test_file(
            filename='large.txt',
            content=b'x' * 10000,  # 10KB file
            file_type='text/plain'
        )
        
        url = reverse('file-list')
        # Filter for files between 5KB and 15KB
        response = self.client.get(url, {'min_size': 5000, 'max_size': 15000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the large file
        self.assertEqual(response.data['results'][0]['size'], 10000)
        logger.debug(f"Successfully filtered by size range, got {len(response.data['results'])} files")

    def test_filter_by_date_range(self):
        """Test filtering files by upload date range."""
        # Create a file with a specific date
        yesterday = timezone.now() - timedelta(days=1)
        old_file = create_test_file(filename='old.txt', content=b'Old content')
        # Update the timestamp manually
        File.objects.filter(pk=old_file.pk).update(uploaded_at=yesterday)
        
        url = reverse('file-list')
        # Get only today's files
        today = timezone.now().date().isoformat()
        response = self.client.get(url, {'uploaded_after': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
        # The old file should not be in the results
        old_file_ids = [f['id'] for f in response.data['results'] if f['original_filename'] == 'old.txt']
        self.assertEqual(len(old_file_ids), 0)
        logger.debug(f"Successfully filtered by date range, got {len(response.data['results'])} files")

    def test_upload_file(self):
        """Test uploading a new file."""
        url = reverse('file-list')
        with open(os.path.join(TEMP_MEDIA_ROOT, 'new_file.txt'), 'wb') as f:
            f.write(b'New file content')
        
        with open(os.path.join(TEMP_MEDIA_ROOT, 'new_file.txt'), 'rb') as f:
            response = self.client.post(url, {'file': f}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_filename'], 'new_file.txt')
        self.assertEqual(response.data['file_type'], 'text/plain')
        self.assertEqual(response.data['is_duplicate'], False)
        logger.debug(f"Successfully uploaded new file: {response.data['id']}")

    def test_upload_duplicate_file(self):
        """Test uploading a file with the same content as an existing file."""
        # First, create a file with specific content
        content = b'Unique content for duplication test'
        first_file = create_test_file(
            filename='first.txt',
            content=content,
            file_type='text/plain'
        )
        
        # Now upload a file with the same content but a different name
        url = reverse('file-list')
        with open(os.path.join(TEMP_MEDIA_ROOT, 'second.txt'), 'wb') as f:
            f.write(content)
        
        with open(os.path.join(TEMP_MEDIA_ROOT, 'second.txt'), 'rb') as f:
            response = self.client.post(url, {'file': f}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_filename'], 'second.txt')
        self.assertEqual(response.data['is_duplicate'], True)
        
        # Verify that a FileReference was created
        self.assertTrue(FileReference.objects.filter(
            original_file=first_file,
            reference_file__original_filename='second.txt'
        ).exists())
        
        logger.debug(f"Successfully uploaded duplicate file: {response.data['id']}")

    def test_upload_empty_file(self):
        """Test uploading an empty file."""
        url = reverse('file-list')
        with open(os.path.join(TEMP_MEDIA_ROOT, 'empty.txt'), 'wb') as f:
            pass  # Create an empty file
        
        with open(os.path.join(TEMP_MEDIA_ROOT, 'empty.txt'), 'rb') as f:
            response = self.client.post(url, {'file': f}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['size'], 0)
        self.assertEqual(response.data['is_duplicate'], False)  # Empty files should still be tracked
        logger.debug(f"Successfully uploaded empty file: {response.data['id']}")

    def test_delete_file(self):
        """Test deleting a file."""
        url = reverse('file-detail', args=[self.file1.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(File.objects.filter(id=self.file1.id).exists())
        logger.debug(f"Successfully deleted file: {self.file1.id}")

    def test_delete_original_with_duplicates(self):
        """Test deleting an original file that has duplicates."""
        # Get the URL for the original file
        url = reverse('file-detail', args=[self.original.id])
        
        # Ensure we have a reference from duplicate to original
        self.assertTrue(FileReference.objects.filter(
            original_file=self.original,
            reference_file=self.duplicate
        ).exists())
        
        # Delete the original
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # The original should be deleted
        self.assertFalse(File.objects.filter(id=self.original.id).exists())
        
        # The duplicate should now be the original (is_duplicate=False)
        updated_duplicate = File.objects.get(id=self.duplicate.id)
        self.assertFalse(updated_duplicate.is_duplicate)
        
        # The reference should be deleted
        self.assertFalse(FileReference.objects.filter(
            original_file=self.original,
            reference_file=self.duplicate
        ).exists())
        
        logger.debug(f"Successfully deleted original file with duplicates: {self.original.id}")

    def test_stats_endpoint(self):
        """Test the stats endpoint."""
        url = reverse('file-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_files', response.data)
        self.assertIn('unique_files', response.data)
        self.assertIn('duplicate_files', response.data)
        self.assertIn('physical_storage', response.data)
        self.assertIn('logical_storage', response.data)
        self.assertIn('storage_saved', response.data)
        
        # We should have 5 total files (4 regular + 1 duplicate)
        self.assertEqual(response.data['total_files'], 5)
        # 4 unique files
        self.assertEqual(response.data['unique_files'], 4)
        # 1 duplicate file
        self.assertEqual(response.data['duplicate_files'], 1)
        
        logger.debug(f"Stats endpoint returned: {response.data}")

    def test_error_handling_missing_file(self):
        """Test error handling when trying to access a non-existent file."""
        url = reverse('file-detail', args=[999999])  # Non-existent ID
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        logger.debug("Successfully handled 404 for missing file")

    def test_error_handling_invalid_filter(self):
        """Test error handling for invalid filter parameters."""
        url = reverse('file-list')
        response = self.client.get(url, {'min_size': 'not-a-number'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        logger.debug("Successfully handled 400 for invalid filter parameter")

    def test_upload_error_no_file(self):
        """Test error handling when no file is provided for upload."""
        url = reverse('file-list')
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        logger.debug("Successfully handled 400 for missing file in upload")


class FileViewSetTest(APITestCase):
    """Test cases for the FileViewSet"""

    def setUp(self):
        """Set up test data"""
        # Create a test file using the fixture
        self.test_file = create_test_file(
            filename='test_file.txt',
            content=b'Original content for testing',
            file_type='text/plain'
        )
        self.file_content = b'Original content for testing'
        self.file_hash = self.test_file.file_hash
        
        # API endpoints
        self.file_list_url = reverse('file-list')
        self.file_detail_url = reverse('file-detail', args=[self.test_file.id])
        self.file_stats_url = reverse('file-stats')

    def tearDown(self):
        """Clean up after tests"""
        cleanup_test_files()

    def test_get_file_list(self):
        """Test getting the list of files"""
        response = self.client.get(self.file_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'test_file.txt')
        self.assertEqual(response.data[0]['file_hash'], self.file_hash)

    def test_get_file_list_with_duplicates(self):
        """Test getting the list of files including duplicates"""
        # Create a duplicate file using fixture
        original_file, duplicate_file, _ = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Duplicate content for testing'
        )
        
        # Default behavior: duplicates are hidden
        response = self.client.get(self.file_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should show both original files (test_file and original_file)
        self.assertEqual(len(response.data), 2)
        
        # Show duplicates
        response = self.client.get(f"{self.file_list_url}?show_duplicates=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # All three files

    def test_get_file_detail(self):
        """Test getting a single file's details"""
        response = self.client.get(self.file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_filename'], 'test_file.txt')
        self.assertEqual(response.data['file_hash'], self.file_hash)
        self.assertEqual(response.data['duplicate_count'], 0)

    def test_delete_file(self):
        """Test deleting a file"""
        response = self.client.delete(self.file_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(File.objects.count(), 0)

    def test_delete_original_with_duplicates(self):
        """Test deleting an original file that has duplicates"""
        # Create a duplicate file pair using fixture
        original_file, duplicate_file, reference = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Content for deletion test'
        )
        
        # Get detail URL for the original file
        original_detail_url = reverse('file-detail', args=[original_file.id])
        
        # Attempt to delete original without confirmation (should fail)
        response = self.client.delete(original_detail_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # Delete with confirmation
        response = self.client.delete(f"{original_detail_url}?confirm_delete_original=true")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # The duplicate should remain but be promoted to original
        remaining_files = File.objects.exclude(id=self.test_file.id)
        self.assertEqual(remaining_files.count(), 1)
        remaining_file = remaining_files.first()
        self.assertEqual(remaining_file.original_filename, 'duplicate.txt')
        self.assertFalse(remaining_file.is_duplicate)  # Should be promoted to original

    def test_upload_file(self):
        """Test uploading a new file"""
        # Create a new file to upload
        upload_file = SimpleUploadedFile(
            name='new_file.txt',
            content=b'New file content for upload test',
            content_type='text/plain'
        )
        
        initial_count = File.objects.count()
        
        # Upload the file
        response = self.client.post(
            self.file_list_url,
            {'file': upload_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), initial_count + 1)
        
        # Check the file was created correctly
        new_file = File.objects.get(original_filename='new_file.txt')
        self.assertEqual(new_file.file_type, 'text/plain')
        self.assertFalse(new_file.is_duplicate)

    def test_upload_duplicate_file(self):
        """Test uploading a duplicate file"""
        # Upload a duplicate of our test file
        duplicate_content = self.file_content  # Same content as test_file
        upload_file = SimpleUploadedFile(
            name='upload_duplicate.txt',
            content=duplicate_content,
            content_type='text/plain'
        )
        
        initial_count = File.objects.count()
        
        # Upload the file
        response = self.client.post(
            self.file_list_url,
            {'file': upload_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should now have original + duplicate
        self.assertEqual(File.objects.count(), initial_count + 1)
        
        # Check the duplicate file was created correctly
        duplicate_files = File.objects.filter(is_duplicate=True)
        self.assertEqual(duplicate_files.count(), 1)
        duplicate = duplicate_files.first()
        self.assertEqual(duplicate.original_filename, 'upload_duplicate.txt')
        self.assertEqual(duplicate.file_hash, self.file_hash)  # Same hash as original
        
        # Should also have a file reference
        self.assertEqual(FileReference.objects.count(), 1)
        reference = FileReference.objects.first()
        self.assertEqual(reference.original_file, self.test_file)
        self.assertEqual(reference.reference_file, duplicate)

    def test_get_storage_stats(self):
        """Test getting storage statistics"""
        # Create a duplicate file pair using fixture
        original_file, duplicate_file, _ = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Content for stats test'
        )
        
        # Get stats
        response = self.client.get(self.file_stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check stats - we should have:
        # - The test_file from setUp
        # - A new original and duplicate pair
        expected_total = 3
        expected_unique = 2
        expected_duplicate = 1
        
        self.assertEqual(response.data['total_files'], expected_total)
        self.assertEqual(response.data['duplicate_files'], expected_duplicate)
        self.assertEqual(response.data['unique_files'], expected_unique)
        
        # Validate storage calculations
        content_size = len(b'Content for stats test')
        test_file_size = len(self.file_content)
        
        # Physical storage should be the size of all original files
        expected_physical = test_file_size + content_size
        self.assertEqual(response.data['physical_storage_bytes'], expected_physical)
        
        # Logical storage should be the size of all files combined
        expected_logical = test_file_size + (content_size * 2)
        self.assertEqual(response.data['logical_storage_bytes'], expected_logical)
        
        # Storage saved should be the size of the duplicate files
        expected_saved = content_size  # Size of one duplicate
        self.assertEqual(response.data['storage_saved_bytes'], expected_saved)
        
        # Storage saved percentage calculation
        expected_percentage = (expected_saved / expected_logical) * 100
        self.assertAlmostEqual(response.data['storage_saved_percentage'], expected_percentage, places=1)

    def test_upload_empty_file(self):
        """Test uploading an empty file"""
        empty_file = SimpleUploadedFile(
            name='empty.txt',
            content=b'',
            content_type='text/plain'
        )
        
        # Upload the file
        response = self.client.post(
            self.file_list_url,
            {'file': empty_file},
            format='multipart'
        )
        
        # Should succeed, empty files are valid
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check file details
        empty_files = File.objects.filter(original_filename='empty.txt')
        self.assertEqual(empty_files.count(), 1)
        empty_file_obj = empty_files.first()
        self.assertEqual(empty_file_obj.size, 0)
        # Empty files have a specific hash
        self.assertEqual(empty_file_obj.file_hash, hashlib.sha256(b'').hexdigest())

    def test_file_filtering(self):
        """Test filtering files by various criteria"""
        # Create multiple test files with different attributes
        doc_file = create_test_file(
            filename='document.docx',
            content=b'Document content',
            file_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        image_file = create_test_file(
            filename='image.jpg',
            content=b'JFIF image data',
            file_type='image/jpeg'
        )
        
        large_file = create_test_file(
            filename='large.bin',
            content=b'X' * 10000,  # 10KB file
            file_type='application/octet-stream'
        )
        
        # Test filtering by file type
        response = self.client.get(f"{self.file_list_url}?file_type=image/jpeg")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'image.jpg')
        
        # Test filtering by min_size
        response = self.client.get(f"{self.file_list_url}?min_size=5000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'large.bin')
        
        # Test filtering by max_size
        response = self.client.get(f"{self.file_list_url}?max_size=1000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should include test_file, doc_file, and image_file
        
        # Test combination of filters
        response = self.client.get(f"{self.file_list_url}?min_size=10&max_size=5000&file_type=text/plain")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'test_file.txt')


class FileDownloadTest(APITestCase):
    """Test cases for file download functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_file = create_test_file(
            filename='download_test.txt',
            content=b'Test content for download',
            file_type='text/plain'
        )
        
        # API endpoint
        self.download_url = reverse('file-download', args=[self.test_file.id])

    def tearDown(self):
        """Clean up test files"""
        cleanup_test_files()

    def test_download_file(self):
        """Test downloading a file"""
        response = self.client.get(self.download_url)
        
        # Check response code and headers
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="{self.test_file.original_filename}"')
        self.assertEqual(response.content, b'Test content for download')

    def test_download_nonexistent_file(self):
        """Test downloading a file that doesn't exist"""
        nonexistent_url = reverse('file-download', args=[99999])
        response = self.client.get(nonexistent_url)
        
        # Should return 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_duplicate_file(self):
        """Test downloading a duplicate file"""
        # Create a duplicate file pair
        original_file, duplicate_file, _ = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Shared content for both files'
        )
        
        # Get the duplicate file download URL
        duplicate_download_url = reverse('file-download', args=[duplicate_file.id])
        
        # Attempt to download the duplicate
        response = self.client.get(duplicate_download_url)
        
        # Should succeed and return the content
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="{duplicate_file.original_filename}"')
        self.assertEqual(response.content, b'Shared content for both files') 