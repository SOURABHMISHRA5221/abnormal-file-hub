import React, { useState } from 'react';
import { FileFilters } from '../services/fileService';
import { FunnelIcon, MagnifyingGlassIcon, ArrowsUpDownIcon, XMarkIcon } from '@heroicons/react/24/outline';

// Get unique file types for filtering
const DEFAULT_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
];

interface SearchFilterProps {
  onFilterChange: (filters: FileFilters) => void;
  fileTypes: string[];
}

export const SearchFilter: React.FC<SearchFilterProps> = ({ 
  onFilterChange,
  fileTypes = DEFAULT_FILE_TYPES
}) => {
  const [filters, setFilters] = useState<FileFilters>({});
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const updatedFilters = { ...filters, search: e.target.value };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const handleFileTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const updatedFilters = { ...filters, file_type: e.target.value || undefined };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const handleSizeChange = (field: 'min_size' | 'max_size', value: string) => {
    // Convert KB to bytes
    const sizeInBytes = value ? parseInt(value) * 1024 : undefined;
    const updatedFilters = { ...filters, [field]: sizeInBytes };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  const handleDateChange = (field: 'uploaded_after' | 'uploaded_before', value: string) => {
    const updatedFilters = { ...filters, [field]: value || undefined };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const updatedFilters = { ...filters, ordering: e.target.value || undefined };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  const handleDuplicatesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    let isDuplicate: boolean | undefined = undefined;
    
    if (e.target.value === 'true') {
      isDuplicate = true;
    } else if (e.target.value === 'false') {
      isDuplicate = false;
    }
    
    const updatedFilters = { ...filters, is_duplicate: isDuplicate };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const resetFilters = () => {
    setFilters({});
    onFilterChange({});
  };
  
  const toggleFilterPanel = () => {
    setIsFilterPanelOpen(!isFilterPanelOpen);
  };

  // Helper to determine if any filters are active
  const hasActiveFilters = () => {
    return Object.values(filters).some(value => 
      value !== undefined && value !== '' && 
      (typeof value !== 'number' || value > 0)
    );
  };
  
  return (
    <div className="abnormal-card p-4 mb-6">
      <div className="flex flex-col sm:flex-row items-center">
        <div className="relative flex-grow mb-2 sm:mb-0">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder="Search files by name..."
            value={filters.search || ''}
            onChange={handleSearchChange}
          />
        </div>
        
        <div className="flex space-x-2 ml-0 sm:ml-4">
          <div className="flex items-center">
            <ArrowsUpDownIcon className="h-5 w-5 text-gray-500 mr-1" aria-hidden="true" />
            <select
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
              value={filters.ordering || ''}
              onChange={handleSortChange}
            >
              <option value="">Sort by...</option>
              <option value="original_filename">Name (A-Z)</option>
              <option value="-original_filename">Name (Z-A)</option>
              <option value="size">Size (Small-Large)</option>
              <option value="-size">Size (Large-Small)</option>
              <option value="uploaded_at">Date (Oldest)</option>
              <option value="-uploaded_at">Date (Newest)</option>
            </select>
          </div>
          
          <button
            type="button"
            onClick={toggleFilterPanel}
            className={`inline-flex items-center px-3 py-2 border shadow-sm text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${
              hasActiveFilters() 
                ? 'border-primary-300 text-primary-700 bg-primary-50 hover:bg-primary-100' 
                : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
            }`}
          >
            <FunnelIcon className={`h-4 w-4 mr-1 ${hasActiveFilters() ? 'text-primary-500' : 'text-gray-500'}`} /> 
            Filters
            {hasActiveFilters() && (
              <span className="ml-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Active
              </span>
            )}
          </button>
        </div>
      </div>
      
      {isFilterPanelOpen && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="file-type" className="block text-sm font-medium text-gray-700">
                File Type
              </label>
              <select
                id="file-type"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.file_type || ''}
                onChange={handleFileTypeChange}
              >
                <option value="">All file types</option>
                {fileTypes.map(type => (
                  <option key={type} value={type}>
                    {type.split('/')[1].toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="min-size" className="block text-sm font-medium text-gray-700">
                Min Size (KB)
              </label>
              <input
                type="number"
                id="min-size"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                placeholder="Min size"
                value={filters.min_size ? (filters.min_size / 1024).toString() : ''}
                onChange={e => handleSizeChange('min_size', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="max-size" className="block text-sm font-medium text-gray-700">
                Max Size (KB)
              </label>
              <input
                type="number"
                id="max-size"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                placeholder="Max size"
                value={filters.max_size ? (filters.max_size / 1024).toString() : ''}
                onChange={e => handleSizeChange('max_size', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="uploaded-after" className="block text-sm font-medium text-gray-700">
                Uploaded After
              </label>
              <input
                type="date"
                id="uploaded-after"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.uploaded_after || ''}
                onChange={e => handleDateChange('uploaded_after', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="uploaded-before" className="block text-sm font-medium text-gray-700">
                Uploaded Before
              </label>
              <input
                type="date"
                id="uploaded-before"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.uploaded_before || ''}
                onChange={e => handleDateChange('uploaded_before', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="show-duplicates" className="block text-sm font-medium text-gray-700">
                Show Duplicates
              </label>
              <select
                id="show-duplicates"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.is_duplicate === undefined ? '' : filters.is_duplicate.toString()}
                onChange={handleDuplicatesChange}
              >
                <option value="">All files</option>
                <option value="false">Originals only</option>
                <option value="true">Duplicates only</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={resetFilters}
              className="inline-flex items-center px-4 py-2 border border-primary-300 shadow-sm text-sm font-medium rounded-md text-primary-700 bg-white hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <XMarkIcon className="h-4 w-4 mr-1" />
              Reset Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}; 