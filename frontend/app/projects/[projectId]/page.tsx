"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { LogoutButton } from "../../../components/logout-button";
import { useAuthSession } from "../../../hooks/use-auth-session";
import { apiFetch } from "../../../lib/api";
import type { ApiMessage, Project } from "../../../lib/types";

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<Project | null>(null);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [projectError, setProjectError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProject() {
      if (!user || !params.projectId) {
        return;
      }

      setIsProjectLoading(true);
      setProjectError(null);

      try {
        const response = await apiFetch(`/api/projects/${params.projectId}`, {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as ApiMessage | null;
          throw new Error(payload?.message || payload?.detail || "Failed to load project detail.");
        }

        const payload = (await response.json()) as Project;
        setProject(payload);
      } catch (requestError) {
        setProjectError(
          requestError instanceof Error ? requestError.message : "Failed to load project detail.",
        );
      } finally {
        setIsProjectLoading(false);
      }
    }

    void loadProject();
  }, [params.projectId, user]);

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
              Project Detail Placeholder
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Project workspace"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              This route only reserves the project-level entry point for a future
              change. It intentionally excludes document upload, knowledge base,
              RAG, Agent, and Skills workflows.
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
      ) : isProjectLoading ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading project metadata...
        </section>
      ) : project ? (
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
          <dl className="grid gap-6 md:grid-cols-2">
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
      ) : null}
    </div>
  );
}
