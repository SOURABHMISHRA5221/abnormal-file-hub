import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fileService, StorageStats as StorageStatsType } from '../services/fileService';
import { ChartBarIcon, DocumentDuplicateIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

export const StorageStats: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<StorageStatsType>({
    queryKey: ['fileStats'],
    queryFn: fileService.getStats,
  });

  if (isLoading) {
    return (
      <div className="abnormal-card p-4 mb-6 animate-pulse">
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
    <div className="abnormal-card p-6">
      <div className="flex items-center mb-6">
        <ChartBarIcon className="h-6 w-6 text-primary-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900">Storage Optimization</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-50 rounded-lg p-5 border border-blue-100 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-blue-100 rounded-md p-2">
              <DocumentDuplicateIcon className="h-5 w-5 text-blue-700" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-800 mb-1">File Statistics</p>
              <p className="text-2xl font-bold text-blue-900">{stats.total_files} Files</p>
              <div className="mt-2 text-sm text-blue-700">
                <div>{stats.unique_files} Unique / {stats.duplicate_files} Duplicates</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-5 border border-green-100 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-green-100 rounded-md p-2">
              <ArrowTrendingUpIcon className="h-5 w-5 text-green-700" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800 mb-1">Storage Saved</p>
              <p className="text-2xl font-bold text-green-900">{formatBytes(stats.storage_saved_bytes)}</p>
              <div className="mt-2 text-sm text-green-700">
                <div>{stats.storage_saved_percentage}% of logical storage</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-5 border border-purple-100 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-purple-100 rounded-md p-2">
              <svg className="h-5 w-5 text-purple-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-purple-800 mb-1">Physical vs Logical</p>
              <p className="text-2xl font-bold text-purple-900">{formatBytes(stats.physical_storage_bytes)}</p>
              <div className="mt-2 text-sm text-purple-700">
                <div>of {formatBytes(stats.logical_storage_bytes)} logical storage</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 