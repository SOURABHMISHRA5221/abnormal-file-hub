export interface File {
  id: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file: string;
  duplicate_count: number;
  storage_saved: number;
  is_duplicate: boolean;
} 