import React, { useState, useEffect } from 'react';
import { fileService, FileFilters, DeleteFileParams } from '../services/fileService';
import { File as FileType } from '../types/file';
import { DocumentIcon, TrashIcon, ArrowDownTrayIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SearchFilter } from './SearchFilter';

export const FileList: React.FC = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<FileFilters>({});
  const [uniqueFileTypes, setUniqueFileTypes] = useState<string[]>([]);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [duplicateConfirmation, setDuplicateConfirmation] = useState<{
    fileId: string;
    count: number;
  } | null>(null);

  // Query for fetching files
  const { data: files, isLoading, error } = useQuery<FileType[]>({
    queryKey: ['files', filters],
    queryFn: () => fileService.getFiles(filters)
  });

  // Update unique file types when files data changes
  useEffect(() => {
    if (files) {
      const fileTypes = [...new Set(files.map(file => file.file_type))];
      setUniqueFileTypes(fileTypes);
    }
  }, [files]);

  // Mutation for deleting files
  const deleteMutation = useMutation({
    mutationFn: fileService.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      queryClient.invalidateQueries({ queryKey: ['fileStats'] });
    },
  });

  // Mutation for downloading files
  const downloadMutation = useMutation({
    mutationFn: ({ fileUrl, filename }: { fileUrl: string; filename: string }) =>
      fileService.downloadFile(fileUrl, filename),
  });

  const handleDelete = async (id: string, forceDelete = false) => {
    try {
      // Clear previous errors
      setDeleteError(null);
      
      // Create properly typed params object
      const deleteParams: DeleteFileParams = {
        id,
        params: forceDelete ? { confirm_delete_original: 'true' } : undefined
      };
      
      await deleteMutation.mutateAsync(deleteParams);
      
      // Reset confirmation state on successful deletion
      setDuplicateConfirmation(null);
    } catch (err: any) {
      console.error('Delete error:', err);
      
      // Handle 409 Conflict - Original file with duplicates
      if (err.response && err.response.status === 409) {
        const data = err.response.data;
        setDuplicateConfirmation({
          fileId: id,
          count: data.duplicate_count
        });
      } else {
        setDeleteError('Failed to delete file. Please try again.');
      }
    }
  };
  
  // Add function to handle confirmation
  const handleConfirmDelete = () => {
    if (duplicateConfirmation) {
      handleDelete(duplicateConfirmation.fileId, true);
    }
  };
  
  // Add function to cancel deletion
  const handleCancelDelete = () => {
    setDuplicateConfirmation(null);
  };

  const handleDownload = async (fileUrl: string, filename: string) => {
    try {
      await downloadMutation.mutateAsync({ fileUrl, filename });
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const handleFilterChange = (newFilters: FileFilters) => {
    setFilters(newFilters);
  };

  // Format bytes to human-readable sizes
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-8 bg-gray-200 rounded"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">Failed to load files. Please try again.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const filesList = files || [];

  return (
    <div className="p-6">
      <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
      
      {deleteError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{deleteError}</p>
            </div>
          </div>
        </div>
      )}
      
      {duplicateConfirmation && (
        <div className="bg-amber-50 border border-amber-300 rounded-md p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-amber-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-amber-800">Warning: File has duplicates</h3>
              <div className="mt-2 text-sm text-amber-700">
                <p>
                  This file has {duplicateConfirmation.count} duplicate{duplicateConfirmation.count !== 1 ? 's' : ''}. 
                  It's recommended to delete the duplicates first.
                </p>
                <p className="mt-2">
                  If you proceed, one of the duplicates will become the new original file.
                </p>
              </div>
              <div className="mt-4 flex space-x-3">
                <button
                  type="button"
                  onClick={handleConfirmDelete}
                  className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500"
                >
                  Proceed with deletion
                </button>
                <button
                  type="button"
                  onClick={handleCancelDelete}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
      {filesList.length === 0 ? (
        <div className="text-center py-12">
          <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No files</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by uploading a file
          </p>
        </div>
      ) : (
        <div className="mt-6 flow-root">
          <ul className="-my-5 divide-y divide-gray-200">
            {filesList.map((file) => (
              <li key={file.id} className="py-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {file.is_duplicate ? (
                      <DocumentDuplicateIcon className="h-8 w-8 text-amber-400" />
                    ) : (
                      <DocumentIcon className="h-8 w-8 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.original_filename}
                      {file.is_duplicate && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                          Duplicate
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-500">
                      {file.file_type} • {formatBytes(file.size)}
                    </p>
                    <p className="text-sm text-gray-500">
                      Uploaded {new Date(file.uploaded_at).toLocaleString()}
                    </p>
                    {!file.is_duplicate && file.duplicate_count > 0 && (
                      <p className="text-sm text-green-600">
                        {file.duplicate_count} duplicate{file.duplicate_count !== 1 ? 's' : ''} • {formatBytes(file.storage_saved)} saved
                      </p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleDownload(file.file, file.original_filename)}
                      disabled={downloadMutation.isPending}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                      Download
                    </button>
                    <button
                      onClick={() => handleDelete(file.id)}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <TrashIcon className="h-4 w-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}; 