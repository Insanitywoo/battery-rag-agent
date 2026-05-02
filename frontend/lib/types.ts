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

export type ApiMessage = {
  message?: string;
  detail?: string;
};
