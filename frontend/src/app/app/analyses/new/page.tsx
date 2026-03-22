"use client";

import Link from "next/link";
import { FormEvent, MouseEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type {
  AnalysisCreateResponse,
  PatientListResponse,
} from "@/types/api";

type AnalysisMode = "ROI_DIRECT" | "FULL_WITH_MANUAL_ROI";

type CropBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type Point = {
  x: number;
  y: number;
};

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export default function NewAnalysisPage() {
  const router = useRouter();
  const imageRef = useRef<HTMLImageElement | null>(null);

  const [patients, setPatients] = useState<PatientListResponse | null>(null);
  const [patientsLoading, setPatientsLoading] = useState(true);

  const [mode, setMode] = useState<AnalysisMode>("ROI_DIRECT");
  const [patientId, setPatientId] = useState("");
  const [examDate, setExamDate] = useState("");

  const [roiImage, setRoiImage] = useState<File | null>(null);
  const [fullImage, setFullImage] = useState<File | null>(null);
  const [fullImageUrl, setFullImageUrl] = useState<string | null>(null);

  const [displayCrop, setDisplayCrop] = useState<CropBox | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<Point | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPatients() {
      try {
        const result = await apiFetch<PatientListResponse>("/patients");
        setPatients(result);
        if (result.items.length > 0) {
          setPatientId(result.items[0].patient_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load patients.");
      } finally {
        setPatientsLoading(false);
      }
    }

    const today = new Date().toISOString().slice(0, 10);
    setExamDate(today);
    loadPatients();
  }, []);

  useEffect(() => {
    if (!fullImage) {
      setFullImageUrl(null);
      setDisplayCrop(null);
      return;
    }

    const url = URL.createObjectURL(fullImage);
    setFullImageUrl(url);
    setDisplayCrop(null);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [fullImage]);

  function resetModeSpecificState(nextMode: AnalysisMode) {
    setMode(nextMode);
    setError(null);

    if (nextMode === "ROI_DIRECT") {
      setFullImage(null);
      setFullImageUrl(null);
      setDisplayCrop(null);
    } else {
      setRoiImage(null);
    }
  }

  function handleOverlayMouseDown(e: MouseEvent<HTMLDivElement>) {
    if (mode !== "FULL_WITH_MANUAL_ROI") return;
    if (!fullImageUrl) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = clamp(e.clientX - rect.left, 0, rect.width);
    const y = clamp(e.clientY - rect.top, 0, rect.height);

    setDrawStart({ x, y });
    setDisplayCrop({ x, y, width: 0, height: 0 });
    setIsDrawing(true);
  }

  function handleOverlayMouseMove(e: MouseEvent<HTMLDivElement>) {
    if (!isDrawing || !drawStart) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const currentX = clamp(e.clientX - rect.left, 0, rect.width);
    const currentY = clamp(e.clientY - rect.top, 0, rect.height);

    const crop: CropBox = {
      x: Math.min(drawStart.x, currentX),
      y: Math.min(drawStart.y, currentY),
      width: Math.abs(currentX - drawStart.x),
      height: Math.abs(currentY - drawStart.y),
    };

    setDisplayCrop(crop);
  }

  function handleOverlayMouseUp() {
    setIsDrawing(false);
    setDrawStart(null);

    setDisplayCrop((prev) => {
      if (!prev) return null;
      if (prev.width < 5 || prev.height < 5) return null;
      return prev;
    });
  }

  function clearCrop() {
    setDisplayCrop(null);
    setDrawStart(null);
    setIsDrawing(false);
  }

  function getNaturalCrop(): CropBox | null {
    const img = imageRef.current;
    if (!img || !displayCrop) return null;

    const displayedWidth = img.clientWidth;
    const displayedHeight = img.clientHeight;
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;

    if (!displayedWidth || !displayedHeight || !naturalWidth || !naturalHeight) {
      return null;
    }

    const scaleX = naturalWidth / displayedWidth;
    const scaleY = naturalHeight / displayedHeight;

    const crop = {
      x: Math.round(displayCrop.x * scaleX),
      y: Math.round(displayCrop.y * scaleY),
      width: Math.round(displayCrop.width * scaleX),
      height: Math.round(displayCrop.height * scaleY),
    };

    if (crop.width <= 0 || crop.height <= 0) return null;

    return crop;
  }

  async function buildCroppedRoiBlob(): Promise<Blob> {
    const img = imageRef.current;
    const naturalCrop = getNaturalCrop();

    if (!img || !naturalCrop) {
      throw new Error("Please draw a valid ROI selection on the full radiograph.");
    }

    const canvas = document.createElement("canvas");
    canvas.width = naturalCrop.width;
    canvas.height = naturalCrop.height;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Unable to prepare cropped ROI.");
    }

    ctx.drawImage(
      img,
      naturalCrop.x,
      naturalCrop.y,
      naturalCrop.width,
      naturalCrop.height,
      0,
      0,
      naturalCrop.width,
      naturalCrop.height
    );

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((result) => resolve(result), "image/png");
    });

    if (!blob) {
      throw new Error("Failed to generate cropped ROI.");
    }

    return blob;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!patientId) {
        throw new Error("Please select a patient.");
      }

      if (!examDate) {
        throw new Error("Please select an exam date.");
      }

      const formData = new FormData();
      formData.append("patient_id", patientId);
      formData.append("exam_date", examDate);
      formData.append("mode", mode);

      if (mode === "ROI_DIRECT") {
        if (!roiImage) {
          throw new Error("Please upload an ROI image.");
        }

        formData.append("roi_image", roiImage);
      } else {
        if (!fullImage) {
          throw new Error("Please upload a full radiograph image.");
        }

        const naturalCrop = getNaturalCrop();
        if (!naturalCrop) {
          throw new Error("Please draw a valid ROI selection on the image.");
        }

        const croppedBlob = await buildCroppedRoiBlob();
        const croppedFile = new File([croppedBlob], "roi-cropped.png", {
          type: "image/png",
        });

        formData.append("full_image", fullImage);
        formData.append("roi_image", croppedFile);
        formData.append("roi_x", String(naturalCrop.x));
        formData.append("roi_y", String(naturalCrop.y));
        formData.append("roi_width", String(naturalCrop.width));
        formData.append("roi_height", String(naturalCrop.height));
      }

      const created = await apiFetch<AnalysisCreateResponse>("/analyses", {
        method: "POST",
        body: formData,
      });

      router.push(`/app/analyses/${created.analysis_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create analysis.");
    } finally {
      setLoading(false);
    }
  }

  const naturalCrop = getNaturalCrop();

  return (
    <main className="space-y-6">
      <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">New analysis</h1>
            <p className="mt-1 text-slate-600">
              Run assistive erosion inference from an ROI image or a manually cropped full radiograph.
            </p>
          </div>

          <Link
            href="/app"
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
          >
            Back to dashboard
          </Link>
        </div>

        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          This workflow is assistive only. Final interpretation remains the responsibility of the clinician.
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Patient
              </label>
              <select
                className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                disabled={patientsLoading}
              >
                {(patients?.items ?? []).map((patient) => (
                  <option key={patient.id} value={patient.patient_id}>
                    {patient.patient_id} — {patient.full_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Exam Date
              </label>
              <input
                type="date"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 p-5">
            <h2 className="text-lg font-semibold text-slate-900">Analysis mode</h2>
            <p className="mt-1 text-sm text-slate-600">
              Choose between a pre-extracted ROI or a full radiograph with manual ROI cropping.
            </p>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => resetModeSpecificState("ROI_DIRECT")}
                className={`rounded-2xl border p-4 text-left transition ${
                  mode === "ROI_DIRECT"
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <p className="font-semibold">ROI direct</p>
                <p className={`mt-1 text-sm ${mode === "ROI_DIRECT" ? "text-slate-200" : "text-slate-600"}`}>
                  Upload a wrist ROI image directly and run inference immediately.
                </p>
              </button>

              <button
                type="button"
                onClick={() => resetModeSpecificState("FULL_WITH_MANUAL_ROI")}
                className={`rounded-2xl border p-4 text-left transition ${
                  mode === "FULL_WITH_MANUAL_ROI"
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <p className="font-semibold">Full radiograph + manual crop</p>
                <p className={`mt-1 text-sm ${mode === "FULL_WITH_MANUAL_ROI" ? "text-slate-200" : "text-slate-600"}`}>
                  Upload a full radiograph, draw the ROI manually, then run inference on the cropped region.
                </p>
              </button>
            </div>
          </div>

          {mode === "ROI_DIRECT" && (
            <div className="rounded-2xl border border-slate-200 p-5 space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">ROI direct upload</h2>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  ROI image
                </label>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.bmp,image/png,image/jpeg,image/bmp"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                  onChange={(e) => setRoiImage(e.target.files?.[0] ?? null)}
                  required={mode === "ROI_DIRECT"}
                />
                <p className="mt-2 text-sm text-slate-500">
                  Accepted formats: PNG, JPG, JPEG, BMP.
                </p>
              </div>
            </div>
          )}

          {mode === "FULL_WITH_MANUAL_ROI" && (
            <div className="rounded-2xl border border-slate-200 p-5 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Full radiograph workflow
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  Upload a full image, then click-and-drag on the image to define the ROI.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Full radiograph image
                </label>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.bmp,image/png,image/jpeg,image/bmp"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
                  onChange={(e) => setFullImage(e.target.files?.[0] ?? null)}
                  required={mode === "FULL_WITH_MANUAL_ROI"}
                />
              </div>

              {fullImageUrl && (
                <div className="space-y-4">
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                    Draw the ROI directly on the image with the mouse. The selected region will be cropped automatically and sent for inference.
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 overflow-auto">
                    <div className="inline-block relative">
                      <img
                        ref={imageRef}
                        src={fullImageUrl}
                        alt="Full radiograph preview"
                        className="max-h-[650px] w-auto rounded-xl border border-slate-200 bg-white object-contain select-none"
                        draggable={false}
                      />

                      <div
                        className="absolute inset-0 cursor-crosshair"
                        onMouseDown={handleOverlayMouseDown}
                        onMouseMove={handleOverlayMouseMove}
                        onMouseUp={handleOverlayMouseUp}
                        onMouseLeave={handleOverlayMouseUp}
                      >
                        {displayCrop && (
                          <div
                            className="absolute border-2 border-sky-500 bg-sky-500/15"
                            style={{
                              left: displayCrop.x,
                              top: displayCrop.y,
                              width: displayCrop.width,
                              height: displayCrop.height,
                            }}
                          />
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={clearCrop}
                      className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
                    >
                      Clear ROI selection
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">ROI X</p>
                      <p className="mt-1 font-medium text-slate-900">
                        {naturalCrop ? naturalCrop.x : "N/A"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">ROI Y</p>
                      <p className="mt-1 font-medium text-slate-900">
                        {naturalCrop ? naturalCrop.y : "N/A"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">ROI Width</p>
                      <p className="mt-1 font-medium text-slate-900">
                        {naturalCrop ? naturalCrop.width : "N/A"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-500">ROI Height</p>
                      <p className="mt-1 font-medium text-slate-900">
                        {naturalCrop ? naturalCrop.height : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading || patientsLoading}
              className="rounded-xl bg-slate-900 text-white px-5 py-2.5 text-sm hover:bg-slate-800 disabled:opacity-60"
            >
              {loading
                ? "Running analysis..."
                : mode === "ROI_DIRECT"
                ? "Run ROI analysis"
                : "Crop ROI and run analysis"}
            </button>

            <Link
              href="/app"
              className="rounded-xl border border-slate-300 px-5 py-2.5 text-sm hover:bg-slate-100"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
}