"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { LogoutButton } from "../../../../components/logout-button";
import { useAuthSession } from "../../../../hooks/use-auth-session";
import { API_BASE_URL, apiFetch } from "../../../../lib/api";
import type {
  ApiMessage,
  ChatMessage,
  ChatSessionDetail,
  ChatSessionSummary,
  ProjectDetail,
  SourceReference,
} from "../../../../lib/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function SourceList({ sources }: { sources: SourceReference[] | null }) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3">
      {sources.map((source) => (
        <div key={`${source.chunk_id}-${source.chunk_index}`} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {source.document_name}
            {source.page_number ? ` · Page ${source.page_number}` : ""}
            {` · Chunk ${source.chunk_index}`}
          </p>
          <p className="mt-2 text-sm leading-7 text-slate-600">{source.excerpt}</p>
        </div>
      ))}
    </div>
  );
}

export default function ProjectChatPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSessionDetail | null>(null);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isSessionsLoading, setIsSessionsLoading] = useState(true);
  const [isSessionLoading, setIsSessionLoading] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [pageError, setPageError] = useState<string | null>(null);
  const [pageNotice, setPageNotice] = useState<string | null>(null);
  const projectId = params.projectId;

  const messages = useMemo(() => activeSession?.messages ?? [], [activeSession]);

  async function loadProject() {
    if (!user || !projectId) {
      return;
    }

    setIsProjectLoading(true);
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

  async function loadSessions(preferredSessionId?: string) {
    if (!user || !projectId) {
      return;
    }

    setIsSessionsLoading(true);
    setPageError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/chat/sessions`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load chat sessions.");
      }

      const payload = (await response.json()) as ChatSessionSummary[];
      setSessions(payload);

      const nextSessionId = preferredSessionId || activeSession?.id || payload[0]?.id;
      if (nextSessionId) {
        await loadSession(nextSessionId);
      } else {
        setActiveSession(null);
      }
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load chat sessions.");
    } finally {
      setIsSessionsLoading(false);
    }
  }

  async function loadSession(sessionId: string) {
    if (!projectId) {
      return;
    }

    setIsSessionLoading(true);
    setPageError(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/chat/sessions/${sessionId}`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load chat session.");
      }

      const payload = (await response.json()) as ChatSessionDetail;
      setActiveSession(payload);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load chat session.");
    } finally {
      setIsSessionLoading(false);
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  useEffect(() => {
    void loadSessions();
  }, [projectId, user]);

  async function handleCreateSession() {
    if (!projectId) {
      return;
    }

    setIsCreatingSession(true);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/chat/sessions`, {
        method: "POST",
        body: JSON.stringify({ title: "New chat" }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to create chat session.");
      }

      const payload = (await response.json()) as ChatSessionSummary;
      setPageNotice("Created a new project chat session.");
      await loadSessions(payload.id);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to create chat session.");
    } finally {
      setIsCreatingSession(false);
    }
  }

  async function handleDeleteSession(session: ChatSessionSummary) {
    if (!projectId) {
      return;
    }

    const confirmed = window.confirm(`Delete "${session.title}"? This removes the chat history for this session.`);
    if (!confirmed) {
      return;
    }

    setDeletingSessionId(session.id);
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/chat/sessions/${session.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to delete chat session.");
      }

      const nextSessions = sessions.filter((item) => item.id !== session.id);
      setSessions(nextSessions);
      setPageNotice("Chat session deleted.");

      if (activeSession?.id === session.id) {
        if (nextSessions[0]) {
          await loadSession(nextSessions[0].id);
        } else {
          setActiveSession(null);
        }
      }
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to delete chat session.");
    } finally {
      setDeletingSessionId(null);
    }
  }

  async function handleSubmitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!projectId || !activeSession || !question.trim()) {
      return;
    }

    setIsStreaming(true);
    setStreamingAnswer("");
    setPageError(null);
    setPageNotice(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/chat/sessions/${activeSession.id}/messages/stream`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question.trim() }),
        },
      );

      if (!response.ok) {
        const text = await response.text();
        try {
          const payload = JSON.parse(text) as ApiMessage;
          throw new Error(payload.message || payload.detail || "Failed to stream project chat.");
        } catch {
          throw new Error(text || "Failed to stream project chat.");
        }
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Streaming response body is unavailable.");
      }

      const decoder = new TextDecoder();
      let nextAnswer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        nextAnswer += decoder.decode(value, { stream: true });
        setStreamingAnswer(nextAnswer);
      }
      nextAnswer += decoder.decode();
      setStreamingAnswer(nextAnswer);
      setQuestion("");
      await loadSessions(activeSession.id);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to stream project chat.");
    } finally {
      setIsStreaming(false);
      setStreamingAnswer("");
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading project chat...
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
              Project RAG Chat
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Project chat"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Ask questions only against this project&apos;s owner-scoped knowledge base.
              Answers stream from the backend and keep source citations on the saved assistant message.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/projects/${projectId}`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Back to project
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

      <div className="grid gap-8 xl:grid-cols-[0.35fr_0.65fr]">
        <aside className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-ink">Sessions</h2>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                Only your own sessions in this project appear here.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleCreateSession()}
              disabled={isCreatingSession}
              className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isCreatingSession ? "Creating..." : "New chat"}
            </button>
          </div>

          <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5">
            {isProjectLoading ? (
              <p className="text-sm text-slate-600">Loading knowledge-base status...</p>
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

          <div className="mt-6 space-y-3">
            {isSessionsLoading ? (
              <div className="rounded-3xl border border-slate-200 bg-mist p-4 text-sm text-slate-600">
                Loading sessions...
              </div>
            ) : sessions.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-mist p-4 text-sm text-slate-600">
                No sessions yet. Start a new project chat to ask your first question.
              </div>
            ) : (
              sessions.map((session) => {
                const isActive = activeSession?.id === session.id;
                return (
                  <div
                    key={session.id}
                    className={`rounded-3xl border p-4 transition ${
                      isActive
                        ? "border-cobalt bg-cobalt/5 shadow-sm"
                        : "border-slate-200 bg-mist"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => void loadSession(session.id)}
                      className="w-full text-left"
                    >
                      <p className="text-sm font-semibold text-ink">{session.title}</p>
                      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                        Updated {formatDate(session.updated_at)}
                      </p>
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDeleteSession(session)}
                      disabled={deletingSessionId === session.id}
                      className="mt-4 rounded-full border border-red-200 bg-white px-4 py-2 text-xs font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                    >
                      {deletingSessionId === session.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          {!activeSession ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-mist p-10 text-sm text-slate-600">
              Create or open a project chat session to start asking questions.
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-2 border-b border-slate-200 pb-5">
                <h2 className="text-2xl font-semibold text-ink">{activeSession.title}</h2>
                <p className="text-sm text-slate-600">
                  Session updated {formatDate(activeSession.updated_at)}
                </p>
              </div>

              <div className="mt-6 space-y-4">
                {isSessionLoading ? (
                  <div className="rounded-3xl border border-slate-200 bg-mist p-4 text-sm text-slate-600">
                    Loading session...
                  </div>
                ) : messages.length === 0 ? (
                  <div className="rounded-3xl border border-dashed border-slate-300 bg-mist p-4 text-sm text-slate-600">
                    This session is empty. Ask a question to start the conversation.
                  </div>
                ) : (
                  messages.map((message: ChatMessage) => (
                    <article
                      key={message.id}
                      className={`rounded-3xl border p-5 ${
                        message.role === "assistant"
                          ? "border-slate-200 bg-mist"
                          : "border-cobalt/30 bg-cobalt/5"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                          {message.role === "assistant" ? "Assistant" : "You"}
                        </p>
                        <p className="text-xs text-slate-500">{formatDate(message.created_at)}</p>
                      </div>
                      <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                        {message.content}
                      </p>
                      {message.role === "assistant" ? <SourceList sources={message.sources_json} /> : null}
                    </article>
                  ))
                )}

                {isStreaming ? (
                  <article className="rounded-3xl border border-slate-200 bg-mist p-5">
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Assistant
                      </p>
                      <p className="text-xs text-slate-500">Streaming...</p>
                    </div>
                    <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                      {streamingAnswer || "Thinking..."}
                    </p>
                  </article>
                ) : null}
              </div>

              <form className="mt-6 space-y-4 border-t border-slate-200 pt-6" onSubmit={handleSubmitQuestion}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="chat-question">
                    Ask a project question
                  </label>
                  <textarea
                    id="chat-question"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    className="min-h-32 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                    placeholder="Ask about battery aging, storage control, or any document evidence in this project."
                    disabled={isStreaming}
                  />
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={isStreaming || !question.trim()}
                    className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isStreaming ? "Streaming answer..." : "Ask with RAG"}
                  </button>
                  <p className="text-xs leading-6 text-slate-500">
                    The frontend streams from the backend with `credentials: "include"` and never holds the model key.
                  </p>
                </div>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
