"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Notice } from "@/components/ui/notice";
import type {
  AnalysisItem,
  AnalysisListResponse,
  MeResponse,
  PatientListResponse,
} from "@/types/api";

type RecentAnalysisRow = AnalysisItem & {
  patient_public_id: string;
  patient_name: string;
};

function formatProbability(value: number | null) {
  if (value === null || Number.isNaN(value)) return "N/A";
  return value.toFixed(6);
}

function predictionLabel(value: number | null) {
  if (value === null) return "N/A";
  return value === 1 ? "Erosion predicted" : "No erosion predicted";
}

function reviewBadgeClass(status: string | null) {
  if (status === "FINAL") {
    return "bg-green-100 text-green-800 border border-green-200";
  }
  if (status === "DRAFT") {
    return "bg-amber-100 text-amber-800 border border-amber-200";
  }
  return "bg-slate-100 text-slate-700 border border-slate-200";
}

function reviewLabel(status: string | null, decision: string | null) {
  if (!status) return "No review";
  return decision ? `${status} · ${decision}` : status;
}

export default function AppHomePage() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [patientsCount, setPatientsCount] = useState(0);
  const [analysesCount, setAnalysesCount] = useState(0);
  const [finalReviewsCount, setFinalReviewsCount] = useState(0);
  const [draftReviewsCount, setDraftReviewsCount] = useState(0);
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysisRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasData = useMemo(
    () => patientsCount > 0 || analysesCount > 0 || recentAnalyses.length > 0,
    [patientsCount, analysesCount, recentAnalyses.length]
  );

  useEffect(() => {
    async function loadDashboard() {
      try {
        const meResult = await apiFetch<MeResponse>("/auth/me");
        setMe(meResult);

        const patientsResult = await apiFetch<PatientListResponse>(
          "/patients?page=1&page_size=100"
        );

        setPatientsCount(patientsResult.total ?? patientsResult.items.length);

        const analysisResponses = await Promise.all(
          patientsResult.items.map(async (patient) => {
            const result = await apiFetch<AnalysisListResponse>(
              `/analyses/by-patient/${patient.patient_id}`
            );

            return {
              patient_public_id: patient.patient_id,
              patient_name: patient.full_name,
              analyses: result.items,
            };
          })
        );

        const flattened: RecentAnalysisRow[] = analysisResponses.flatMap((entry) =>
          entry.analyses.map((analysis) => ({
            ...analysis,
            patient_public_id: entry.patient_public_id,
            patient_name: entry.patient_name,
          }))
        );

        flattened.sort((a, b) => {
          const da = new Date(a.created_at).getTime();
          const db = new Date(b.created_at).getTime();
          return db - da;
        });

        setRecentAnalyses(flattened.slice(0, 8));
        setAnalysesCount(flattened.length);
        setFinalReviewsCount(
          flattened.filter((a) => a.latest_review_status === "FINAL").length
        );
        setDraftReviewsCount(
          flattened.filter((a) => a.latest_review_status === "DRAFT").length
        );
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load dashboard."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return <main>Loading dashboard...</main>;
  }

  return (
    <main className="space-y-6">
      <section className="rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 px-8 py-8 text-white shadow-sm">
        <div className="max-w-4xl">
          <div className="inline-flex rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs tracking-wide text-slate-200">
            AI-assisted rheumatology workflow
          </div>

          <h1 className="mt-5 text-4xl font-bold leading-tight">
            Welcome{me ? `, Dr. ${me.full_name}` : ""}.
          </h1>

          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-200">
            RheumaAssist supports clinicians in early radiographic review by
            combining patient registration, ROI-based AI analysis, clinician
            review, and longitudinal follow-up in one local-first environment.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/app/patients"
              className="rounded-2xl bg-white px-4 py-3 text-sm font-medium text-slate-900 hover:bg-slate-100"
            >
              Open patient registry
            </Link>

            <Link
              href="/app/analyses/new"
              className="rounded-2xl border border-white/20 px-4 py-3 text-sm font-medium text-white hover:bg-white/10"
            >
              Start new analysis
            </Link>
          </div>
        </div>
      </section>

      <Notice tone="warning" title="Clinical safety note">
        AI output is assistive only and must be reviewed by a licensed
        clinician. This system does not independently diagnose rheumatoid
        arthritis.
      </Notice>

      {error && (
        <Notice tone="error" title="Dashboard loading error">
          {error}
        </Notice>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6">
          <p className="text-sm text-slate-500">Registered patients</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{patientsCount}</p>
        </div>

        <div className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6">
          <p className="text-sm text-slate-500">Total analyses</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{analysesCount}</p>
        </div>

        <div className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6">
          <p className="text-sm text-slate-500">Final reviews</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{finalReviewsCount}</p>
        </div>

        <div className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6">
          <p className="text-sm text-slate-500">Draft reviews</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{draftReviewsCount}</p>
        </div>
      </div>

      <section className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Recent analyses
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Latest AI-assisted analyses across registered patients.
            </p>
          </div>

          {hasData && (
            <Link
              href="/app/patients"
              className="rounded-2xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
            >
              View all patients
            </Link>
          )}
        </div>

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full border border-slate-200 rounded-2xl overflow-hidden">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Patient
                </th>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Exam Date
                </th>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Probability
                </th>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Prediction
                </th>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Review
                </th>
                <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {recentAnalyses.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-sm text-slate-500 text-center"
                  >
                    No analyses available yet.
                  </td>
                </tr>
              ) : (
                recentAnalyses.map((analysis) => (
                  <tr key={analysis.id} className="border-t border-slate-200">
                    <td className="px-4 py-3 text-sm text-slate-800">
                      <div className="font-medium">
                        {analysis.patient_public_id}
                      </div>
                      <div className="text-slate-500">
                        {analysis.patient_name}
                      </div>
                    </td>

                    <td className="px-4 py-3 text-sm text-slate-800">
                      {analysis.exam_date ?? "N/A"}
                    </td>

                    <td className="px-4 py-3 text-sm text-slate-800">
                      {formatProbability(analysis.erosion_probability)}
                    </td>

                    <td className="px-4 py-3 text-sm text-slate-800">
                      {predictionLabel(analysis.predicted_class)}
                    </td>

                    <td className="px-4 py-3 text-sm text-slate-800">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${reviewBadgeClass(
                          analysis.latest_review_status
                        )}`}
                      >
                        {reviewLabel(
                          analysis.latest_review_status,
                          analysis.latest_review_decision
                        )}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-sm">
                      <Link
                        href={`/app/analyses/${analysis.id}`}
                        className="rounded-xl border border-slate-300 px-3 py-2 hover:bg-slate-100"
                      >
                        View result
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}