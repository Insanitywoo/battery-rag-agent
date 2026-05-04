"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { LogoutButton } from "../../../../components/logout-button";
import { useAuthSession } from "../../../../hooks/use-auth-session";
import { apiFetch } from "../../../../lib/api";
import type {
  AgentResultPayload,
  AgentTask,
  AgentTaskType,
  ApiMessage,
  ProjectDetail,
  SourceReference,
} from "../../../../lib/types";

const TASK_OPTIONS: { label: string; value: AgentTaskType }[] = [
  { label: "Research QA", value: "research_qa" },
  { label: "Paper Summary", value: "paper_summary" },
  { label: "Multi-paper Compare", value: "multi_paper_compare" },
  { label: "Literature Review", value: "literature_review" },
  { label: "Writing Outline", value: "writing_outline" },
  { label: "Evidence Check", value: "evidence_check" },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatTaskType(taskType: string) {
  return taskType.replaceAll("_", " ");
}

function SourceList({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-slate-500">No supporting sources were returned for this result.</p>;
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

function ResultPanel({ result }: { result: AgentResultPayload }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-mist p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Routed task</p>
          <p className="mt-3 text-lg font-semibold text-ink capitalize">{formatTaskType(result.routed_task_type)}</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-mist p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Route confidence</p>
          <p className="mt-3 text-lg font-semibold text-ink">{Math.round(result.route_confidence * 100)}%</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-mist p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Document scope</p>
          <p className="mt-3 text-sm font-medium leading-6 text-slate-700">
            {result.document_scope.length > 0 ? result.document_scope.join(", ") : "Current project evidence"}
          </p>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Route reason</p>
        <p className="mt-3 text-sm leading-7 text-slate-700">{result.route_reason}</p>
      </div>

      {result.answer ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Answer</p>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{result.answer}</p>
        </div>
      ) : null}

      {result.result && result.result !== result.answer ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Result</p>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{result.result}</p>
        </div>
      ) : null}

      {result.clarification ? (
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
          <p className="text-xs font-semibold uppercase tracking-[0.18em]">Clarification needed</p>
          <p className="mt-3 text-sm leading-7">{result.clarification}</p>
        </div>
      ) : null}

      {result.sections.length > 0 ? (
        <div className="space-y-4">
          {result.sections.map((section) => (
            <div key={section.title} className="rounded-3xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{section.title}</p>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{section.content}</p>
            </div>
          ))}
        </div>
      ) : null}

      {result.warnings.length > 0 ? (
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">Warnings</p>
          <ul className="mt-3 space-y-2 text-sm leading-7 text-amber-900">
            {result.warnings.map((warning) => (
              <li key={warning}>- {warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.unsupported_claims.length > 0 ? (
        <div className="rounded-3xl border border-red-200 bg-red-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-red-800">Unsupported claims</p>
          <ul className="mt-3 space-y-2 text-sm leading-7 text-red-800">
            {result.unsupported_claims.map((claim) => (
              <li key={claim}>- {claim}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Sources</p>
        <div className="mt-4">
          <SourceList sources={result.sources} />
        </div>
      </div>
    </div>
  );
}

export default function ProjectAgentPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [taskInput, setTaskInput] = useState("");
  const [selectedTaskType, setSelectedTaskType] = useState<AgentTaskType | "auto">("auto");
  const [latestTask, setLatestTask] = useState<AgentTask | null>(null);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!projectId || !taskInput.trim()) {
      setPageError("Enter a research task before running the Agent.");
      return;
    }

    setIsSubmitting(true);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/agent/run`, {
        method: "POST",
        body: JSON.stringify({
          user_input: taskInput.trim(),
          task_type: selectedTaskType === "auto" ? null : selectedTaskType,
        }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to run project Agent task.");
      }

      const payload = (await response.json()) as AgentTask;
      setLatestTask(payload);
      setPageNotice(
        payload.status === "needs_clarification"
          ? "The Agent needs more detail before it can run safely."
          : "Agent task completed.",
      );
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to run project Agent task.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading project agent workspace...
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
              Project Agent Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Project agent"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Run one bounded research task at a time against the current project knowledge base.
              The backend routes the request, executes one Skill, and returns structured results with evidence.
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
              href={`/projects/${projectId}/chat`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Open chat
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

      <div className="grid gap-8 xl:grid-cols-[0.4fr_0.6fr]">
        <aside className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          <h2 className="text-xl font-semibold text-ink">Run a research task</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Requests stay owner-scoped and project-scoped. The frontend uses `credentials: "include"`
            and never exposes model provider secrets.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="agent-task-type">
                Task type
              </label>
              <select
                id="agent-task-type"
                value={selectedTaskType}
                onChange={(event) => setSelectedTaskType(event.target.value as AgentTaskType | "auto")}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
              >
                <option value="auto">Auto route</option>
                {TASK_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="agent-task-input">
                Task prompt
              </label>
              <textarea
                id="agent-task-input"
                value={taskInput}
                onChange={(event) => setTaskInput(event.target.value)}
                className="min-h-48 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                placeholder="Ask a research question, request a summary, compare methods, draft an outline, or check evidence against this project."
                disabled={isSubmitting}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !taskInput.trim()}
              className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Running agent..." : "Run agent task"}
            </button>
          </form>

          <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5">
            {isProjectLoading ? (
              <p className="text-sm text-slate-600">Loading project status...</p>
            ) : project ? (
              <div className="space-y-3 text-sm text-slate-600">
                <p>
                  Indexed chunks: <span className="font-semibold text-ink">{project.knowledge_base.indexed_chunks}</span>
                </p>
                <p>
                  Chat ready: <span className="font-semibold text-ink">{project.knowledge_base.can_chat ? "Yes" : "No"}</span>
                </p>
                <p>
                  Needs rebuild: <span className="font-semibold text-ink">{project.knowledge_base.needs_rebuild ? "Yes" : "No"}</span>
                </p>
              </div>
            ) : null}
          </div>
        </aside>

        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          {!latestTask ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-mist p-10 text-sm text-slate-600">
              Run an Agent task to see structured results, evidence sources, warnings, and clarification guidance here.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-5">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Latest agent task</p>
                    <h2 className="mt-2 text-2xl font-semibold text-ink capitalize">
                      {formatTaskType(latestTask.task_type)}
                    </h2>
                  </div>
                  <div className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                    {formatTaskType(latestTask.status)}
                  </div>
                </div>
                <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{latestTask.user_input}</p>
                <p className="mt-4 text-xs text-slate-500">Updated {formatDate(latestTask.updated_at)}</p>
                {latestTask.error_message ? (
                  <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    {latestTask.error_message}
                  </div>
                ) : null}
              </div>

              {latestTask.result_json ? <ResultPanel result={latestTask.result_json} /> : null}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
