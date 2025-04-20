# Abnormal File Hub Technical Documentation

## Overview
This document outlines the technical architecture for a file storage application with intelligent deduplication capabilities. The system identifies duplicate files based on content hashing and references the original file instead of storing duplicates.

## Technology Stack

### Backend
- **Framework**: Django REST Framework
- **Language**: Python 3.10
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **File Storage**: Local filesystem with configurable paths
- **Containerization**: Docker and docker-compose

### Frontend
- **Framework**: React
- **Language**: TypeScript
- **State Management**: React Query for server state
- **Styling**: Tailwind CSS
- **Build Tool**: Create React App

## Core Modules

### 1. File Management Module

#### File Model
```python
# backend/files/models.py
class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=255)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64)
    is_duplicate = models.BooleanField(default=False)
    
    # Properties for duplicate calculations
    @property
    def duplicate_count(self):
        if self.is_duplicate:
            return 0
        return FileReference.objects.filter(original_file=self).count()
    
    @property
    def storage_saved(self):
        return self.size * self.duplicate_count
```

#### FileReference Model
```python
# backend/files/models.py
class FileReference(models.Model):
    original_file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='original_references')
    reference_file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='duplicate_references')
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. API Endpoints

#### File List and Upload
```python
# backend/files/views.py
class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    
    def get_queryset(self):
        # Filter options for duplicates
        show_duplicates = self.request.query_params.get('show_duplicates', 'false').lower() == 'true'
        if not show_duplicates:
            queryset = queryset.filter(is_duplicate=False)
        return queryset
    
    def create(self, request):
        # File upload with deduplication logic
        file_obj = request.FILES.get('file')
        file_hash = self._calculate_file_hash(file_obj)
        
        # Check for existing file with same hash
        existing_file = File.objects.filter(file_hash=file_hash, is_duplicate=False).first()
        if existing_file:
            # Create duplicate reference
            # ...
        else:
            # Save new file
            # ...
```

#### Storage Statistics
```python
# backend/files/views.py
@action(detail=False, methods=['get'])
def stats(self, request):
    # Get total files count
    total_files = File.objects.count()
    duplicate_files = File.objects.filter(is_duplicate=True).count()
    
    # Calculate storage metrics
    physical_storage = sum(file.size for file in File.objects.filter(is_duplicate=False))
    logical_storage = sum(file.size for file in File.objects.all())
    
    return Response({
        'total_files': total_files,
        'duplicate_files': duplicate_files,
        'unique_files': total_files - duplicate_files,
        'physical_storage_bytes': physical_storage,
        'logical_storage_bytes': logical_storage,
        'storage_saved_bytes': logical_storage - physical_storage,
        'storage_saved_percentage': (
            ((logical_storage - physical_storage) / logical_storage) * 100 
            if logical_storage > 0 else 0
        )
    })
```

### 3. Frontend Components

#### File List Component
```typescript
// frontend/src/components/FileList.tsx
export const FileList: React.FC = () => {
  const [filters, setFilters] = useState<FileFilters>({});
  const [showDuplicates, setShowDuplicates] = useState(false);
  
  const { data, isLoading, error } = useQuery(
    ['files', filters, showDuplicates],
    () => fileService.getFiles({ ...filters, show_duplicates: showDuplicates })
  );
  
  // Rendering logic
  // ...
}
```

#### File Upload Component
```typescript
// frontend/src/components/FileUpload.tsx
export const FileUpload: React.FC = () => {
  const queryClient = useQueryClient();
  
  const uploadMutation = useMutation(
    (file: File) => fileService.uploadFile(file),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('files');
        queryClient.invalidateQueries('stats');
      }
    }
  );
  
  // Upload handling logic
  // ...
}
```

## Deduplication System

### Hash Calculation
```python
def _calculate_file_hash(self, file_obj):
    """Calculate SHA-256 hash of file contents for deduplication"""
    hasher = hashlib.sha256()
    
    # Reset file pointer to beginning
    file_obj.seek(0)
    
    for chunk in file_obj.chunks():
        hasher.update(chunk)
        
    # Reset file pointer to beginning for later use
    file_obj.seek(0)
    
    return hasher.hexdigest()
```

### Duplicate Detection Workflow
1. User uploads a file
2. System calculates SHA-256 hash of file contents
3. System checks database for existing files with same hash
4. If duplicate found:
   - Create new `File` entry with `is_duplicate=True`
   - Create `FileReference` entry linking to original file
   - Return success response without storing duplicate file
5. If no duplicate found:
   - Store file normally
   - Create `File` entry with `is_duplicate=False`

## Logging System

```python
# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'files': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Docker Deployment

### Docker Compose Setup
```yaml
services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - backend_storage:/app/media
      - backend_static:/app/staticfiles
      - backend_data:/app/data
    environment:
      - DJANGO_DEBUG=True
      - DJANGO_SECRET_KEY=insecure-dev-only-key

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
    depends_on:
      - backend

volumes:
  backend_storage:
  backend_static:
  backend_data:
```

## Development Workflow
1. Clone repository
2. Run `docker-compose up -d` to start all services
3. Access frontend at `http://localhost:3000`
4. Access backend API at `http://localhost:8000/api`

## Testing Strategy
- Backend unit tests for models and business logic
- API endpoint tests for validation
- Frontend component tests
- End-to-end tests for critical user workflows

## Security Considerations
- File type validation and sanitization
- Proper error handling to avoid information disclosure
- Rate limiting for upload endpoints
- Content validation where applicable 