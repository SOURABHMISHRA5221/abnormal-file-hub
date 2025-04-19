#!/usr/bin/env python
import os
import sys
import logging
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Get the logger
logger = logging.getLogger('files')

# Create test log entries
logger.debug("DEBUG: Test debug message from debug_logger.py")
logger.info("INFO: Test info message from debug_logger.py")
logger.warning("WARNING: Test warning message from debug_logger.py")
logger.error("ERROR: Test error message from debug_logger.py")

print("Logging test completed. Check the log file at /app/logs/debug.log")

# Also create a direct file for testing
with open('/app/logs/test_direct.log', 'w') as f:
    f.write("Direct file write test\n")

print("Direct file write test completed. Check /app/logs/test_direct.log") 