"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { LogoutButton } from "../../../../components/logout-button";
import { useAuthSession } from "../../../../hooks/use-auth-session";
import { apiFetch } from "../../../../lib/api";
import type {
  ApiMessage,
  ExperimentDataset,
  ExperimentDatasetDetail,
  ExperimentOutput,
  ProjectDetail,
} from "../../../../lib/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatOutputType(value: ExperimentOutput["output_type"]) {
  return value.replaceAll("_", " ");
}

function ChartPreview({
  projectId,
  output,
}: {
  projectId: string;
  output: ExperimentOutput;
}) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    async function loadChart() {
      if (!output.chart_path) {
        setImageUrl(null);
        setError(null);
        return;
      }

      try {
        setError(null);
        const response = await apiFetch(`/api/projects/${projectId}/experiments/outputs/${output.id}/chart`, {
          method: "GET",
          headers: { Accept: "image/svg+xml" },
        });
        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as ApiMessage | null;
          throw new Error(payload?.detail || payload?.message || "Failed to load chart preview.");
        }
        const blob = await response.blob();
        objectUrl = window.URL.createObjectURL(blob);
        if (active) {
          setImageUrl(objectUrl);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "Failed to load chart preview.");
          setImageUrl(null);
        }
      }
    }

    void loadChart();
    return () => {
      active = false;
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl);
      }
    };
  }, [output.chart_path, output.id, projectId]);

  if (!output.chart_path) {
    return null;
  }

  if (error) {
    return <p className="text-sm text-red-700">{error}</p>;
  }

  if (!imageUrl) {
    return <p className="text-sm text-slate-500">Loading chart preview...</p>;
  }

  return <img src={imageUrl} alt={output.title} className="w-full rounded-3xl border border-slate-200 bg-white" />;
}

export default function ProjectExperimentAnalysisPage() {
  const params = useParams<{ projectId: string }>();
  const { user, isLoading, error, logout } = useAuthSession({ redirectToLogin: true });
  const projectId = params.projectId;
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [datasets, setDatasets] = useState<ExperimentDataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<ExperimentDatasetDetail | null>(null);
  const [outputs, setOutputs] = useState<ExperimentOutput[]>([]);
  const [selectedOutput, setSelectedOutput] = useState<ExperimentOutput | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [chartType, setChartType] = useState<"line" | "bar">("line");
  const [xField, setXField] = useState("");
  const [yField, setYField] = useState("");
  const [chartTitle, setChartTitle] = useState("");
  const [analysisPrompt, setAnalysisPrompt] = useState("");
  const [analysisTitle, setAnalysisTitle] = useState("");
  const [pageError, setPageError] = useState<string | null>(null);
  const [pageNotice, setPageNotice] = useState<string | null>(null);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isDatasetsLoading, setIsDatasetsLoading] = useState(true);
  const [isOutputsLoading, setIsOutputsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isStatsRunning, setIsStatsRunning] = useState(false);
  const [isChartRunning, setIsChartRunning] = useState(false);
  const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);
  const [deletingOutputId, setDeletingOutputId] = useState<string | null>(null);
  const [exportingOutputId, setExportingOutputId] = useState<string | null>(null);

  async function loadProject() {
    if (!user || !projectId) {
      return;
    }
    setIsProjectLoading(true);
    try {
      const response = await apiFetch(`/api/projects/${projectId}`, { method: "GET", cache: "no-store" });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to load project.");
      }
      setProject((await response.json()) as ProjectDetail);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load project.");
    } finally {
      setIsProjectLoading(false);
    }
  }

  async function loadDatasets(preferredDatasetId?: string) {
    if (!user || !projectId) {
      return;
    }
    setIsDatasetsLoading(true);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to load experiment datasets.");
      }
      const payload = (await response.json()) as ExperimentDataset[];
      setDatasets(payload);
      const nextDatasetId = preferredDatasetId || selectedDataset?.id || payload[0]?.id;
      if (nextDatasetId) {
        await openDataset(nextDatasetId);
      } else {
        setSelectedDataset(null);
      }
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load experiment datasets.");
    } finally {
      setIsDatasetsLoading(false);
    }
  }

  async function openDataset(datasetId: string) {
    if (!projectId) {
      return;
    }
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets/${datasetId}`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to load dataset detail.");
      }
      const payload = (await response.json()) as ExperimentDatasetDetail;
      setSelectedDataset(payload);
      const numericColumn = payload.columns.find((column) => column.inferred_type === "numeric");
      setXField((current) =>
        payload.columns.some((column) => column.name === current) ? current : payload.columns[0]?.name || "",
      );
      setYField((current) =>
        payload.columns.some((column) => column.name === current && column.inferred_type === "numeric")
          ? current
          : numericColumn?.name || "",
      );
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load dataset detail.");
    }
  }

  async function loadOutputs(preferredOutputId?: string) {
    if (!user || !projectId) {
      return;
    }
    setIsOutputsLoading(true);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/outputs`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to load experiment outputs.");
      }
      const payload = (await response.json()) as ExperimentOutput[];
      setOutputs(payload);
      const nextOutputId = preferredOutputId || selectedOutput?.id || payload[0]?.id;
      setSelectedOutput(payload.find((item) => item.id === nextOutputId) ?? payload[0] ?? null);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to load experiment outputs.");
    } finally {
      setIsOutputsLoading(false);
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId, user]);

  useEffect(() => {
    void loadDatasets();
    void loadOutputs();
  }, [projectId, user]);

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setPageError(null);
    setPageNotice(null);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || !selectedFile) {
      setPageError("Choose a CSV file before uploading.");
      return;
    }
    setIsUploading(true);
    setPageError(null);
    setPageNotice(null);
    try {
      const formData = new FormData();
      formData.append("upload", selectedFile);
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets`, {
        method: "POST",
        body: formData,
        skipJsonContentType: true,
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to upload CSV dataset.");
      }
      const payload = (await response.json()) as ExperimentDataset;
      setPageNotice(`Uploaded ${payload.original_filename}.`);
      setSelectedFile(null);
      event.currentTarget.reset();
      await loadDatasets(payload.id);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to upload CSV dataset.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleGenerateStats() {
    if (!projectId || !selectedDataset) {
      return;
    }
    setIsStatsRunning(true);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets/${selectedDataset.id}/stats`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to generate statistics.");
      }
      const payload = (await response.json()) as ExperimentOutput;
      setPageNotice("Statistics summary saved.");
      await loadOutputs(payload.id);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to generate statistics.");
    } finally {
      setIsStatsRunning(false);
    }
  }

  async function handleGenerateChart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || !selectedDataset || !xField || !yField) {
      setPageError("Select a dataset plus X and Y fields before generating a chart.");
      return;
    }
    setIsChartRunning(true);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets/${selectedDataset.id}/charts`, {
        method: "POST",
        body: JSON.stringify({
          chart_type: chartType,
          x_field: xField,
          y_field: yField,
          title: chartTitle.trim() || null,
        }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to generate chart.");
      }
      const payload = (await response.json()) as ExperimentOutput;
      setPageNotice("Chart output saved.");
      await loadOutputs(payload.id);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to generate chart.");
    } finally {
      setIsChartRunning(false);
    }
  }

  async function handleGenerateAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || !selectedDataset) {
      return;
    }
    setIsAnalysisRunning(true);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets/${selectedDataset.id}/analysis`, {
        method: "POST",
        body: JSON.stringify({
          title: analysisTitle.trim() || null,
          prompt: analysisPrompt.trim() || null,
        }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to generate experiment analysis.");
      }
      const payload = (await response.json()) as ExperimentOutput;
      setPageNotice("Experiment analysis saved.");
      await loadOutputs(payload.id);
    } catch (requestError) {
      setPageError(
        requestError instanceof Error ? requestError.message : "Failed to generate experiment analysis.",
      );
    } finally {
      setIsAnalysisRunning(false);
    }
  }

  async function handleDeleteDataset(dataset: ExperimentDataset) {
    if (!projectId) {
      return;
    }
    const confirmed = window.confirm(`Delete ${dataset.original_filename} and its saved outputs?`);
    if (!confirmed) {
      return;
    }
    setDeletingDatasetId(dataset.id);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/datasets/${dataset.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to delete experiment dataset.");
      }
      setPageNotice("Experiment dataset deleted.");
      if (selectedDataset?.id === dataset.id) {
        setSelectedDataset(null);
      }
      await Promise.all([loadDatasets(), loadOutputs()]);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to delete experiment dataset.");
    } finally {
      setDeletingDatasetId(null);
    }
  }

  async function handleDeleteOutput(output: ExperimentOutput) {
    if (!projectId) {
      return;
    }
    const confirmed = window.confirm(`Delete ${output.title}?`);
    if (!confirmed) {
      return;
    }
    setDeletingOutputId(output.id);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(`/api/projects/${projectId}/experiments/outputs/${output.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || "Failed to delete experiment output.");
      }
      setPageNotice("Experiment output deleted.");
      await loadOutputs();
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Failed to delete experiment output.");
    } finally {
      setDeletingOutputId(null);
    }
  }

  async function handleExport(output: ExperimentOutput, format: "markdown" | "latex") {
    if (!projectId) {
      return;
    }
    setExportingOutputId(output.id);
    setPageError(null);
    setPageNotice(null);
    try {
      const response = await apiFetch(
        `/api/projects/${projectId}/experiments/outputs/${output.id}/export/${format}`,
        {
          method: "GET",
          headers: { Accept: format === "markdown" ? "text/markdown" : "application/x-tex" },
        },
      );
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as ApiMessage | null;
        throw new Error(payload?.detail || payload?.message || `Failed to export ${format}.`);
      }
      const content = await response.text();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename=\"?([^\"]+)\"?/i);
      const filename = match?.[1] || `${output.title}.${format === "markdown" ? "md" : "tex"}`;
      const blob = new Blob([content], {
        type: format === "markdown" ? "text/markdown;charset=utf-8" : "application/x-tex;charset=utf-8",
      });
      const objectUrl = window.URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      window.document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(objectUrl);
      setPageNotice(`${format === "markdown" ? "Markdown" : "LaTeX"} export generated.`);
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : `Failed to export ${format}.`);
    } finally {
      setExportingOutputId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-slate-600 shadow-xl shadow-slate-200/40">
          Loading experiment analysis workspace...
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
              Project Experiment Analysis Workspace
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-ink">
              {project?.name || "Experiment analysis"}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              Upload CSV experiment datasets, preview parsed rows, generate descriptive statistics,
              create controlled SVG charts, and save bounded experiment-analysis outputs without
              executing any user code.
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

      <div className="grid gap-8 xl:grid-cols-[0.38fr_0.62fr]">
        <aside className="space-y-8">
          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <h2 className="text-xl font-semibold text-ink">Upload experiment CSV</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              Requests stay owner-scoped and project-scoped. The frontend continues using the
              existing HttpOnly Cookie session through <code>credentials: "include"</code>.
            </p>
            <form className="mt-6 space-y-5" onSubmit={handleUpload}>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileSelection}
                className="block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-full file:border-0 file:bg-ink file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
              />
              <button
                type="submit"
                disabled={isUploading}
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isUploading ? "Uploading..." : "Upload CSV dataset"}
              </button>
            </form>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">Datasets</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Only your current project datasets appear here.
                </p>
              </div>
              <div className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                {datasets.length} saved
              </div>
            </div>

            {isDatasetsLoading ? (
              <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5 text-sm text-slate-600">
                Loading datasets...
              </div>
            ) : datasets.length === 0 ? (
              <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-5 text-sm text-slate-600">
                No experiment datasets yet.
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {datasets.map((dataset) => (
                  <article key={dataset.id} className="rounded-3xl border border-slate-200 bg-mist p-5">
                    <button type="button" onClick={() => void openDataset(dataset.id)} className="w-full text-left">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                        {dataset.columns.length} columns | {dataset.row_count} rows
                      </p>
                      <h3 className="mt-2 text-lg font-semibold text-ink">{dataset.original_filename}</h3>
                      <p className="mt-2 text-xs text-slate-500">
                        {formatBytes(dataset.file_size)} | Updated {formatDate(dataset.updated_at)}
                      </p>
                    </button>
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => void handleDeleteDataset(dataset)}
                        disabled={deletingDatasetId === dataset.id}
                        className="rounded-full border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      >
                        {deletingDatasetId === dataset.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </aside>

        <section className="space-y-8">
          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">Dataset detail</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Parsed metadata and preview rows are bounded and read-only.
                </p>
              </div>
              {isProjectLoading ? (
                <span className="text-sm text-slate-500">Loading project...</span>
              ) : null}
            </div>

            {!selectedDataset ? (
              <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-6 text-sm text-slate-600">
                Select an experiment dataset to inspect its columns and preview rows.
              </div>
            ) : (
              <div className="mt-6 space-y-6">
                <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                  <h3 className="text-lg font-semibold text-ink">{selectedDataset.original_filename}</h3>
                  <p className="mt-2 text-sm text-slate-600">
                    {selectedDataset.row_count} rows | {selectedDataset.columns.length} columns
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    {selectedDataset.columns.map((column) => (
                      <span
                        key={column.name}
                        className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600"
                      >
                        {column.name}: {column.inferred_type}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid gap-6 xl:grid-cols-2">
                  <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold text-ink">Statistics</h3>
                        <p className="mt-2 text-sm leading-7 text-slate-600">
                          Generates descriptive summaries for numeric columns only.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleGenerateStats()}
                        disabled={isStatsRunning}
                        className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                      >
                        {isStatsRunning ? "Generating..." : "Generate stats"}
                      </button>
                    </div>
                  </div>

                  <form className="rounded-3xl border border-slate-200 bg-mist p-5" onSubmit={handleGenerateChart}>
                    <h3 className="text-lg font-semibold text-ink">Chart generation</h3>
                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <select
                        value={chartType}
                        onChange={(event) => setChartType(event.target.value as "line" | "bar")}
                        className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                      >
                        <option value="line">Line chart</option>
                        <option value="bar">Bar chart</option>
                      </select>
                      <input
                        type="text"
                        value={chartTitle}
                        onChange={(event) => setChartTitle(event.target.value)}
                        placeholder="Optional chart title"
                        className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                      />
                      <select
                        value={xField}
                        onChange={(event) => setXField(event.target.value)}
                        className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                      >
                        {selectedDataset.columns.map((column) => (
                          <option key={column.name} value={column.name}>
                            X: {column.name}
                          </option>
                        ))}
                      </select>
                      <select
                        value={yField}
                        onChange={(event) => setYField(event.target.value)}
                        className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                      >
                        {selectedDataset.columns
                          .filter((column) => column.inferred_type === "numeric")
                          .map((column) => (
                            <option key={column.name} value={column.name}>
                              Y: {column.name}
                            </option>
                          ))}
                      </select>
                    </div>
                    <button
                      type="submit"
                      disabled={isChartRunning || !xField || !yField}
                      className="mt-4 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                    >
                      {isChartRunning ? "Generating..." : "Generate chart"}
                    </button>
                  </form>
                </div>

                <form className="rounded-3xl border border-slate-200 bg-mist p-5" onSubmit={handleGenerateAnalysis}>
                  <h3 className="text-lg font-semibold text-ink">Experiment Analysis Skill</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    The saved result is grounded only in CSV-derived facts, statistics, chart metadata,
                    and your explicit framing.
                  </p>
                  <div className="mt-4 grid gap-4">
                    <input
                      type="text"
                      value={analysisTitle}
                      onChange={(event) => setAnalysisTitle(event.target.value)}
                      placeholder="Optional saved output title"
                      className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                    />
                    <textarea
                      value={analysisPrompt}
                      onChange={(event) => setAnalysisPrompt(event.target.value)}
                      placeholder="Describe what aspect of the experiment should be discussed in the bounded analysis."
                      className="min-h-32 rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cobalt focus:ring-2 focus:ring-cobalt/20"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isAnalysisRunning}
                    className="mt-4 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isAnalysisRunning ? "Generating..." : "Generate experiment analysis"}
                  </button>
                </form>

                <div className="overflow-x-auto rounded-3xl border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 bg-white text-sm text-slate-700">
                    <thead className="bg-mist">
                      <tr>
                        {selectedDataset.columns.map((column) => (
                          <th key={column.name} className="px-4 py-3 text-left font-semibold text-slate-600">
                            {column.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedDataset.preview_rows.length === 0 ? (
                        <tr>
                          <td colSpan={selectedDataset.columns.length || 1} className="px-4 py-5 text-slate-500">
                            No preview rows were available in this dataset.
                          </td>
                        </tr>
                      ) : (
                        selectedDataset.preview_rows.map((row, rowIndex) => (
                          <tr key={`preview-${rowIndex}`}>
                            {selectedDataset.columns.map((column) => (
                              <td key={`${rowIndex}-${column.name}`} className="px-4 py-3 align-top">
                                {row[column.name] || " "}
                              </td>
                            ))}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/40">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">Saved outputs</h2>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Outputs are owner-scoped and exportable as Markdown or LaTeX fragments only.
                </p>
              </div>
              <div className="rounded-full border border-slate-200 bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                {outputs.length} saved
              </div>
            </div>

            {isOutputsLoading ? (
              <div className="mt-6 rounded-3xl border border-slate-200 bg-mist p-5 text-sm text-slate-600">
                Loading outputs...
              </div>
            ) : outputs.length === 0 ? (
              <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-mist p-5 text-sm text-slate-600">
                No experiment outputs yet.
              </div>
            ) : (
              <div className="mt-6 grid gap-6 xl:grid-cols-[0.38fr_0.62fr]">
                <div className="space-y-4">
                  {outputs.map((output) => (
                    <article key={output.id} className="rounded-3xl border border-slate-200 bg-mist p-5">
                      <button type="button" onClick={() => setSelectedOutput(output)} className="w-full text-left">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          {formatOutputType(output.output_type)}
                        </p>
                        <h3 className="mt-2 text-lg font-semibold text-ink">{output.title}</h3>
                        <p className="mt-2 text-xs text-slate-500">Updated {formatDate(output.updated_at)}</p>
                      </button>
                      <div className="mt-4 flex flex-wrap gap-3">
                        <button
                          type="button"
                          onClick={() => void handleExport(output, "markdown")}
                          disabled={exportingOutputId === output.id}
                          className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                        >
                          {exportingOutputId === output.id ? "Exporting..." : "Export Markdown"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleExport(output, "latex")}
                          disabled={exportingOutputId === output.id}
                          className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                        >
                          {exportingOutputId === output.id ? "Exporting..." : "Export LaTeX"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDeleteOutput(output)}
                          disabled={deletingOutputId === output.id}
                          className="rounded-full border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                        >
                          {deletingOutputId === output.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="rounded-3xl border border-slate-200 bg-mist p-5">
                  {selectedOutput ? (
                    <div className="space-y-6">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                          {formatOutputType(selectedOutput.output_type)}
                        </p>
                        <h3 className="mt-2 text-2xl font-semibold text-ink">{selectedOutput.title}</h3>
                        <p className="mt-2 text-xs text-slate-500">Updated {formatDate(selectedOutput.updated_at)}</p>
                      </div>

                      {selectedOutput.chart_path ? (
                        <ChartPreview projectId={projectId} output={selectedOutput} />
                      ) : null}

                      {selectedOutput.content_markdown ? (
                        <pre className="whitespace-pre-wrap break-words rounded-3xl border border-slate-200 bg-white p-5 text-sm leading-7 text-slate-700">
                          {selectedOutput.content_markdown}
                        </pre>
                      ) : null}

                      {selectedOutput.stats_json ? (
                        <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white">
                          <table className="min-w-full divide-y divide-slate-200 text-sm text-slate-700">
                            <thead className="bg-mist">
                              <tr>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Column</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Count</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Mean</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Min</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Max</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-600">Std</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {Object.entries(selectedOutput.stats_json).map(([column, metric]) => (
                                <tr key={column}>
                                  <td className="px-4 py-3">{column}</td>
                                  <td className="px-4 py-3">{metric.count}</td>
                                  <td className="px-4 py-3">{metric.mean}</td>
                                  <td className="px-4 py-3">{metric.min}</td>
                                  <td className="px-4 py-3">{metric.max}</td>
                                  <td className="px-4 py-3">{metric.std}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-sm text-slate-600">
                      Select a saved output to inspect markdown, chart preview, and statistics here.
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </section>
      </div>
    </div>
  );
}
