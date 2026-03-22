"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { PatientCreateRequest, PatientResponse } from "@/types/api";

export default function NewPatientPage() {
  const router = useRouter();

  const [form, setForm] = useState<PatientCreateRequest>({
    patient_id: "",
    hospital_number: "",
    full_name: "",
    date_of_birth: "",
    sex: "female",
    notes: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof PatientCreateRequest>(
    key: K,
    value: PatientCreateRequest[K]
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const created = await apiFetch<PatientResponse>("/patients", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          notes: form.notes?.trim() ? form.notes : null,
        }),
      });

      router.push("/app/patients");
      console.log("Created patient:", created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create patient.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-3xl mx-auto rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">New patient</h1>
            <p className="mt-1 text-slate-600">
              Create a new patient record in the local registry.
            </p>
          </div>

          <Link
            href="/app/patients"
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
          >
            Back to patients
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Patient ID
            </label>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={form.patient_id}
              onChange={(e) => updateField("patient_id", e.target.value)}
              placeholder="P-0005"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Hospital Number
            </label>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={form.hospital_number}
              onChange={(e) => updateField("hospital_number", e.target.value)}
              placeholder="H-10005"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Full Name
            </label>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={form.full_name}
              onChange={(e) => updateField("full_name", e.target.value)}
              placeholder="Patient full name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Date of Birth
            </label>
            <input
              type="date"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={form.date_of_birth}
              onChange={(e) => updateField("date_of_birth", e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Sex
            </label>
            <select
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={form.sex}
              onChange={(e) =>
                updateField("sex", e.target.value as "female" | "male" | "other")
              }
            >
              <option value="female">female</option>
              <option value="male">male</option>
              <option value="other">other</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Notes
            </label>
            <textarea
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300 min-h-[120px]"
              value={form.notes ?? ""}
              onChange={(e) => updateField("notes", e.target.value)}
              placeholder="Optional notes"
            />
          </div>

          {error && (
            <div className="md:col-span-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="md:col-span-2 flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-slate-900 text-white px-5 py-2.5 text-sm hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Creating..." : "Create patient"}
            </button>

            <Link
              href="/app/patients"
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