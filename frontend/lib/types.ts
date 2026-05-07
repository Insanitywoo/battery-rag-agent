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

export type KnowledgeBaseStatus = {
  total_documents: number;
  processed_documents: number;
  embedded_documents: number;
  total_chunks: number;
  indexed_chunks: number;
  can_chat: boolean;
  needs_rebuild: boolean;
  last_embedded_at: string | null;
};

export type ProjectDetail = Project & {
  knowledge_base: KnowledgeBaseStatus;
};

export type KnowledgeBaseBuildResult = {
  message: string;
  knowledge_base: KnowledgeBaseStatus;
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
  embedding_status: "not_indexed" | "indexing" | "indexed" | "failed";
  error_message: string | null;
  processed_at: string | null;
  embedded_at: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type SourceReference = {
  document_id: string;
  document_name: string;
  page_number: number | null;
  chunk_id: string;
  chunk_index: number;
  excerpt: string;
};

export type ExternalReference = {
  id: string;
  user_id: string;
  project_id: string;
  source: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstract: string | null;
  bibtex: string;
  warnings: string[];
  created_at: string;
  updated_at: string;
};

export type ExternalReferenceSearchCandidate = {
  dedupe_key: string;
  source: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstract: string | null;
  warnings: string[];
};

export type ExternalReferenceSearchResponse = {
  results: ExternalReferenceSearchCandidate[];
  warnings: string[];
};

export type ExternalReferenceContext = {
  id: string;
  label: "external reference";
  source: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstract: string | null;
  warnings: string[];
};

export type ChatMessage = {
  id: string;
  user_id: string;
  project_id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources_json: SourceReference[] | null;
  created_at: string;
};

export type ChatSessionSummary = {
  id: string;
  user_id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatSessionDetail = ChatSessionSummary & {
  messages: ChatMessage[];
};

export type ApiMessage = {
  message?: string;
  detail?: string;
};

export type AgentTaskType =
  | "research_qa"
  | "paper_summary"
  | "multi_paper_compare"
  | "literature_review"
  | "writing_outline"
  | "evidence_check";

export type AgentResultSection = {
  title: string;
  content: string;
};

export type AgentResultPayload = {
  routed_task_type: AgentTaskType;
  route_confidence: number;
  route_reason: string;
  answer: string | null;
  result: string | null;
  sections: AgentResultSection[];
  document_scope: string[];
  sources: SourceReference[];
  external_references: ExternalReferenceContext[];
  warnings: string[];
  clarification: string | null;
  supported_claims: string[];
  unsupported_claims: string[];
};

export type AgentTask = {
  id: string;
  user_id: string;
  project_id: string;
  task_type: AgentTaskType;
  status: "queued" | "running" | "completed" | "failed" | "needs_clarification";
  user_input: string;
  result_json: AgentResultPayload | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type WritingArtifactType =
  | "outline"
  | "introduction_outline"
  | "related_work"
  | "method_framework"
  | "conclusion"
  | "citation_check";

export type WritingArtifact = {
  id: string;
  user_id: string;
  project_id: string;
  artifact_type: WritingArtifactType;
  title: string;
  content_markdown: string;
  sources: SourceReference[];
  warnings: string[];
  unsupported_claims: string[];
  created_at: string;
  updated_at: string;
};

export type ExperimentColumnType = "numeric" | "categorical" | "text" | "empty";

export type ExperimentDatasetColumn = {
  name: string;
  inferred_type: ExperimentColumnType;
};

export type ExperimentDataset = {
  id: string;
  user_id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  storage_path: string;
  columns: ExperimentDatasetColumn[];
  row_count: number;
  created_at: string;
  updated_at: string;
};

export type ExperimentDatasetDetail = ExperimentDataset & {
  preview_rows: Array<Record<string, string | null>>;
};

export type ExperimentStatsMetric = {
  count: number;
  mean: number;
  min: number;
  max: number;
  std: number;
};

export type ExperimentOutputType = "stats_summary" | "line_chart" | "bar_chart" | "result_analysis";

export type ExperimentOutput = {
  id: string;
  user_id: string;
  project_id: string;
  dataset_id: string;
  output_type: ExperimentOutputType;
  title: string;
  content_markdown: string | null;
  chart_path: string | null;
  stats_json: Record<string, ExperimentStatsMetric> | null;
  created_at: string;
  updated_at: string;
};
