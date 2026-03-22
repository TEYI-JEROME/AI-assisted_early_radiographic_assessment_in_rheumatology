"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { PatientListResponse } from "@/types/api";

export default function PatientsPage() {
  const [data, setData] = useState<PatientListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    async function loadPatients() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (query.trim()) {
          params.set("q", query.trim());
        }
        params.set("page", String(page));
        params.set("page_size", String(pageSize));

        const result = await apiFetch<PatientListResponse>(`/patients?${params.toString()}`);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load patients.");
      } finally {
        setLoading(false);
      }
    }

    loadPatients();
  }, [query, page, pageSize]);

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setQuery(searchInput);
  }

  function clearSearch() {
    setSearchInput("");
    setQuery("");
    setPage(1);
  }

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Patients</h1>
            <p className="text-slate-600 mt-1">
              Local patient registry for RheumaAssist.
            </p>
          </div>

          <div className="flex gap-3">
            <Link
              href="/app/patients/new"
              className="rounded-xl bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800"
            >
              New patient
            </Link>

            <Link
              href="/app"
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
            >
              Back to dashboard
            </Link>
          </div>
        </div>

        <form
          onSubmit={handleSearchSubmit}
          className="mt-6 flex flex-col md:flex-row gap-3 md:items-end"
        >
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Search patients
            </label>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by patient ID, hospital number, or full name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Page size
            </label>
            <select
              className="rounded-xl border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
              value={pageSize}
              onChange={(e) => {
                setPage(1);
                setPageSize(Number(e.target.value));
              }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>

          <button
            type="submit"
            className="rounded-xl bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800"
          >
            Search
          </button>

          <button
            type="button"
            onClick={clearSearch}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
          >
            Clear
          </button>
        </form>

        {query && (
          <p className="mt-3 text-sm text-slate-500">
            Active search: <span className="font-medium">{query}</span>
          </p>
        )}

        {loading && <p className="mt-6 text-slate-600">Loading patients...</p>}

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="mt-6 overflow-x-auto">
              <table className="min-w-full border border-slate-200 rounded-xl overflow-hidden">
                <thead className="bg-slate-100 text-left">
                  <tr>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      Patient ID
                    </th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      Hospital Number
                    </th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      Full Name
                    </th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      DOB
                    </th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      Sex
                    </th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.items ?? []).length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-6 text-sm text-slate-500 text-center"
                      >
                        No patients found.
                      </td>
                    </tr>
                  ) : (
                    data?.items.map((patient) => (
                      <tr key={patient.id} className="border-t border-slate-200">
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {patient.patient_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {patient.hospital_number}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {patient.full_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {patient.date_of_birth}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-800">
                          {patient.sex}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <Link
                            href={`/app/patients/${patient.patient_id}`}
                            className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <p className="text-sm text-slate-500">
                Showing page {page} of {totalPages} · Total patients: {total}
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
                >
                  Previous
                </button>

                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}