"use client";

import Link from "next/link";

import { LogoutButton } from "../../components/logout-button";
import { useAuthSession } from "../../hooks/use-auth-session";

const cards = [
  {
    title: "Projects",
    body: "Create and organize owner-scoped research projects before later document and RAG changes land.",
  },
  {
    title: "Workspace boundary",
    body: "This dashboard is authenticated and relies on the backend HttpOnly auth Cookie.",
  },
  {
    title: "Scope guardrail",
    body: "Document upload, knowledge base, RAG, Agent, and Skills remain intentionally out of scope here.",
  },
];

export default function DashboardPage() {
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading your workspace...
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
              Personal Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              Welcome back{user ? `, ${user.name}` : ""}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              You are now inside the authenticated shell for your personal research
              workspace. This stage establishes account access and project ownership
              boundaries for future changes.
            </p>
            {user ? (
              <p className="mt-4 text-sm text-slate-500">
                Signed in as <span className="font-medium text-slate-700">{user.email}</span>
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/projects"
              className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Open project workspace
            </Link>
            <LogoutButton onLogout={logout} />
          </div>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {cards.map((card) => (
          <article
            key={card.title}
            className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg shadow-slate-200/30"
          >
            <h2 className="text-lg font-semibold text-ink">{card.title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">{card.body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
