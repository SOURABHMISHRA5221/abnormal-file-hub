# File Management Commands

Django management commands for the file storage application with deduplication capabilities.

## Available Commands

### generate_test_data

Generates test files with duplicates for testing the system.

```bash
# Generate 10 unique files and 20 duplicates (default sizes)
python manage.py generate_test_data

# Generate 5 unique files and 10 duplicates with 5KB base size
python manage.py generate_test_data --unique=5 --duplicates=10 --size=5120

# Clean existing test data before generating new data
python manage.py generate_test_data --clean
```

Options:
- `--unique`: Number of unique files to create (default: 10)
- `--duplicates`: Number of duplicate files to create (default: 20)
- `--size`: Base size of files in bytes (default: 1024)
- `--clean`: Clean existing test data before creating new files

### analyze_storage

Analyzes storage usage and deduplication efficiency.

```bash
# Generate basic storage report
python manage.py analyze_storage

# Generate detailed report with file type distribution
python manage.py analyze_storage --detail

# Show files with at least 3 duplicates
python manage.py analyze_storage --detail --min-duplicates=3
```

Options:
- `--detail`: Show detailed analysis by file type and top files with duplicates
- `--min-duplicates`: Minimum number of duplicates to include in the top files report (default: 1)

### delete_duplicates

Deletes all duplicate files from the system.

```bash
# Show what would be deleted without performing the actual deletion
python manage.py delete_duplicates --dry-run

# Delete all duplicate files
python manage.py delete_duplicates
```

Options:
- `--dry-run`: Show what would be deleted without performing the actual deletion

## Development Workflow

1. Generate test data for development and testing:
   ```bash
   python manage.py generate_test_data --clean
   ```

2. Analyze storage usage and deduplication efficiency:
   ```bash
   python manage.py analyze_storage --detail
   ```

3. Run the application and test file upload/download functionality

4. Check deduplication effectiveness by analyzing storage again

## Logging

All commands use Python's logging framework to log operations. Log messages are categorized by:

- INFO: Regular operations like file creation/deletion
- WARNING: Non-critical issues like missing files
- ERROR: Critical issues that prevent successful command execution

View detailed logs in the Django log files based on your logging configuration. 