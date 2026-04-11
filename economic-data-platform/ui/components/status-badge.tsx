import { cn } from "@/lib/utils";

const palette: Record<string, string> = {
  healthy: "bg-emerald-100 text-emerald-700",
  success: "bg-emerald-100 text-emerald-700",
  running: "bg-blue-100 text-blue-700",
  queued: "bg-amber-100 text-amber-700",
  degraded: "bg-amber-100 text-amber-700",
  failed: "bg-red-100 text-red-700",
  error: "bg-red-100 text-red-700",
  unknown: "bg-gray-100 text-gray-600",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const colors = palette[status.toLowerCase()] ?? palette.unknown;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        colors,
        className,
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", {
          "bg-emerald-500": status === "healthy" || status === "success",
          "bg-blue-500": status === "running",
          "bg-amber-500": status === "queued" || status === "degraded",
          "bg-red-500": status === "failed" || status === "error",
          "bg-gray-400": !palette[status.toLowerCase()],
        })}
      />
      {status}
    </span>
  );
}
