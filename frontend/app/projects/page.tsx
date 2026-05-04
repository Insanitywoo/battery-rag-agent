"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { LogoutButton } from "../../components/logout-button";
import { useAuthSession } from "../../hooks/use-auth-session";
import { apiFetch } from "../../lib/api";
import type { ApiMessage, Project } from "../../lib/types";

export default function ProjectsPage() {
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [projects, setProjects] = useState<Project[]>([]);
  const [isProjectsLoading, setIsProjectsLoading] = useState(true);
  const [projectError, setProjectError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  async function loadProjects() {
    setIsProjectsLoading(true);
    setProjectError(null);

    try {
      const response = await apiFetch("/api/projects", {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load projects.");
      }

      const payload = (await response.json()) as Project[];
      setProjects(payload);
    } catch (requestError) {
      setProjectError(requestError instanceof Error ? requestError.message : "Failed to load projects.");
    } finally {
      setIsProjectsLoading(false);
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsCreating(true);
    setProjectError(null);

    try {
      const response = await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify({
          name,
          description: description || null,
        }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to create project.");
      }

      const project = (await response.json()) as Project;
      setProjects((current) => [project, ...current]);
      setName("");
      setDescription("");
    } catch (requestError) {
      setProjectError(requestError instanceof Error ? requestError.message : "Failed to create project.");
    } finally {
      setIsCreating(false);
    }
  }

  useEffect(() => {
    if (user) {
      void loadProjects();
    }
  }, [user]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading your projects...
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
              Project Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">Your research projects</h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Projects are owner-scoped. Each workspace now expands into document upload,
              ingestion, vector knowledge-base build, and project-scoped RAG chat.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Back to dashboard
            </Link>
            <LogoutButton onLogout={logout} />
          </div>
        </div>
      </section>

      <section className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/30">
          <h2 className="text-xl font-semibold text-ink">Create project</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Add a personal research workspace that later changes can expand with
            documents, knowledge bases, and workflows.
          </p>
          <form className="mt-6 space-y-5" onSubmit={handleCreateProject}>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="project-name">
                Project name
              </label>
              <input
                id="project-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                placeholder="Battery fast charging optimization"
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="project-description">
                Description
              </label>
              <textarea
                id="project-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                className="min-h-32 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                placeholder="Short note about the topic, method, or deliverable."
              />
            </div>
            <button
              type="submit"
              disabled={isCreating}
              className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isCreating ? "Creating..." : "Create project"}
            </button>
          </form>
        </article>

        <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/30">
          <h2 className="text-xl font-semibold text-ink">Project list</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Only projects owned by the authenticated user are visible here.
          </p>
          {projectError ? (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {projectError}
            </div>
          ) : null}
          {isProjectsLoading ? (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-mist px-4 py-5 text-sm text-slate-600">
              Loading projects...
            </div>
          ) : projects.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-mist px-4 py-5 text-sm text-slate-600">
              No projects yet. Create your first workspace to continue.
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  className="rounded-3xl border border-slate-200 bg-mist p-5"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-ink">{project.name}</h3>
                      <p className="mt-2 text-sm leading-7 text-slate-600">
                        {project.description || "No description provided yet."}
                      </p>
                    </div>
                    <Link
                      href={`/projects/${project.id}`}
                      className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
                    >
                      Open workspace
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
