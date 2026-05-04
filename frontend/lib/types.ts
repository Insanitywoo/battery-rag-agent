export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type Document = {
  id: string;
  user_id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  status: "uploaded" | "processing" | "processed" | "failed";
  error_message: string | null;
  processed_at: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type ApiMessage = {
  message?: string;
  detail?: string;
};
