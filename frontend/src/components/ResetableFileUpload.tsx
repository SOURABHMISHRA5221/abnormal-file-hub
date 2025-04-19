import React, { useState } from 'react';
import { FileUpload } from './FileUpload';

interface ResetableFileUploadProps {
  onUploadSuccess: () => void;
}

export const ResetableFileUpload: React.FC<ResetableFileUploadProps> = ({ onUploadSuccess }) => {
  const [resetKey, setResetKey] = useState(0);

  const handleUploadSuccess = () => {
    // Call the parent's success handler
    onUploadSuccess();
    
    // Force a remount of the FileUpload component
    setResetKey(prev => prev + 1);
  };

  return <FileUpload key={resetKey} onUploadSuccess={handleUploadSuccess} />;
}; 