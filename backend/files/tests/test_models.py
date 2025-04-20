import os
import logging
import tempfile
from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from files.models import File, FileReference
from files.tests.fixtures import create_test_file, create_file_pair, cleanup_test_files

# Set up logging
logger = logging.getLogger(__name__)

# Create a temporary directory for test uploads
TEMP_MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'test_models')
os.makedirs(TEMP_MEDIA_ROOT, exist_ok=True)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FileModelTest(TestCase):
    def setUp(self):
        logger.debug("Setting up File model tests")
        self.file1 = create_test_file(
            filename='test1.txt',
            content=b'Test content for file 1',
            file_type='text/plain'
        )
        
        # Create a duplicate pair for testing references
        self.original, self.duplicate, self.reference = create_file_pair(
            original_filename='original.txt',
            duplicate_filename='duplicate.txt',
            content=b'Duplicate content for testing'
        )
        
        logger.debug(f"Test setup complete with {File.objects.count()} files")
    
    def tearDown(self):
        cleanup_test_files()
        logger.debug("Test cleanup complete")
    
    def test_file_model_creation(self):
        """Test that a File model instance can be created correctly."""
        test_file = create_test_file(
            filename='new_file.txt',
            content=b'New file content for testing',
            file_type='text/plain'
        )
        
        self.assertEqual(test_file.original_filename, 'new_file.txt')
        self.assertEqual(test_file.file_type, 'text/plain')
        self.assertEqual(test_file.size, len(b'New file content for testing'))
        self.assertFalse(test_file.is_duplicate)
        self.assertIsNotNone(test_file.file_hash)
        
        logger.debug(f"Created file with hash: {test_file.file_hash}")
    
    def test_file_hash_calculation(self):
        """Test that file hash is calculated correctly on save."""
        # Create a file with known content to verify hash
        content = b'Test content for hash calculation'
        test_file = create_test_file(
            filename='hash_test.txt',
            content=content,
            file_type='text/plain'
        )
        
        # Manually calculate the expected hash
        import hashlib
        expected_hash = hashlib.sha256(content).hexdigest()
        
        self.assertEqual(test_file.file_hash, expected_hash)
        logger.debug(f"Hash verification successful: {test_file.file_hash}")
    
    def test_duplicate_count_property(self):
        """Test the duplicate_count property of the File model."""
        # Create additional duplicates to test counting
        for i in range(3):
            create_test_file(
                filename=f'duplicate{i}.txt',
                content=b'Duplicate content for testing',
                file_type='text/plain'
            )
        
        # Refresh the original from the database
        self.original.refresh_from_db()
        
        # The original should have 4 duplicates (the initial one + 3 new ones)
        self.assertEqual(self.original.duplicate_count, 4)
        logger.debug(f"Original file has {self.original.duplicate_count} duplicates")
    
    def test_storage_saved_property(self):
        """Test the storage_saved property of the File model."""
        # Create a file with known size
        content = b'x' * 1000  # 1KB content
        original = create_test_file(
            filename='original_size.txt',
            content=content,
            file_type='text/plain'
        )
        
        # Create multiple duplicates with the same content
        for i in range(5):
            create_test_file(
                filename=f'duplicate_size{i}.txt',
                content=content,
                file_type='text/plain'
            )
        
        # Refresh the original from the database
        original.refresh_from_db()
        
        # Storage saved should be 5 * 1000 = 5000 bytes (5 duplicates × file size)
        self.assertEqual(original.storage_saved, 5000)
        logger.debug(f"Storage saved: {original.storage_saved} bytes")
    
    def test_file_path_generation(self):
        """Test that the file upload path is generated correctly."""
        test_file = create_test_file(
            filename='path_test.txt',
            content=b'Test content for path generation',
            file_type='text/plain'
        )
        
        # The file path should include the file hash
        self.assertIn(test_file.file_hash, test_file.file.name)
        logger.debug(f"File path generated correctly: {test_file.file.name}")
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        empty_file = create_test_file(
            filename='empty.txt',
            content=b'',
            file_type='text/plain'
        )
        
        self.assertEqual(empty_file.size, 0)
        self.assertEqual(empty_file.file_hash, hashlib.sha256(b'').hexdigest())
        self.assertFalse(empty_file.is_duplicate)
        logger.debug("Empty file handling successful")
    
    def test_file_reference_creation(self):
        """Test creation of a FileReference."""
        # Create a new reference to test creation
        new_duplicate = create_test_file(
            filename='new_duplicate.txt',
            content=b'Duplicate content for testing',
            file_type='text/plain'
        )
        
        # Verify that a reference was created automatically
        reference_exists = FileReference.objects.filter(
            original_file=self.original,
            reference_file=new_duplicate
        ).exists()
        
        self.assertTrue(reference_exists)
        self.assertTrue(new_duplicate.is_duplicate)
        logger.debug("FileReference creation successful")
    
    def test_file_reference_deletion(self):
        """Test deletion of a FileReference when a duplicate is deleted."""
        # The count of references before deletion
        initial_ref_count = FileReference.objects.filter(
            original_file=self.original
        ).count()
        
        # Delete the duplicate
        self.duplicate.delete()
        
        # The count of references after deletion should be one less
        new_ref_count = FileReference.objects.filter(
            original_file=self.original
        ).count()
        
        self.assertEqual(new_ref_count, initial_ref_count - 1)
        # The reference should not exist anymore
        self.assertFalse(FileReference.objects.filter(
            original_file=self.original,
            reference_file=self.duplicate
        ).exists())
        logger.debug("FileReference deletion successful")
    
    def test_file_deletion_cascade(self):
        """Test that references are deleted when an original file is deleted."""
        # Create additional duplicates for testing
        for i in range(2):
            create_test_file(
                filename=f'cascade{i}.txt',
                content=b'Duplicate content for testing',
                file_type='text/plain'
            )
        
        # Count references before deletion
        initial_ref_count = FileReference.objects.filter(
            original_file=self.original
        ).count()
        self.assertTrue(initial_ref_count > 0)
        
        # Get all duplicate IDs for later checking
        duplicate_ids = list(FileReference.objects.filter(
            original_file=self.original
        ).values_list('reference_file_id', flat=True))
        
        # Delete the original
        original_id = self.original.id
        self.original.delete()
        
        # The original should be deleted
        self.assertFalse(File.objects.filter(id=original_id).exists())
        
        # All references should be deleted
        self.assertEqual(
            FileReference.objects.filter(original_file_id=original_id).count(), 
            0
        )
        
        # The duplicates should still exist, but one should become the new original
        for duplicate_id in duplicate_ids:
            duplicate_exists = File.objects.filter(id=duplicate_id).exists()
            self.assertTrue(duplicate_exists)
        
        # One of the duplicates should now be the original (is_duplicate=False)
        new_original_count = File.objects.filter(
            id__in=duplicate_ids, 
            is_duplicate=False
        ).count()
        self.assertEqual(new_original_count, 1)
        
        logger.debug("File deletion cascade test successful")


class FileReferenceModelTest(TestCase):
    def setUp(self):
        """Set up test environment for file reference tests."""
        self.original_file, self.duplicate_file, self.file_reference = create_file_pair()
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_files()
        
    def test_create_file_reference(self):
        """Test file reference creation."""
        self.assertIsNotNone(self.file_reference.id)
        self.assertEqual(self.file_reference.original_file, self.original_file)
        self.assertEqual(self.file_reference.reference_file, self.duplicate_file)
        
    def test_cascade_delete_original(self):
        """Test that deleting the original file also deletes its references."""
        reference_id = self.file_reference.id
        self.original_file.delete()
        
        # Reference should be deleted
        with self.assertRaises(FileReference.DoesNotExist):
            FileReference.objects.get(id=reference_id)
            
    def test_cascade_delete_reference(self):
        """Test that deleting a duplicate file also deletes the reference."""
        reference_id = self.file_reference.id
        self.duplicate_file.delete()
        
        # Reference should be deleted
        with self.assertRaises(FileReference.DoesNotExist):
            FileReference.objects.get(id=reference_id) 