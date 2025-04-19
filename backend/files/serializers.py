from rest_framework import serializers
from .models import File, FileReference

class FileSerializer(serializers.ModelSerializer):
    duplicate_count = serializers.IntegerField(read_only=True)
    storage_saved = serializers.IntegerField(read_only=True)
    is_duplicate = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = File
        fields = ['id', 'file', 'original_filename', 'file_type', 'size', 'uploaded_at', 
                  'duplicate_count', 'storage_saved', 'is_duplicate', 'file_hash']
        read_only_fields = ['id', 'uploaded_at', 'duplicate_count', 'storage_saved', 'is_duplicate']
        
class FileReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileReference
        fields = ['id', 'original_file', 'reference_file', 'created_at']
        read_only_fields = ['id', 'created_at'] 