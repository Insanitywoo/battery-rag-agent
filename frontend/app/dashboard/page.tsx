const cards = [
  "Projects",
  "Documents",
  "Usage",
  "Recent outputs",
];

export default function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16">
      <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-xl shadow-slate-200/40">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cobalt">
          Dashboard Placeholder
        </p>
        <h1 className="mt-4 text-4xl font-semibold text-ink">
          Workspace shell for future project features
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600">
          This route is intentionally limited to layout scaffolding. It exists so
          later changes can add authenticated project navigation, document views,
          and research workflows without reshaping the app.
        </p>
      </section>

      <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article
            key={card}
            className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg shadow-slate-200/30"
          >
            <h2 className="text-lg font-semibold text-ink">{card}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              Placeholder only. No product data, auth, RAG, or agent workflow is
              implemented in this bootstrap change.
            </p>
          </article>
        ))}
      </section>
    </div>
  );
}
