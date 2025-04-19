# Abnormal File Hub

A robust file management system with intelligent deduplication for efficient storage optimization.

![Abnormal File Hub](https://img.shields.io/badge/Abnormal-File%20Hub-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Overview

Abnormal File Hub is a modern file management system that automatically detects and handles duplicate files to save storage space. The application provides a clean interface for uploading, managing, and tracking files while giving insights into storage efficiency through deduplication.

## ✨ Key Features

- **Intelligent Deduplication**: Automatically detects duplicate files using SHA-256 hash verification
- **Storage Optimization**: Saves storage space by storing only one physical copy of duplicate files
- **Real-time Statistics**: Displays storage savings and deduplication efficiency metrics
- **Robust File Management**: Upload, download, search, sort, and filter files with ease
- **RESTful API**: Comprehensive API for programmatic access to all functionality
- **Transaction Safety**: Database transactions ensure data integrity during operations

## 🔧 Technology Stack

### Backend
- Django 4.0.10 (Python)
- Django REST Framework
- SQLite (production deployments can use PostgreSQL)
- Gunicorn

### Frontend
- React
- TypeScript
- TanStack Query (React Query)
- Tailwind CSS
- Heroicons

### Infrastructure
- Docker
- Docker Compose

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/abnormal-file-hub.git
   cd abnormal-file-hub
   ```

2. Start the application using Docker Compose:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/

## 📋 API Documentation

### Files Endpoints

#### List Files
- **GET** `/api/files/`
- Query Parameters:
  - `search`: Search by filename
  - `file_type`: Filter by file type (e.g., 'image/jpeg')
  - `min_size`: Filter by minimum file size (bytes)
  - `max_size`: Filter by maximum file size (bytes)
  - `uploaded_after`: Filter by upload date (YYYY-MM-DD)
  - `uploaded_before`: Filter by upload date (YYYY-MM-DD)
  - `ordering`: Sort by field (e.g., 'size', '-uploaded_at')
  - `is_duplicate`: Show only duplicates (`true`) or originals (`false`)
  - `show_duplicates`: Include duplicate files in the response

#### Upload File
- **POST** `/api/files/`
- Form data:
  - `file`: File to upload

#### Get File Details
- **GET** `/api/files/<file_id>/`

#### Delete File
- **DELETE** `/api/files/<file_id>/`

#### Get Storage Statistics
- **GET** `/api/files/stats/`
- Returns:
  - `total_files`: Total number of files
  - `duplicate_files`: Number of duplicate files
  - `unique_files`: Number of unique files
  - `physical_storage_bytes`: Actual storage used
  - `logical_storage_bytes`: Storage that would be used without deduplication
  - `storage_saved_bytes`: Storage saved through deduplication
  - `storage_saved_percentage`: Percentage of storage saved

## 🔍 How Deduplication Works

1. When a file is uploaded, the system calculates a SHA-256 hash of its contents
2. If an identical file (same hash) already exists in the system:
   - The file is marked as a duplicate
   - A reference is created pointing to the original file
   - The physical file is still stored for redundancy, but marked as a duplicate in the database
3. When accessing files, duplicates are hidden by default (can be shown with query parameters)
4. When deleting:
   - If deleting a duplicate, only its reference is removed
   - If deleting an original with duplicates, one duplicate is promoted to be the new original

## 🔄 Deduplication Integrity System

The application includes a robust system to maintain the integrity of file deduplication:

### Automatic Verification
- Each time the application starts, it automatically verifies and fixes any inconsistencies in the deduplication references
- The `files/apps.py` runs a verification process that ensures all duplicate flags and references are correct

### Fix Duplicates Script

The included `fix_duplicates.py` script provides a comprehensive solution for maintaining and repairing the deduplication system:

```bash
# Run the script in the Docker container
docker exec -it abnormal-file-hub-main-backend-1 python fix_duplicates.py --verbose
```

The script performs the following operations:

1. **Rebuilds file references** from scratch by:
   - Clearing existing references
   - Resetting all duplicate flags
   - Identifying files with identical hashes
   - Setting one file as the original and others as duplicates
   - Creating proper reference relationships

2. **Verifies and fixes inconsistencies** by:
   - Finding files marked as duplicates but missing references
   - Locating references to files that aren't marked as duplicates
   - Automatically repairing these inconsistencies

3. **Recalculates storage statistics** to ensure accurate reporting

Using this script ensures the deduplication system remains intact even if file operations (like deletes) are interrupted or encounter errors.

## 📊 Storage Efficiency

The system provides real-time statistics about storage efficiency:

- Track the total number of files vs. unique files
- See how much storage is physically used vs. logically needed
- Monitor storage savings from deduplication in bytes and percentage

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

## 🔒 Security Considerations

- File hashes are stored securely in the database
- API endpoints use proper authentication (when deploying in production)
- Transactions ensure data integrity during file operations
- Deduplication maintains file access controls between users

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

If you have any questions, feel free to reach out to the maintainers.

---

Built with ❤️ for efficient file management.

