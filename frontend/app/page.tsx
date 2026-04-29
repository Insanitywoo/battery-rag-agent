import Link from "next/link";

const pillars = [
  "Project-scoped research workspaces",
  "Evidence-grounded RAG answers",
  "Agent-driven literature workflows",
  "Structured export and reporting paths",
];

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-16 px-6 py-16">
      <section className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr] lg:items-center">
        <div className="space-y-6">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cobalt">
            Product Shell
          </p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-tight text-ink">
            Battery-RAG Agent bootstrap landing page
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-600">
            This placeholder marks the future public entry point for an online
            research assistant focused on battery systems, control engineering,
            and AI-enabled literature workflows.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/dashboard"
              className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              View dashboard placeholder
            </Link>
            <span className="rounded-full border border-slate-300 px-6 py-3 text-sm text-slate-600">
              Scope limited to bootstrap UI only
            </span>
          </div>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/50">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-ember">
            Planned pillars
          </p>
          <ul className="mt-6 space-y-4">
            {pillars.map((pillar) => (
              <li
                key={pillar}
                className="rounded-2xl border border-slate-200 bg-mist px-4 py-4 text-sm text-slate-700"
              >
                {pillar}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg shadow-slate-200/40">
          <h2 className="text-lg font-semibold text-ink">What exists now</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            A frontend shell with placeholder routes, ready for future auth,
            project navigation, and product workflows.
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg shadow-slate-200/40">
          <h2 className="text-lg font-semibold text-ink">What comes later</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Login, document ingestion, RAG chat, agent task execution, and
            export workflows are intentionally deferred beyond this bootstrap.
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg shadow-slate-200/40">
          <h2 className="text-lg font-semibold text-ink">Why this page exists</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            It validates routing, styling, and application structure without
            pretending the product is functionally implemented yet.
          </p>
        </div>
      </section>
    </div>
  );
}
