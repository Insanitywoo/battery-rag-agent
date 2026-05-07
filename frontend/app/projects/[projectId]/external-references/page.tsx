"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { LogoutButton } from "../../../../components/logout-button";
import { useAuthSession } from "../../../../hooks/use-auth-session";
import { apiFetch } from "../../../../lib/api";
import type {
  ApiMessage,
  ExternalReference,
  ExternalReferenceSearchCandidate,
  ExternalReferenceSearchResponse,
  ProjectDetail,
} from "../../../../lib/types";

type ProviderOption = "all" | "crossref" | "arxiv";

const PROVIDER_OPTIONS: { label: string; value: ProviderOption }[] = [
  { label: "All providers", value: "all" },
  { label: "Crossref", value: "crossref" },
  { label: "arXiv", value: "arxiv" },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatAuthors(authors: string[]) {
  return authors.length > 0 ? authors.join(", ") : "Unknown authors";
}

export default function ProjectExternalReferencesPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [references, setReferences] = useState<ExternalReference[]>([]);
  const [results, setResults] = useState<ExternalReferenceSearchCandidate[]>([]);
  const [searchWarnings, setSearchWarnings] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [doi, setDoi] = useState("");
  const [provider, setProvider] = useState<ProviderOption>("all");
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isReferencesLoading, setIsReferencesLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [deletingReferenceId, setDeletingReferenceId] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
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
      const response = await apiFetch(`/api/projects/${projectId}`, { method: "GET", cache: "no-store" });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load project detail.");
      }
      setProject((await response.json()) as ProjectDetail);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load project detail.");
    } finally {
      setIsProjectLoading(false);
    }
  }

  async function loadReferences() {
    if (!user || !projectId) {
      return;
    }

    setIsReferencesLoading(true);
    setPageError(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/external-references`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to load saved external references.");
      }
      setReferences((await response.json()) as ExternalReference[]);
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to load saved external references.",
      );
    } finally {
      setIsReferencesLoading(false);
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  useEffect(() => {
    void loadReferences();
  }, [projectId, user]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || (!query.trim() && !doi.trim())) {
      setPageError("Enter keywords, a title, or a DOI before searching.");
      return;
    }

    setIsSearching(true);
    setPageError(null);
    setPageNotice(null);
    setSearchWarnings([]);

    try {
      const response = await apiFetch(`/api/projects/${projectId}/external-references/search`, {
        method: "POST",
        body: JSON.stringify({
          query: query.trim() || null,
          doi: doi.trim() || null,
          provider,
          limit: 6,
        }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to search external references.");
      }
      const payload = (await response.json()) as ExternalReferenceSearchResponse;
      setResults(payload.results);
      setSearchWarnings(payload.warnings);
      setPageNotice(`Found ${payload.results.length} deduplicated candidate reference${payload.results.length === 1 ? "" : "s"}.`);
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to search external references.",
      );
    } finally {
      setIsSearching(false);
    }
  }

  async function handleSave(candidate: ExternalReferenceSearchCandidate) {
    if (!projectId) {
      return;
    }

    setSavingKey(candidate.dedupe_key);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/external-references`, {
        method: "POST",
        body: JSON.stringify(candidate),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to save external reference.");
      }
      await loadReferences();
      setPageNotice("External reference saved to this project.");
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to save external reference.",
      );
    } finally {
      setSavingKey(null);
    }
  }

  async function handleDelete(reference: ExternalReference) {
    if (!projectId) {
      return;
    }
    const confirmed = window.confirm(`Delete saved reference "${reference.title}"?`);
    if (!confirmed) {
      return;
    }

    setDeletingReferenceId(reference.id);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/external-references/${reference.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to delete external reference.");
      }
      setReferences((current) => current.filter((item) => item.id !== reference.id));
      setPageNotice("External reference deleted.");
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to delete external reference.",
      );
    } finally {
      setDeletingReferenceId(null);
    }
  }

  async function handleExport() {
    if (!projectId) {
      return;
    }

    setIsExporting(true);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/external-references/export/bibtex`, {
        method: "GET",
        headers: { Accept: "application/x-bibtex" },
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.message || payload?.detail || "Failed to export BibTeX.");
      }
      const bibtex = await response.text();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename=\"?([^\"]+)\"?/i);
      const filename = match?.[1] || `external-references-${projectId}.bib`;
      const blob = new Blob([bibtex], { type: "application/x-bibtex;charset=utf-8" });
      const objectUrl = window.URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      window.document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(objectUrl);
      setPageNotice("BibTeX draft export generated. Please verify every citation manually.");
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to export BibTeX.");
    } finally {
      setIsExporting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading external references workspace...
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
              Project External References Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "External references"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Search Crossref and arXiv metadata from explicit user-entered queries, save curated references
              into this project, and export draft BibTeX without mixing external metadata into internal evidence.
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
              href={`/projects/${projectId}/writing`}
              className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Open paper writing
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

      <div className="grid gap-8 xl:grid-cols-[0.42fr_0.58fr]">
        <aside className="space-y-8">
          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <h2 className="text-xl font-semibold text-ink">Search external metadata</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              Searches use only the keywords, title text, or DOI that you type here. Private project files
              and chat content are never sent to external providers by this workspace.
            </p>

            <form className="mt-6 space-y-5" onSubmit={handleSearch}>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="external-query">
                  Keywords or title
                </label>
                <input
                  id="external-query"
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                  placeholder="lithium-ion battery degradation thermal management"
                  disabled={isSearching}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="external-doi">
                  DOI
                </label>
                <input
                  id="external-doi"
                  type="text"
                  value={doi}
                  onChange={(event) => setDoi(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                  placeholder="10.1038/example-doi"
                  disabled={isSearching}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="external-provider">
                  Provider
                </label>
                <select
                  id="external-provider"
                  value={provider}
                  onChange={(event) => setProvider(event.target.value as ProviderOption)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                >
                  {PROVIDER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={isSearching || (!query.trim() && !doi.trim())}
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isSearching ? "Searching..." : "Search references"}
              </button>
            </form>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">Saved references</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  These records stay owner-scoped and project-scoped. BibTeX export is draft-only.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleExport()}
                disabled={isExporting}
                className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
              >
                {isExporting ? "Exporting..." : "Export BibTeX"}
              </button>
            </div>

            {isReferencesLoading ? (
              <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5 text-sm text-slate-600">
                Loading saved references...
              </div>
            ) : references.length === 0 ? (
              <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-5 text-sm text-slate-600">
                No saved external references yet.
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {references.map((reference) => (
                  <article key={reference.id} className="rounded-3xl border border-slate-200 bg-mist p-5">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {reference.source} {reference.year ? `| ${reference.year}` : ""}
                    </p>
                    <h3 className="mt-2 text-lg font-semibold text-ink">{reference.title}</h3>
                    <p className="mt-2 text-sm leading-7 text-slate-600">{formatAuthors(reference.authors)}</p>
                    <p className="mt-2 text-sm leading-7 text-slate-600">
                      Venue: {reference.venue || "Unavailable"}
                    </p>
                    <p className="mt-1 text-sm leading-7 text-slate-600">
                      DOI: {reference.doi || "Unavailable"}
                    </p>
                    <p className="mt-1 break-all text-sm leading-7 text-slate-600">
                      URL: {reference.url || "Unavailable"}
                    </p>
                    {reference.abstract ? (
                      <p className="mt-3 text-sm leading-7 text-slate-600">{reference.abstract}</p>
                    ) : null}
                    {reference.warnings.length > 0 ? (
                      <ul className="mt-3 space-y-1 text-sm leading-7 text-amber-800">
                        {reference.warnings.map((warning) => (
                          <li key={warning}>- {warning}</li>
                        ))}
                      </ul>
                    ) : null}
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                      <p className="text-xs text-slate-500">Updated {formatDate(reference.updated_at)}</p>
                      <button
                        type="button"
                        onClick={() => void handleDelete(reference)}
                        disabled={deletingReferenceId === reference.id}
                        className="rounded-full border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      >
                        {deletingReferenceId === reference.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </aside>

        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-ink">Candidate results</h2>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                Search results are transient until you explicitly save them into this project.
              </p>
            </div>
            {isProjectLoading ? (
              <span className="text-sm text-slate-500">Loading project...</span>
            ) : (
              <span className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                {results.length} candidate{results.length === 1 ? "" : "s"}
              </span>
            )}
          </div>

          {searchWarnings.length > 0 ? (
            <div className="mt-6 rounded-3xl border border-amber-200 bg-amber-50 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">Provider warnings</p>
              <ul className="mt-3 space-y-2 text-sm leading-7 text-amber-900">
                {searchWarnings.map((warning) => (
                  <li key={warning}>- {warning}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {results.length === 0 ? (
            <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-10 text-sm text-slate-600">
              Search by title, keyword, or DOI to review external paper metadata here.
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {results.map((candidate) => (
                <article key={candidate.dedupe_key} className="rounded-3xl border border-slate-200 bg-mist p-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {candidate.source} {candidate.year ? `| ${candidate.year}` : ""}
                  </p>
                  <h3 className="mt-2 text-lg font-semibold text-ink">{candidate.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-600">{formatAuthors(candidate.authors)}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    Venue: {candidate.venue || "Unavailable"}
                  </p>
                  <p className="mt-1 text-sm leading-7 text-slate-600">
                    DOI: {candidate.doi || "Unavailable"}
                  </p>
                  <p className="mt-1 break-all text-sm leading-7 text-slate-600">
                    URL: {candidate.url || "Unavailable"}
                  </p>
                  {candidate.abstract ? (
                    <p className="mt-3 text-sm leading-7 text-slate-600">{candidate.abstract}</p>
                  ) : null}
                  {candidate.warnings.length > 0 ? (
                    <ul className="mt-3 space-y-1 text-sm leading-7 text-amber-800">
                      {candidate.warnings.map((warning) => (
                        <li key={warning}>- {warning}</li>
                      ))}
                    </ul>
                  ) : null}
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => void handleSave(candidate)}
                      disabled={savingKey === candidate.dedupe_key}
                      className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                    >
                      {savingKey === candidate.dedupe_key ? "Saving..." : "Save to project"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
