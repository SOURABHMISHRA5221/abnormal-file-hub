# Abnormal File Hub

![File Deduplication](https://img.shields.io/badge/Deduplication-Enabled-brightgreen)
![Django](https://img.shields.io/badge/Backend-Django-092E20)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED)

A modern, efficient file storage application with intelligent deduplication capabilities. Upload files through a clean interface while the system automatically detects and manages duplicates, saving valuable storage space.

## ✨ Features

- **Smart Deduplication**: Automatically detects identical files using SHA-256 hash verification
- **Storage Optimization**: Stores only one physical copy of duplicate files
- **Real-time Statistics**: Track storage savings and deduplication efficiency
- **Flexible Search**: Filter files by name, type, size, upload date
- **Docker Ready**: Spin up with a single command using Docker Compose
- **Management Tools**: Analyze storage usage and generate test data

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SOURABHMISHRA5221/abnormal-file-hub.git
   cd abnormal-file-hub
   ```

2. **Launch the application**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend UI: [http://localhost:3000](http://localhost:3000)
   - API Endpoints: [http://localhost:8000/api/](http://localhost:8000/api/)

## 🔍 How It Works

### Deduplication Process

1. When a file is uploaded, a SHA-256 hash of its content is calculated
2. The system checks if a file with the same hash already exists:
   - If unique: The file is stored normally
   - If duplicate: A reference to the original file is created, saving storage space
3. All files appear in the user interface with appropriate metadata
4. Storage statistics show real-time savings from deduplication

### System Architecture

- **Backend**: Django REST Framework (Python)
  - Models for file and reference tracking
  - API endpoints for file operations
  - Deduplication logic and storage optimization

- **Frontend**: React with TypeScript
  - Intuitive file upload interface
  - Responsive file listing with filters
  - Storage statistics visualization

## 🛠️ Management Tools

The application includes powerful management commands for testing and administration:

```bash
# Generate test data with configurable parameters
./run_management_commands.sh generate --unique=10 --duplicates=20 --clean

# Analyze storage usage with detailed reporting
./run_management_commands.sh analyze --detail

# Safely manage duplicate files
./run_management_commands.sh delete --dry-run
```

## 📊 Storage Statistics

The system provides detailed statistics about storage efficiency:

- Total files vs. unique files
- Physical storage used vs. logical storage required
- Storage saved through deduplication (bytes and percentage)
- File type distribution analysis

## 🔌 API Endpoints

The backend provides comprehensive API endpoints:

- `GET /api/files/` - List all files with powerful filtering options
- `POST /api/files/` - Upload files with automatic deduplication
- `DELETE /api/files/{id}/` - Delete files with reference management
- `GET /api/files/stats/` - Get storage statistics
- `GET /api/files/{id}/download/` - Download file content

## 💻 Development

### Project Structure

```
abnormal-file-hub/
├── backend/              # Django REST Framework backend
│   ├── core/             # Django settings
│   ├── files/            # File management app
│   │   ├── models.py     # Data models
│   │   ├── views.py      # API endpoints
│   │   └── management/   # Management commands
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   └── services/     # API integration
├── docs/                 # Documentation
└── docker-compose.yml    # Docker configuration
```

### Testing

Generate test data and verify functionality:

```bash
# Run backend tests
docker-compose exec backend python manage.py test

# Generate test data
./run_management_commands.sh generate --unique=5 --duplicates=10

# Run test sequence
./test_commands.sh
```

## 📖 Documentation

For more detailed information, check the documentation files:

- [Management Commands](backend/files/management/commands/README.md)
- [Technical Documentation](docs/technical.md)
- [Project Status](docs/status.md)

---

Built with ❤️ for efficient file management. Contributions welcome!

