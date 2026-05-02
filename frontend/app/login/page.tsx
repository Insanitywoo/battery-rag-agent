"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useMemo, useState } from "react";

import { apiFetch } from "../../lib/api";
import type { ApiMessage } from "../../lib/types";

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/dashboard";
  const registered = searchParams.get("registered") === "1";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const helperText = useMemo(() => {
    if (registered) {
      return "Registration successful. Sign in to access your workspace.";
    }
    return "Sign in with the account you created for your personal research workspace.";
  }, [registered]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Login failed.");
      }

      router.replace(nextPath);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-73px)] max-w-6xl items-center px-6 py-16">
      <div className="grid w-full gap-10 lg:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cobalt">
            Auth
          </p>
          <h1 className="mt-4 text-4xl font-semibold text-ink">Sign in to your workspace</h1>
          <p className="mt-4 text-base leading-8 text-slate-600">{helperText}</p>
          <div className="mt-8 rounded-2xl border border-slate-200 bg-mist p-5 text-sm leading-7 text-slate-600">
            This change only introduces account access and personal project workspace
            foundations. Document upload, RAG, Agent, and Skills remain out of scope.
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                placeholder="At least 8 characters"
                required
              />
            </div>
            {error ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            ) : null}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-sm text-slate-600">
            Need an account?{" "}
            <Link href="/register" className="font-medium text-cobalt hover:text-blue-700">
              Create one
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto flex min-h-[calc(100vh-73px)] max-w-6xl items-center px-6 py-16">
          <div className="w-full rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
            Loading sign-in page...
          </div>
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}
