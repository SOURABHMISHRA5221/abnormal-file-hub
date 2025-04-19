import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fileService, StorageStats as StorageStatsType } from '../services/fileService';
import { ChartBarIcon } from '@heroicons/react/24/outline';

export const StorageStats: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<StorageStatsType>({
    queryKey: ['fileStats'],
    queryFn: fileService.getStats,
  });

  if (isLoading) {
    return (
      <div className="bg-white shadow-sm rounded-lg p-4 mb-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return null;
  }

  // Format bytes to human-readable sizes
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white shadow-sm rounded-lg p-4 mb-6">
      <div className="flex items-center mb-4">
        <ChartBarIcon className="h-6 w-6 text-primary-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900">Storage Optimization</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm font-medium text-blue-700 mb-1">File Statistics</p>
          <p className="text-2xl font-bold text-blue-900">{stats.total_files} Files</p>
          <div className="mt-2 text-sm text-blue-600">
            <div>{stats.unique_files} Unique / {stats.duplicate_files} Duplicates</div>
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm font-medium text-green-700 mb-1">Storage Saved</p>
          <p className="text-2xl font-bold text-green-900">{formatBytes(stats.storage_saved_bytes)}</p>
          <div className="mt-2 text-sm text-green-600">
            <div>{stats.storage_saved_percentage}% of logical storage</div>
          </div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm font-medium text-purple-700 mb-1">Physical vs Logical</p>
          <p className="text-2xl font-bold text-purple-900">{formatBytes(stats.physical_storage_bytes)}</p>
          <div className="mt-2 text-sm text-purple-600">
            <div>of {formatBytes(stats.logical_storage_bytes)} logical storage</div>
          </div>
        </div>
      </div>
    </div>
  );
}; 