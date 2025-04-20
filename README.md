# File Storage Application with Deduplication

A modern file storage application with deduplication capabilities, built with Django REST Framework and React.

## Overview

This application allows users to:

- Upload files through a web interface
- Automatically deduplicate files based on content
- Track saved storage space through deduplication
- Download and manage uploaded files
- Get statistics on storage usage and efficiency

## Architecture

- **Backend**: Django REST Framework
  - File deduplication based on SHA-256 hash comparison
  - Efficient storage management with reference tracking
  - API endpoints for file management and stats

- **Frontend**: React/TypeScript
  - Modern UI with file upload capability
  - File listing and management
  - Storage statistics visualization

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd file-storage-app
   ```

2. Start the application:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/

## File Deduplication System

The application uses a content-based deduplication system:

1. When a file is uploaded, a SHA-256 hash of its content is calculated
2. If a file with the same hash already exists:
   - The physical file is not stored again
   - A reference to the original file is created
   - The duplicate is marked as such in the database
3. When accessing a duplicate file:
   - The content is served from the original file
   - All metadata (filename, upload date) is preserved for the duplicate

### Benefits

- Significant storage savings for duplicate content
- Transparent to users (duplicates appear as normal files)
- Allows tracking of deduplication efficiency

## Management Commands

A set of management commands is provided for system management and testing:

### Using the Management Commands

Use the provided shell script to run management commands:

```bash
# Show help
./run_management_commands.sh help

# Generate test data
./run_management_commands.sh generate --unique=10 --duplicates=20 --clean

# Analyze storage usage
./run_management_commands.sh analyze --detail

# Delete duplicate files (dry run)
./run_management_commands.sh delete --dry-run
```

See `backend/files/management/commands/README.md` for detailed command documentation.

## API Endpoints

- `GET /api/files/` - List files with filtering
- `POST /api/files/` - Upload new file with deduplication
- `DELETE /api/files/{id}/` - Delete file with reference management
- `GET /api/files/stats/` - Get storage statistics
- `GET /api/files/{id}/download/` - Download a file

## Development

### Project Structure

- `backend/` - Django REST Framework backend
  - `core/` - Main Django settings
  - `files/` - File app with models, views, and serializers
- `frontend/` - React frontend
  - `src/components/` - React components
  - `src/services/` - API integration services

### Testing

Run the tests using:

```bash
docker-compose exec backend python manage.py test
```

Or use the test data generation command to create test data:

```bash
./run_management_commands.sh generate --unique=5 --duplicates=10
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

