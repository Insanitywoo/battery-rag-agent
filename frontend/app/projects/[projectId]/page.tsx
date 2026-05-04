"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import { LogoutButton } from "../../../components/logout-button";
import { useAuthSession } from "../../../hooks/use-auth-session";
import { apiFetch } from "../../../lib/api";
import type {
  ApiMessage,
  Document,
  KnowledgeBaseBuildResult,
  ProjectDetail,
} from "../../../lib/types";

const ACCEPTED_FILE_TYPES = ".pdf,.txt,.md,.csv";

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatEmbeddingStatus(status: Document["embedding_status"]) {
  return status.replaceAll("_", " ");
}

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [projectError, setProjectError] = useState<string | null>(null);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [documentNotice, setDocumentNotice] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [processingDocumentId, setProcessingDocumentId] = useState<string | null>(null);
  const [isBuildingKnowledgeBase, setIsBuildingKnowledgeBase] = useState(false);
  const projectId = params.projectId;

  const documentSummary = useMemo(() => {
    if (documents.length === 0) {
      return "No files uploaded yet.";
    }
    const chunkTotal = documents.reduce((total, document) => total + document.chunk_count, 0);
    return `${documents.length} file${documents.length === 1 ? "" : "s"} / ${chunkTotal} chunk${chunkTotal === 1 ? "" : "s"}`;
  }, [documents]);

  async function loadProject() {
    if (!user || !projectId) {
      return;
    }

    setIsProjectLoading(true);
    setProjectError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load project detail.");
      }

      const payload = (await response.json()) as ProjectDetail;
      setProject(payload);
    } catch (requestError) {
      setProjectError(requestError instanceof Error ? requestError.message : "Failed to load project detail.");
    } finally {
      setIsProjectLoading(false);
    }
  }

  async function loadDocuments() {
    if (!user || !projectId) {
      return;
    }

    setIsDocumentsLoading(true);
    setDocumentError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/documents`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load project documents.");
      }

      const payload = (await response.json()) as Document[];
      setDocuments(payload);
    } catch (requestError) {
      setDocumentError(
        requestError instanceof Error ? requestError.message : "Failed to load project documents.",
      );
    } finally {
      setIsDocumentsLoading(false);
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  useEffect(() => {
    void loadDocuments();
  }, [projectId, user]);

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    setUploadMessage(null);
    setDocumentNotice(null);
    setDocumentError(null);
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!projectId || !selectedFile) {
      setUploadMessage("Choose a PDF, TXT, MD, or CSV file before uploading.");
      return;
    }

    setIsUploading(true);
    setUploadMessage(null);
    setDocumentNotice(null);
    setDocumentError(null);

    try {
      const formData = new FormData();
      formData.append("upload", selectedFile);

      const response = await apiFetch(`/api/projects/${projectId}/documents`, {
        method: "POST",
        body: formData,
        skipJsonContentType: true,
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to upload file.");
      }

      const payload = (await response.json()) as Document;
      setDocuments((current) => [payload, ...current]);
      setSelectedFile(null);
      setUploadMessage(`Uploaded ${payload.original_filename}.`);
      event.currentTarget.reset();
      await loadProject();
    } catch (requestError) {
      setUploadMessage(requestError instanceof Error ? requestError.message : "Failed to upload file.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(document: Document) {
    if (!projectId) {
      return;
    }

    const confirmed = window.confirm(`Delete ${document.original_filename}? This removes the stored file permanently.`);
    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(document.id);
    setDocumentError(null);
    setDocumentNotice(null);
    setUploadMessage(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/documents/${document.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to delete file.");
      }

      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setDocumentNotice(`${document.original_filename} was deleted.`);
      await loadProject();
    } catch (requestError) {
      setDocumentError(requestError instanceof Error ? requestError.message : "Failed to delete file.");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function handleProcess(document: Document) {
    if (!projectId) {
      return;
    }

    setProcessingDocumentId(document.id);
    setDocumentError(null);
    setDocumentNotice(null);
    setUploadMessage(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/documents/${document.id}/process`, {
        method: "POST",
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to process document.");
      }

      const payload = (await response.json()) as Document;
      await Promise.all([loadDocuments(), loadProject()]);

      if (payload.status === "failed") {
        setDocumentError(payload.error_message || "Document processing failed.");
      } else {
        const actionLabel = document.chunk_count > 0 ? "Reprocessed" : "Processed";
        setDocumentNotice(`${actionLabel} ${payload.original_filename}.`);
      }
    } catch (requestError) {
      setDocumentError(
        requestError instanceof Error ? requestError.message : "Failed to process document.",
      );
    } finally {
      setProcessingDocumentId(null);
    }
  }

  async function handleBuildKnowledgeBase() {
    if (!projectId) {
      return;
    }

    setIsBuildingKnowledgeBase(true);
    setProjectError(null);
    setDocumentNotice(null);
    setDocumentError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/knowledge-base/build`, {
        method: "POST",
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to build the project knowledge base.");
      }

      const payload = (await response.json()) as KnowledgeBaseBuildResult;
      setDocumentNotice(payload.message);
      await Promise.all([loadProject(), loadDocuments()]);
    } catch (requestError) {
      setProjectError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to build the project knowledge base.",
      );
    } finally {
      setIsBuildingKnowledgeBase(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading project detail...
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-[2rem] border border-red-200 bg-red-50 p-8 text-red-700 shadow-xl shadow-red-100/50">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16">
      <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cobalt">
              Project Knowledge Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Project workspace"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Upload project documents, process them into chunks, build the project
              vector knowledge base, and continue into owner-scoped RAG chat from here.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/projects"
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Back to projects
            </Link>
            <LogoutButton onLogout={logout} />
          </div>
        </div>
      </section>

      {projectError ? (
        <section className="rounded-[2rem] border border-red-200 bg-red-50 p-8 text-red-700 shadow-xl shadow-red-100/40">
          {projectError}
        </section>
      ) : null}

      {isProjectLoading ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading project metadata...
        </section>
      ) : project ? (
        <div className="grid gap-8 xl:grid-cols-[0.92fr_1.08fr]">
          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
            <h2 className="text-xl font-semibold text-ink">Project metadata</h2>
            <dl className="mt-6 grid gap-6 md:grid-cols-2">
              <div>
                <dt className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Project ID
                </dt>
                <dd className="mt-2 text-sm text-slate-700">{project.id}</dd>
              </div>
              <div>
                <dt className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Owner ID
                </dt>
                <dd className="mt-2 text-sm text-slate-700">{project.owner_id}</dd>
              </div>
              <div className="md:col-span-2">
                <dt className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Description
                </dt>
                <dd className="mt-2 text-sm leading-7 text-slate-700">
                  {project.description || "No description provided yet."}
                </dd>
              </div>
            </dl>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-ink">Knowledge base status</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  Vectors are built from processed chunks only. Retrieval and chat remain
                  scoped to the current authenticated owner and this project.
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-mist px-4 py-3 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                {project.knowledge_base.can_chat ? "Chat ready" : "Needs build"}
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Processed documents
                </p>
                <p className="mt-3 text-3xl font-semibold text-ink">
                  {project.knowledge_base.processed_documents}
                </p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Embedded documents
                </p>
                <p className="mt-3 text-3xl font-semibold text-ink">
                  {project.knowledge_base.embedded_documents}
                </p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Total chunks
                </p>
                <p className="mt-3 text-3xl font-semibold text-ink">
                  {project.knowledge_base.total_chunks}
                </p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Indexed chunks
                </p>
                <p className="mt-3 text-3xl font-semibold text-ink">
                  {project.knowledge_base.indexed_chunks}
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void handleBuildKnowledgeBase()}
                disabled={isBuildingKnowledgeBase}
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isBuildingKnowledgeBase
                  ? "Building..."
                  : project.knowledge_base.needs_rebuild || !project.knowledge_base.can_chat
                    ? "Build / rebuild vector DB"
                    : "Rebuild vector DB"}
              </button>
              <Link
                href={`/projects/${project.id}/chat`}
                className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
              >
                Open project chat
              </Link>
              <Link
                href={`/projects/${project.id}/agent`}
                className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
              >
                Open project agent
              </Link>
            </div>

            <p className="mt-4 text-xs leading-6 text-slate-500">
              Last embedded: {formatDate(project.knowledge_base.last_embedded_at)}
            </p>
          </section>
        </div>
      ) : null}

      {project ? (
        <section className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
          <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/30">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-ink">Upload files</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  Allowed types: PDF, TXT, MD, and CSV. The backend validates both
                  extension and MIME type before saving into local storage.
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-mist px-4 py-3 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                {documentSummary}
              </div>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleUpload}>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="document-upload">
                  Choose file
                </label>
                <input
                  id="document-upload"
                  type="file"
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={handleFileSelection}
                  className="block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-full file:border-0 file:bg-ink file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
                />
                <p className="mt-3 text-xs leading-6 text-slate-500">
                  Upload keeps the raw file, processing creates chunks, and vector build
                  happens only when you explicitly trigger the knowledge-base step.
                </p>
              </div>
              {uploadMessage ? (
                <div className="rounded-2xl border border-slate-200 bg-mist px-4 py-3 text-sm text-slate-700">
                  {uploadMessage}
                </div>
              ) : null}
              <button
                type="submit"
                disabled={isUploading}
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isUploading ? "Uploading..." : "Upload file"}
              </button>
            </form>
          </article>

          <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/30">
            <h2 className="text-xl font-semibold text-ink">Current workspace scope</h2>
            <div className="mt-6 space-y-4 text-sm leading-7 text-slate-600">
              <p>
                Files, chunks, vectors, and chat history are all owner-scoped and project-scoped.
              </p>
              <p>
                Protected requests continue to use the existing HttpOnly cookie session through
                `credentials: "include"`.
              </p>
              <p>
                The frontend never stores the model key or token in browser storage.
              </p>
              <p>
                The Agent workspace runs one bounded research task at a time and reuses the same
                owner-scoped retrieval and evidence rules as project chat.
              </p>
            </div>
          </article>
        </section>
      ) : null}

      {project ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-ink">Stored files</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                This list is scoped to the authenticated owner and the current project only.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-mist px-4 py-3 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
              {documentSummary}
            </div>
          </div>

          {documentError ? (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {documentError}
            </div>
          ) : null}
          {documentNotice ? (
            <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {documentNotice}
            </div>
          ) : null}

          {isDocumentsLoading ? (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-mist px-4 py-5 text-sm text-slate-600">
              Loading files...
            </div>
          ) : documents.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-mist px-4 py-5 text-sm text-slate-600">
              No files yet. Upload a project file to create the local storage record.
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {documents.map((document) => (
                <article key={document.id} className="rounded-3xl border border-slate-200 bg-mist p-5">
                  <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-lg font-semibold text-ink">
                        {document.original_filename}
                      </h3>
                      <div className="mt-4 grid gap-4 text-sm text-slate-600 md:grid-cols-2 xl:grid-cols-4">
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Type</p>
                          <p className="mt-1">{document.file_type.toUpperCase()}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Size</p>
                          <p className="mt-1">{formatBytes(document.file_size)}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Status</p>
                          <p className="mt-1 capitalize">{document.status}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Chunks</p>
                          <p className="mt-1">{document.chunk_count}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Embedding</p>
                          <p className="mt-1 capitalize">{formatEmbeddingStatus(document.embedding_status)}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Uploaded</p>
                          <p className="mt-1">{formatDate(document.created_at)}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">Embedded</p>
                          <p className="mt-1">{formatDate(document.embedded_at)}</p>
                        </div>
                        <div>
                          <p className="font-semibold uppercase tracking-[0.16em] text-slate-500">MIME</p>
                          <p className="mt-1 break-all">{document.mime_type}</p>
                        </div>
                      </div>
                      {document.error_message ? (
                        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                          {document.error_message}
                        </div>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => void handleProcess(document)}
                        disabled={processingDocumentId === document.id}
                        className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                      >
                        {processingDocumentId === document.id
                          ? "Processing..."
                          : document.chunk_count > 0
                            ? "Reprocess document"
                            : "Process document"}
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(document)}
                        disabled={deletingDocumentId === document.id}
                        className="rounded-full border border-red-200 bg-white px-5 py-2.5 text-sm font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      >
                        {deletingDocumentId === document.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
