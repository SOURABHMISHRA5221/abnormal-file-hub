import axios from 'axios';
import { File as FileType } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export interface FileFilters {
  search?: string;
  file_type?: string;
  min_size?: number;
  max_size?: number;
  uploaded_after?: string;
  uploaded_before?: string;
  ordering?: string;
  is_duplicate?: boolean;
}

export interface StorageStats {
  total_files: number;
  duplicate_files: number;
  unique_files: number;
  physical_storage_bytes: number;
  logical_storage_bytes: number;
  storage_saved_bytes: number;
  storage_saved_percentage: number;
}

export const fileService = {
  async uploadFile(file: File): Promise<FileType> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_URL}/files/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getFiles(filters?: FileFilters): Promise<FileType[]> {
    // Build query params from filters
    const params = new URLSearchParams();
    if (filters) {
      if (filters.search) params.append('search', filters.search);
      if (filters.file_type) params.append('file_type', filters.file_type);
      if (filters.min_size !== undefined) params.append('min_size', filters.min_size.toString());
      if (filters.max_size !== undefined) params.append('max_size', filters.max_size.toString());
      if (filters.uploaded_after) params.append('uploaded_after', filters.uploaded_after);
      if (filters.uploaded_before) params.append('uploaded_before', filters.uploaded_before);
      if (filters.ordering) params.append('ordering', filters.ordering);
      if (filters.is_duplicate !== undefined) params.append('is_duplicate', filters.is_duplicate.toString());
    }

    const response = await axios.get(`${API_URL}/files/`, { params });
    return response.data;
  },

  async deleteFile(id: string): Promise<void> {
    await axios.delete(`${API_URL}/files/${id}/`);
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await axios.get(fileUrl, {
        responseType: 'blob',
      });
      
      // Create a blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },

  async getStats(): Promise<StorageStats> {
    const response = await axios.get(`${API_URL}/files/stats/`);
    return response.data;
  }
}; 