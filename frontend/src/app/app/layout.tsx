"use client";

import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { MeResponse } from "@/types/api";

function NavItem({
  href,
  label,
  active,
}: {
  href: string;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-2xl px-4 py-3 text-sm transition ${
        active
          ? "bg-slate-900 text-white shadow-sm"
          : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {label}
    </Link>
  );
}

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSession() {
      try {
        const result = await apiFetch<MeResponse>("/auth/me");
        setMe(result);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    loadSession();
  }, [router]);

  async function handleLogout() {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
    }
  }

  if (loading) {
    return <main className="p-8">Loading application...</main>;
  }

  if (!me) {
    return <main className="p-8">Redirecting...</main>;
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="flex min-h-screen">
        <aside className="hidden md:flex md:w-80 md:flex-col md:border-r md:border-slate-200 md:bg-white md:px-6 md:py-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">RheumaAssist</h1>
            <p className="mt-1 text-sm text-slate-500">
              Local-first AI-assisted rheumatology workflow
            </p>
          </div>

          <div className="mt-8">
            <p className="mb-3 text-xs uppercase tracking-wide text-slate-400">
              Navigation
            </p>

            <nav className="space-y-2">
              <NavItem
                href="/app"
                label="Dashboard"
                active={pathname === "/app"}
              />
              <NavItem
                href="/app/patients"
                label="Patients"
                active={pathname.startsWith("/app/patients")}
              />
              <NavItem
                href="/app/analyses/new"
                label="New analysis"
                active={pathname === "/app/analyses/new"}
              />
            </nav>
          </div>

          <div className="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-sm font-semibold text-slate-900">{me.full_name}</p>
            <p className="mt-1 text-xs text-slate-500">{me.email}</p>
            <p className="mt-3 text-xs text-slate-500">
              Roles: {me.roles.join(", ")}
            </p>
          </div>

          <div className="mt-6 rounded-3xl border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-semibold text-amber-900">
              Clinical reminder
            </p>
            <p className="mt-2 text-sm leading-6 text-amber-900">
              AI outputs are assistive only and must be reviewed by a licensed
              clinician before interpretation.
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="mt-6 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm hover:bg-slate-100"
          >
            Logout
          </button>
        </aside>

        <div className="flex-1 min-w-0">
          <header className="border-b border-slate-200 bg-white px-6 py-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">Connected clinician</p>
                <p className="font-medium text-slate-900">{me.full_name}</p>
              </div>

              <div className="md:hidden">
                <button
                  onClick={handleLogout}
                  className="rounded-2xl border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100"
                >
                  Logout
                </button>
              </div>
            </div>
          </header>

          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  );
}