type NoticeTone = "info" | "success" | "warning" | "error";

const toneClasses: Record<NoticeTone, string> = {
  info: "border-sky-200 bg-sky-50 text-sky-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  error: "border-rose-200 bg-rose-50 text-rose-900",
};

export function Notice({
  tone = "info",
  title,
  children,
}: {
  tone?: NoticeTone;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`rounded-2xl border px-4 py-4 ${toneClasses[tone]}`}>
      {title && <p className="text-sm font-semibold">{title}</p>}
      <div className={title ? "mt-1 text-sm" : "text-sm"}>{children}</div>
    </div>
  );
}