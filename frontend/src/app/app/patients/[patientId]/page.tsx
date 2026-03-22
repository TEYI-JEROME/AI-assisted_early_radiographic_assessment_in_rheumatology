"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type {
  AnalysisItem,
  AnalysisListResponse,
  PatientResponse,
} from "@/types/api";

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

function comparisonSummary(newer: AnalysisItem | null, older: AnalysisItem | null) {
  if (!newer || !older) return "Select two analyses to compare longitudinally.";

  if (
    newer.erosion_probability === null ||
    older.erosion_probability === null ||
    Number.isNaN(newer.erosion_probability) ||
    Number.isNaN(older.erosion_probability)
  ) {
    return "Probability comparison is not available for one or both analyses.";
  }

  const delta = newer.erosion_probability - older.erosion_probability;

  if (Math.abs(delta) < 1e-6) {
    return "The erosion probability is unchanged between the two selected analyses.";
  }

  if (delta > 0) {
    return `The newer analysis shows a higher erosion probability by ${delta.toFixed(6)}.`;
  }

  return `The newer analysis shows a lower erosion probability by ${Math.abs(delta).toFixed(6)}.`;
}

export default function PatientDetailPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [patient, setPatient] = useState<PatientResponse | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newerAnalysisId, setNewerAnalysisId] = useState("");
  const [olderAnalysisId, setOlderAnalysisId] = useState("");

  useEffect(() => {
    async function loadPatientData() {
      try {
        const [patientResult, analysesResult] = await Promise.all([
          apiFetch<PatientResponse>(`/patients/${patientId}`),
          apiFetch<AnalysisListResponse>(`/analyses/by-patient/${patientId}`),
        ]);

        setPatient(patientResult);
        setAnalyses(analysesResult);

        const items = analysesResult.items ?? [];
        if (items.length > 0) {
          setNewerAnalysisId(items[0].id);
        }
        if (items.length > 1) {
          setOlderAnalysisId(items[1].id);
        } else if (items.length === 1) {
          setOlderAnalysisId(items[0].id);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load patient details."
        );
      } finally {
        setLoading(false);
      }
    }

    if (patientId) {
      loadPatientData();
    }
  }, [patientId]);

  const analysisItems = analyses?.items ?? [];

  const newerAnalysis = useMemo(
    () => analysisItems.find((a) => a.id === newerAnalysisId) ?? null,
    [analysisItems, newerAnalysisId]
  );

  const olderAnalysis = useMemo(
    () => analysisItems.find((a) => a.id === olderAnalysisId) ?? null,
    [analysisItems, olderAnalysisId]
  );

  const probabilityDelta =
    newerAnalysis &&
    olderAnalysis &&
    newerAnalysis.erosion_probability !== null &&
    olderAnalysis.erosion_probability !== null
      ? newerAnalysis.erosion_probability - olderAnalysis.erosion_probability
      : null;

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Patient details</h1>
              <p className="mt-1 text-slate-600">
                Clinical overview and longitudinal analysis history.
              </p>
            </div>

            <div className="flex gap-3">
              <Link
                href="/app/analyses/new"
                className="rounded-xl bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800"
              >
                New analysis
              </Link>

              <Link
                href="/app/patients"
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
              >
                Back to patients
              </Link>
            </div>
          </div>

          {loading && <p className="mt-6 text-slate-600">Loading patient...</p>}

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && patient && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Patient ID</p>
                <p className="mt-1 font-medium text-slate-900">{patient.patient_id}</p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Hospital Number</p>
                <p className="mt-1 font-medium text-slate-900">{patient.hospital_number}</p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Full Name</p>
                <p className="mt-1 font-medium text-slate-900">{patient.full_name}</p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Date of Birth</p>
                <p className="mt-1 font-medium text-slate-900">{patient.date_of_birth}</p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Sex</p>
                <p className="mt-1 font-medium text-slate-900">{patient.sex}</p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Notes</p>
                <p className="mt-1 font-medium text-slate-900">
                  {patient.notes?.trim() ? patient.notes : "No notes"}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Longitudinal comparison
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Compare two analyses of the same patient over time.
              </p>
            </div>
          </div>

          {!loading && !error && (
            <div className="mt-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Newer analysis
                  </label>
                  <select
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                    value={newerAnalysisId}
                    onChange={(e) => setNewerAnalysisId(e.target.value)}
                  >
                    {analysisItems.map((analysis) => (
                      <option key={analysis.id} value={analysis.id}>
                        {analysis.exam_date ?? "N/A"} — {analysis.id.slice(0, 8)} —{" "}
                        {predictionLabel(analysis.predicted_class)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Older analysis
                  </label>
                  <select
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                    value={olderAnalysisId}
                    onChange={(e) => setOlderAnalysisId(e.target.value)}
                  >
                    {analysisItems.map((analysis) => (
                      <option key={analysis.id} value={analysis.id}>
                        {analysis.exam_date ?? "N/A"} — {analysis.id.slice(0, 8)} —{" "}
                        {predictionLabel(analysis.predicted_class)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {analysisItems.length < 2 ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  At least two analyses are needed for longitudinal comparison.
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">Newer analysis</p>
                      <div className="mt-3 space-y-2 text-sm text-slate-800">
                        <p>
                          <span className="text-slate-500">Exam date: </span>
                          {newerAnalysis?.exam_date ?? "N/A"}
                        </p>
                        <p>
                          <span className="text-slate-500">Probability: </span>
                          {formatProbability(newerAnalysis?.erosion_probability ?? null)}
                        </p>
                        <p>
                          <span className="text-slate-500">Prediction: </span>
                          {predictionLabel(newerAnalysis?.predicted_class ?? null)}
                        </p>
                        <p>
                          <span className="text-slate-500">Review: </span>
                          {reviewLabel(
                            newerAnalysis?.latest_review_status ?? null,
                            newerAnalysis?.latest_review_decision ?? null
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">Older analysis</p>
                      <div className="mt-3 space-y-2 text-sm text-slate-800">
                        <p>
                          <span className="text-slate-500">Exam date: </span>
                          {olderAnalysis?.exam_date ?? "N/A"}
                        </p>
                        <p>
                          <span className="text-slate-500">Probability: </span>
                          {formatProbability(olderAnalysis?.erosion_probability ?? null)}
                        </p>
                        <p>
                          <span className="text-slate-500">Prediction: </span>
                          {predictionLabel(olderAnalysis?.predicted_class ?? null)}
                        </p>
                        <p>
                          <span className="text-slate-500">Review: </span>
                          {reviewLabel(
                            olderAnalysis?.latest_review_status ?? null,
                            olderAnalysis?.latest_review_decision ?? null
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <h3 className="text-sm font-semibold text-slate-900">
                      Comparison summary
                    </h3>
                    <p className="mt-2 text-sm text-slate-700">
                      {comparisonSummary(newerAnalysis, olderAnalysis)}
                    </p>

                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <p className="text-sm text-slate-500">Probability delta</p>
                        <p className="mt-1 text-lg font-semibold text-slate-900">
                          {probabilityDelta === null || Number.isNaN(probabilityDelta)
                            ? "N/A"
                            : probabilityDelta > 0
                            ? `+${probabilityDelta.toFixed(6)}`
                            : probabilityDelta.toFixed(6)}
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <p className="text-sm text-slate-500">Newer review</p>
                        <p className="mt-1">
                          <span
                            className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${reviewBadgeClass(
                              newerAnalysis?.latest_review_status ?? null
                            )}`}
                          >
                            {reviewLabel(
                              newerAnalysis?.latest_review_status ?? null,
                              newerAnalysis?.latest_review_decision ?? null
                            )}
                          </span>
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <p className="text-sm text-slate-500">Older review</p>
                        <p className="mt-1">
                          <span
                            className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${reviewBadgeClass(
                              olderAnalysis?.latest_review_status ?? null
                            )}`}
                          >
                            {reviewLabel(
                              olderAnalysis?.latest_review_status ?? null,
                              olderAnalysis?.latest_review_decision ?? null
                            )}
                          </span>
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-3">
                      {newerAnalysis && (
                        <Link
                          href={`/app/analyses/${newerAnalysis.id}`}
                          className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
                        >
                          Open newer analysis
                        </Link>
                      )}

                      {olderAnalysis && (
                        <Link
                          href={`/app/analyses/${olderAnalysis.id}`}
                          className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
                        >
                          Open older analysis
                        </Link>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Analysis history
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Previous AI-assisted analyses for this patient.
              </p>
            </div>

            <p className="text-sm text-slate-500">
              Total analyses: {analyses?.items.length ?? 0}
            </p>
          </div>

          {!loading && !error && (
            <div className="mt-6 overflow-x-auto">
              <table className="min-w-full border border-slate-200 rounded-xl overflow-hidden">
                <thead className="bg-slate-100 text-left">
                  <tr>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Exam Date</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Status</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Probability</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Prediction</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Review</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Model</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(analyses?.items ?? []).length === 0 ? (
                    <tr>
                      <td
                        colSpan={7}
                        className="px-4 py-6 text-sm text-slate-500 text-center"
                      >
                        No analyses available for this patient yet.
                      </td>
                    </tr>
                  ) : (
                    analyses?.items.map((analysis) => (
                      <tr key={analysis.id} className="border-t border-slate-200">
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {analysis.exam_date ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {analysis.status}
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
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {analysis.model_version ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <Link
                            href={`/app/analyses/${analysis.id}`}
                            className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100"
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
          )}
        </div>
      </div>
    </main>
  );
}