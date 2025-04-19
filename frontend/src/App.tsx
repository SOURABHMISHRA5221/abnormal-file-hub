import React, { useState } from 'react';
import { ResetableFileUpload } from './components/ResetableFileUpload';
import { FileList } from './components/FileList';
import { StorageStats } from './components/StorageStats';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-primary-600 shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Abnormal File Hub</h1>
              <p className="mt-1 text-sm text-primary-100">
                Intelligent file management with deduplication
              </p>
            </div>
            <div className="hidden sm:block">
              <a 
                href="https://abnormal.ai" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-white hover:text-primary-100 font-medium"
              >
                Powered by Abnormal AI
              </a>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="space-y-8">
            <StorageStats />
            <div className="abnormal-card">
              <ResetableFileUpload onUploadSuccess={handleUploadSuccess} />
            </div>
            <div className="abnormal-card p-4">
              <FileList key={refreshKey} />
            </div>
          </div>
        </div>
      </main>
      <footer className="bg-white shadow border-t border-gray-100 mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            © 2024 File Hub. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
