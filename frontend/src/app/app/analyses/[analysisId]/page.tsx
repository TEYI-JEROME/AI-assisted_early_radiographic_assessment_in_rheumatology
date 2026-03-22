"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type {
  AnalysisDetailResponse,
  ReviewCreateRequest,
  ReviewResponse,
} from "@/types/api";

function formatProbability(value: number | null) {
  if (value === null || Number.isNaN(value)) return "N/A";
  return value.toFixed(6);
}

function predictionLabel(value: number | null) {
  if (value === null) return "N/A";
  return value === 1 ? "Erosion predicted" : "No erosion predicted";
}

export default function AnalysisDetailPage() {
  const params = useParams<{ analysisId: string }>();
  const analysisId = params.analysisId;

  const [data, setData] = useState<AnalysisDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [decision, setDecision] =
    useState<ReviewCreateRequest["decision"]>("UNCERTAIN");
  const [freeText, setFreeText] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);
  const [savedReview, setSavedReview] = useState<ReviewResponse | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

  useEffect(() => {
    async function loadAnalysis() {
      try {
        const result = await apiFetch<AnalysisDetailResponse>(
          `/analyses/${analysisId}`
        );
        setData(result);

        if (result.latest_review) {
          setSavedReview(result.latest_review);
          setDecision(
            (result.latest_review.decision as
              | "CONFIRMED"
              | "NOT_CONFIRMED"
              | "UNCERTAIN"
              | null) ?? "UNCERTAIN"
          );
          setFreeText(result.latest_review.free_text ?? "");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analysis.");
      } finally {
        setLoading(false);
      }
    }

    if (analysisId) {
      loadAnalysis();
    }
  }, [analysisId]);

  async function submitReview(mode: "draft" | "finalize") {
    if (!data) return;

    setReviewLoading(true);
    setReviewError(null);
    setReviewSuccess(null);

    try {
      const payload: ReviewCreateRequest = {
        decision,
        structured_note: {
          source: "frontend_v1",
          analysis_id: data.id,
          patient_id: data.patient?.patient_id ?? null,
          exam_date: data.exam?.exam_date ?? null,
          ai_prediction: data.predicted_class,
          erosion_probability: data.erosion_probability,
          threshold: data.threshold,
        },
        free_text: freeText.trim() ? freeText.trim() : null,
      };

      const endpoint =
        mode === "draft"
          ? `/reviews/${analysisId}/draft`
          : `/reviews/${analysisId}/finalize`;

      const result = await apiFetch<ReviewResponse>(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSavedReview(result);
      setReviewSuccess(
        mode === "draft"
          ? "Draft review saved successfully."
          : "Clinical review finalized successfully."
      );
    } catch (err) {
      setReviewError(
        err instanceof Error ? err.message : "Failed to submit review."
      );
    } finally {
      setReviewLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Analysis result</h1>
            <p className="mt-1 text-slate-600">
              Review the assistive erosion output before clinician validation.
            </p>
          </div>

          <div className="flex gap-3">
            <Link
              href="/app/analyses/new"
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
            >
              New analysis
            </Link>

            <Link
              href="/app"
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
            >
              Dashboard
            </Link>
          </div>
        </div>

        {loading && <p className="mt-6 text-slate-600">Loading analysis...</p>}

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && data && (
          <div className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Analysis ID</p>
                    <p className="mt-1 font-medium text-slate-900 break-all">
                      {data.id}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Status</p>
                    <p className="mt-1 font-medium text-slate-900">{data.status}</p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Patient</p>
                    <p className="mt-1 font-medium text-slate-900">
                      {data.patient
                        ? `${data.patient.patient_id} — ${data.patient.full_name}`
                        : "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Exam Date</p>
                    <p className="mt-1 font-medium text-slate-900">
                      {data.exam?.exam_date ?? "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Erosion Probability</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {formatProbability(data.erosion_probability)}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm text-slate-500">Threshold</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {formatProbability(data.threshold)}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4 md:col-span-2">
                    <p className="text-sm text-slate-500">Prediction</p>
                    <p className="mt-1 font-medium text-slate-900">
                      {predictionLabel(data.predicted_class)}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-4 md:col-span-2">
                    <p className="text-sm text-slate-500">Model Version</p>
                    <p className="mt-1 font-medium text-slate-900">
                      {data.model_version ?? "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">
                      ROI preview
                    </h2>
                    <p className="mt-1 text-sm text-slate-600">
                      Uploaded wrist ROI used for AI inference.
                    </p>
                  </div>

                  {data.roi_image_id && (
                    <a
                      href={`${apiBase}/images/${data.roi_image_id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100"
                    >
                      Open image
                    </a>
                  )}
                </div>

                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 min-h-[320px] flex items-center justify-center overflow-hidden">
                  {data.roi_image_id ? (
                    <img
                      src={`${apiBase}/images/${data.roi_image_id}`}
                      alt="ROI preview"
                      className="max-h-[500px] w-auto rounded-xl border border-slate-200 bg-white object-contain"
                    />
                  ) : (
                    <p className="text-sm text-slate-500">No ROI image available.</p>
                  )}
                </div>
              </div>
            </div>

            {data.error_message && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {data.error_message}
              </div>
            )}

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              AI output is assistive and must be reviewed by a licensed clinician.
              This system does not independently diagnose rheumatoid arthritis.
            </div>

            <div className="rounded-2xl border border-slate-200 p-6">
              <h2 className="text-xl font-semibold text-slate-900">
                Clinician review
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Record the clinical decision linked to this AI-assisted result.
              </p>

              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Decision
                  </label>
                  <select
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                    value={decision}
                    onChange={(e) =>
                      setDecision(
                        e.target.value as
                          | "CONFIRMED"
                          | "NOT_CONFIRMED"
                          | "UNCERTAIN"
                      )
                    }
                    disabled={reviewLoading}
                  >
                    <option value="CONFIRMED">CONFIRMED</option>
                    <option value="NOT_CONFIRMED">NOT_CONFIRMED</option>
                    <option value="UNCERTAIN">UNCERTAIN</option>
                  </select>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Current AI summary</p>
                  <p className="mt-2 text-sm text-slate-800">
                    Probability: {formatProbability(data.erosion_probability)}
                  </p>
                  <p className="text-sm text-slate-800">
                    Threshold: {formatProbability(data.threshold)}
                  </p>
                  <p className="text-sm text-slate-800">
                    Prediction: {predictionLabel(data.predicted_class)}
                  </p>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Free text note
                  </label>
                  <textarea
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 min-h-[140px] outline-none focus:ring-2 focus:ring-slate-300"
                    value={freeText}
                    onChange={(e) => setFreeText(e.target.value)}
                    placeholder="Enter the clinician's interpretation, comments, or justification."
                    disabled={reviewLoading}
                  />
                </div>
              </div>

              {reviewError && (
                <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {reviewError}
                </div>
              )}

              {reviewSuccess && (
                <div className="mt-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
                  {reviewSuccess}
                </div>
              )}

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => submitReview("draft")}
                  disabled={reviewLoading}
                  className="rounded-xl border border-slate-300 px-5 py-2.5 text-sm hover:bg-slate-100 disabled:opacity-60"
                >
                  {reviewLoading ? "Saving..." : "Save draft"}
                </button>

                <button
                  type="button"
                  onClick={() => submitReview("finalize")}
                  disabled={reviewLoading}
                  className="rounded-xl bg-slate-900 text-white px-5 py-2.5 text-sm hover:bg-slate-800 disabled:opacity-60"
                >
                  {reviewLoading ? "Submitting..." : "Finalize review"}
                </button>
              </div>

              {savedReview && (
                <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Latest saved review
                  </h3>
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-slate-500">Status: </span>
                      <span className="text-slate-900">{savedReview.status}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Decision: </span>
                      <span className="text-slate-900">
                        {savedReview.decision ?? "N/A"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Version: </span>
                      <span className="text-slate-900">{savedReview.version}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Signed at: </span>
                      <span className="text-slate-900">
                        {savedReview.signed_at ?? "Not signed"}
                      </span>
                    </div>
                  </div>

                  {savedReview.free_text && (
                    <div className="mt-3">
                      <p className="text-slate-500 text-sm">Free text</p>
                      <p className="mt-1 text-sm text-slate-900 whitespace-pre-wrap">
                        {savedReview.free_text}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}