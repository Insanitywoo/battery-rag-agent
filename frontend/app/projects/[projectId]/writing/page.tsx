"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { LogoutButton } from "../../../../components/logout-button";
import { useAuthSession } from "../../../../hooks/use-auth-session";
import { apiFetch } from "../../../../lib/api";
import type {
  ApiMessage,
  ProjectDetail,
  SourceReference,
  WritingArtifact,
  WritingArtifactType,
} from "../../../../lib/types";

const TASK_OPTIONS: { label: string; value: WritingArtifactType }[] = [
  { label: "Paper Outline", value: "outline" },
  { label: "Introduction Outline", value: "introduction_outline" },
  { label: "Related Work Draft", value: "related_work" },
  { label: "Method Framework", value: "method_framework" },
  { label: "Conclusion Draft", value: "conclusion" },
  { label: "Citation Check", value: "citation_check" },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatArtifactType(value: string) {
  return value.replaceAll("_", " ");
}

function SourceList({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-slate-500">No supporting project evidence was saved for this result.</p>;
  }

  return (
    <div className="space-y-3">
      {sources.map((source) => (
        <div key={`${source.chunk_id}-${source.chunk_index}`} className="rounded-2xl border border-slate-200 bg-mist p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {source.document_name}
            {source.page_number ? ` | Page ${source.page_number}` : ""}
            {` | Chunk ${source.chunk_index}`}
          </p>
          <p className="mt-2 text-sm leading-7 text-slate-600">{source.excerpt}</p>
        </div>
      ))}
    </div>
  );
}

function ArtifactResult({ artifact }: { artifact: WritingArtifact }) {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Saved artifact</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">{artifact.title}</h2>
          </div>
          <div className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
            {formatArtifactType(artifact.artifact_type)}
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-500">Updated {formatDate(artifact.updated_at)}</p>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Markdown content</p>
        <pre className="mt-4 whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">
          {artifact.content_markdown}
        </pre>
      </div>

      {artifact.warnings.length > 0 ? (
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">Warnings</p>
          <ul className="mt-3 space-y-2 text-sm leading-7 text-amber-900">
            {artifact.warnings.map((warning) => (
              <li key={warning}>- {warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {artifact.unsupported_claims.length > 0 ? (
        <div className="rounded-3xl border border-red-200 bg-red-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-red-800">Unsupported claims</p>
          <ul className="mt-3 space-y-2 text-sm leading-7 text-red-800">
            {artifact.unsupported_claims.map((claim) => (
              <li key={claim}>- {claim}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Sources</p>
        <div className="mt-4">
          <SourceList sources={artifact.sources} />
        </div>
      </div>
    </div>
  );
}

export default function ProjectPaperWritingPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [artifacts, setArtifacts] = useState<WritingArtifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<WritingArtifact | null>(null);
  const [topic, setTopic] = useState("");
  const [researchDirection, setResearchDirection] = useState("");
  const [requirements, setRequirements] = useState("");
  const [selectedTaskType, setSelectedTaskType] = useState<WritingArtifactType>("outline");
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isArtifactsLoading, setIsArtifactsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExportingId, setIsExportingId] = useState<string | null>(null);
  const [deletingArtifactId, setDeletingArtifactId] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [pageNotice, setPageNotice] = useState<string | null>(null);
  const projectId = params.projectId;

  async function loadProject() {
    if (!user || !projectId) {
      return;
    }

    setIsProjectLoading(true);
    setPageError(null);

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
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load project detail.");
    } finally {
      setIsProjectLoading(false);
    }
  }

  async function loadArtifacts() {
    if (!user || !projectId) {
      return;
    }

    setIsArtifactsLoading(true);
    setPageError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/writing/artifacts`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load writing artifacts.");
      }

      const payload = (await response.json()) as WritingArtifact[];
      setArtifacts(payload);
      setSelectedArtifact((current) => {
        if (current) {
          return payload.find((artifact) => artifact.id === current.id) ?? payload[0] ?? null;
        }
        return payload[0] ?? null;
      });
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to load writing artifacts.",
      );
    } finally {
      setIsArtifactsLoading(false);
    }
  }

  async function openArtifact(artifactId: string) {
    if (!projectId) {
      return;
    }

    setPageError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/writing/artifacts/${artifactId}`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load writing artifact detail.");
      }

      const payload = (await response.json()) as WritingArtifact;
      setSelectedArtifact(payload);
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to load writing artifact detail.",
      );
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  useEffect(() => {
    void loadArtifacts();
  }, [projectId, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!projectId || !topic.trim()) {
      setPageError("Enter a paper topic before generating a writing artifact.");
      return;
    }

    setIsSubmitting(true);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/writing/run`, {
        method: "POST",
        body: JSON.stringify({
          task_type: selectedTaskType,
          topic: topic.trim(),
          research_direction: researchDirection.trim() || null,
          requirements: requirements.trim() || null,
        }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to generate writing artifact.");
      }

      const payload = (await response.json()) as WritingArtifact;
      setSelectedArtifact(payload);
      setPageNotice("Writing artifact saved.");
      await loadArtifacts();
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to generate writing artifact.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(artifact: WritingArtifact) {
    if (!projectId) {
      return;
    }

    const confirmed = window.confirm(`Delete "${artifact.title}"?`);
    if (!confirmed) {
      return;
    }

    setDeletingArtifactId(artifact.id);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/writing/artifacts/${artifact.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to delete writing artifact.");
      }

      setArtifacts((current) => current.filter((item) => item.id !== artifact.id));
      setSelectedArtifact((current) => (current?.id === artifact.id ? null : current));
      setPageNotice("Writing artifact deleted.");
      await loadArtifacts();
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to delete writing artifact.",
      );
    } finally {
      setDeletingArtifactId(null);
    }
  }

  async function handleExport(artifact: WritingArtifact) {
    if (!projectId) {
      return;
    }

    setIsExportingId(artifact.id);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/writing/artifacts/${artifact.id}/export/markdown`, {
        method: "GET",
        headers: { Accept: "text/markdown" },
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to export markdown.");
      }

      const markdown = await response.text();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename=\"?([^\"]+)\"?/i);
      const filename = match?.[1] || `${artifact.title}.md`;
      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const objectUrl = window.URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      window.document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(objectUrl);
      setPageNotice("Markdown export generated.");
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to export markdown.");
    } finally {
      setIsExportingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading paper writing workspace...
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-red-200 bg-red-50 p-8 text-red-700 shadow-xl shadow-red-100/50">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-12">
      <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cobalt">
              Project Paper Writing Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Paper writing assistant"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Generate evidence-first writing artifacts from the current project knowledge base.
              The system saves markdown drafts, source references, unsupported claims, and clearly labeled
              external-reference notes for later review.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/projects/${projectId}`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Back to project
            </Link>
            <Link
              href={`/projects/${projectId}/agent`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Open agent
            </Link>
            <Link
              href={`/projects/${projectId}/external-references`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Open external references
            </Link>
            <LogoutButton onLogout={logout} />
          </div>
        </div>
      </section>

      {pageError ? (
        <section className="rounded-[2rem] border border-red-200 bg-red-50 p-5 text-red-700 shadow-xl shadow-red-100/40">
          {pageError}
        </section>
      ) : null}
      {pageNotice ? (
        <section className="rounded-[2rem] border border-emerald-200 bg-emerald-50 p-5 text-emerald-700 shadow-xl shadow-emerald-100/40">
          {pageNotice}
        </section>
      ) : null}

      <div className="grid gap-8 xl:grid-cols-[0.38fr_0.62fr]">
        <aside className="space-y-8">
          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <h2 className="text-xl font-semibold text-ink">Run a writing task</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              Requests stay owner-scoped and project-scoped. The frontend keeps using the existing
              HttpOnly Cookie session through <code>credentials: "include"</code>.
            </p>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="writing-task-type">
                  Writing task type
                </label>
                <select
                  id="writing-task-type"
                  value={selectedTaskType}
                  onChange={(event) => setSelectedTaskType(event.target.value as WritingArtifactType)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                >
                  {TASK_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="writing-topic">
                  Paper topic
                </label>
                <input
                  id="writing-topic"
                  type="text"
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                  placeholder="Battery aging prediction under temperature cycling"
                  disabled={isSubmitting}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="writing-direction">
                  Research direction
                </label>
                <input
                  id="writing-direction"
                  type="text"
                  value={researchDirection}
                  onChange={(event) => setResearchDirection(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                  placeholder="Lithium-ion batteries, thermal management, or system identification"
                  disabled={isSubmitting}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="writing-requirements">
                  Writing requirements
                </label>
                <textarea
                  id="writing-requirements"
                  value={requirements}
                  onChange={(event) => setRequirements(event.target.value)}
                  className="min-h-40 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                  placeholder="Specify the framing, structure, emphasis, or the claims that need evidence support."
                  disabled={isSubmitting}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !topic.trim()}
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isSubmitting ? "Generating..." : "Generate writing artifact"}
              </button>
            </form>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">Artifact history</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Only your own project-scoped artifacts appear here.
                </p>
              </div>
              <div className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                {artifacts.length} saved
              </div>
            </div>

            {isArtifactsLoading ? (
              <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5 text-sm text-slate-600">
                Loading writing history...
              </div>
            ) : artifacts.length === 0 ? (
              <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-5 text-sm text-slate-600">
                No writing artifacts yet. Generate one to populate this workspace.
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {artifacts.map((artifact) => (
                  <article key={artifact.id} className="rounded-3xl border border-slate-200 bg-mist p-5">
                    <button
                      type="button"
                      onClick={() => void openArtifact(artifact.id)}
                      className="w-full text-left"
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                        {formatArtifactType(artifact.artifact_type)}
                      </p>
                      <h3 className="mt-2 text-lg font-semibold text-ink">{artifact.title}</h3>
                      <p className="mt-2 text-xs text-slate-500">Updated {formatDate(artifact.updated_at)}</p>
                    </button>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => void handleExport(artifact)}
                        disabled={isExportingId === artifact.id}
                        className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      >
                        {isExportingId === artifact.id ? "Exporting..." : "Export Markdown"}
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(artifact)}
                        disabled={deletingArtifactId === artifact.id}
                        className="rounded-full border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      >
                        {deletingArtifactId === artifact.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </aside>

        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          {isProjectLoading ? (
            <div className="rounded-3xl border border-slate-200 bg-mist p-10 text-sm text-slate-600">
              Loading project writing status...
            </div>
          ) : selectedArtifact ? (
            <ArtifactResult artifact={selectedArtifact} />
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-mist p-10 text-sm text-slate-600">
              Generate or open a saved writing artifact to review markdown content, sources, warnings, and unsupported claims here.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
