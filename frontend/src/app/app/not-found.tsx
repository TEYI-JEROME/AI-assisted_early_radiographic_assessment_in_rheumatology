import Link from "next/link";

export default function AppNotFound() {
  return (
    <main className="p-8">
      <div className="max-w-2xl mx-auto rounded-2xl border border-slate-200 bg-white p-8 shadow-sm text-center">
        <h1 className="text-3xl font-bold text-slate-900">Page not found</h1>
        <p className="mt-3 text-slate-600">
          The page you are looking for does not exist in this RheumaAssist workspace.
        </p>

        <div className="mt-6 flex justify-center gap-3">
          <Link
            href="/app"
            className="rounded-xl bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800"
          >
            Go to dashboard
          </Link>

          <Link
            href="/app/patients"
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
          >
            Open patients
          </Link>
        </div>
      </div>
    </main>
  );
}