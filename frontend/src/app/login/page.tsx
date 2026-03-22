"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Notice } from "@/components/ui/notice";
import type { MeResponse } from "@/types/api";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("admin@local.demo");
  const [password, setPassword] = useState("AdminPassword!ChangeMe");
  const [rememberMe, setRememberMe] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiFetch<MeResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          remember_me: rememberMe,
        }),
      });

      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 lg:grid-cols-2">
        <section className="hidden lg:flex flex-col justify-between bg-slate-900 px-12 py-12 text-white">
          <div>
            <div className="inline-flex rounded-full border border-white/20 px-3 py-1 text-xs tracking-wide text-slate-200">
              RheumaAssist · Local-first clinical prototype
            </div>

            <h1 className="mt-8 text-5xl font-bold leading-tight">
              AI-assisted radiographic review for rheumatology workflows
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-slate-300">
              RheumaAssist was designed to support clinicians in the early
              radiographic assessment of rheumatoid arthritis by combining
              patient records, ROI-based image analysis, clinician review, and
              longitudinal follow-up in one local-first application.
            </p>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm font-semibold text-white">
                Intended for clinicians and authorized staff
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                AI output is assistive only. Final interpretation remains the
                responsibility of the licensed clinician.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm font-semibold text-white">
                Core workflow
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Patient registry → ROI or full radiograph upload → AI result →
                clinician review → longitudinal tracking.
              </p>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-6 py-10">
          <div className="w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div>
              <h2 className="text-4xl font-bold text-slate-900">RheumaAssist</h2>
              <p className="mt-3 text-slate-600 leading-7">
                Sign in to access the local clinical prototype for AI-assisted
                radiographic assessment in rheumatology.
              </p>
            </div>

            <div className="mt-6 lg:hidden">
              <Notice tone="info" title="Clinical scope">
                This application supports early radiographic review and
                longitudinal follow-up. It does not independently diagnose
                rheumatoid arthritis.
              </Notice>
            </div>

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@hospital.local"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <label className="flex items-center gap-3 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Remember me
              </label>

              {error && (
                <Notice tone="error" title="Authentication failed">
                  {error}
                </Notice>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-base font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-900">Demo access</p>
              <p className="mt-1 text-sm text-slate-600">
                Use the seeded demo account for local testing.
              </p>
              <div className="mt-3 text-sm text-slate-700">
                <p>Email: admin@local.demo</p>
                <p>Password: AdminPassword!ChangeMe</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}