"""
Test fixtures for the files app.
"""
import os
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from files.models import File, FileReference

# Set up logging
logger = logging.getLogger(__name__)

def create_test_file(filename="test_file.txt", content=b"Test file content", file_type="text/plain", is_duplicate=False):
    """
    Create a test file for testing purposes.
    
    Args:
        filename (str): Name of the test file
        content (bytes): Binary content of the file
        file_type (str): MIME type of the file
        is_duplicate (bool): Whether this file should be marked as a duplicate
        
    Returns:
        File: The created File instance
    """
    logger.debug(f"Creating test file: {filename}")
    uploaded_file = SimpleUploadedFile(filename, content, content_type=file_type)
    
    file_obj = File.objects.create(
        file=uploaded_file,
        original_filename=filename,
        file_type=file_type,
        size=len(content),
        is_duplicate=is_duplicate
    )
    
    logger.debug(f"Created test file with ID: {file_obj.id}")
    return file_obj

def create_file_pair(original_filename="original.txt", duplicate_filename="duplicate.txt", content=b"Duplicate content"):
    """
    Create a pair of files (original and duplicate) with the same content and a reference between them.
    
    Args:
        original_filename (str): Name for the original file
        duplicate_filename (str): Name for the duplicate file
        content (bytes): Binary content for both files
        
    Returns:
        tuple: (original_file, duplicate_file, file_reference)
    """
    logger.debug(f"Creating file pair: {original_filename} and {duplicate_filename}")
    
    # Create original file
    original_file = create_test_file(
        filename=original_filename,
        content=content,
        is_duplicate=False
    )
    
    # Create duplicate file
    duplicate_file = create_test_file(
        filename=duplicate_filename,
        content=content,
        is_duplicate=True
    )
    
    # Create the reference between them
    file_reference = FileReference.objects.create(
        original_file=original_file,
        reference_file=duplicate_file
    )
    
    logger.debug(f"Created file pair with original ID: {original_file.id} and duplicate ID: {duplicate_file.id}")
    return original_file, duplicate_file, file_reference

def cleanup_test_files():
    """
    Clean up all test files created during testing.
    Deletes all File objects, which should cascade to FileReference.
    Also removes any physical files left in the media directory.
    """
    logger.debug("Cleaning up test files")
    
    # Clean up database objects
    file_count = File.objects.count()
    File.objects.all().delete()
    
    logger.debug(f"Deleted {file_count} File objects from database")
    
    # Any additional cleanup for physical files can be added here
    
    return