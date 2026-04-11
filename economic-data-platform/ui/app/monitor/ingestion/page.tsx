"use client";

import { useCallback, useEffect, useState } from "react";
import { Database, Globe, TrendingUp, Server } from "lucide-react";
import { KPICard } from "@/components/kpi-card";
import { StatusBadge } from "@/components/status-badge";
import { RefreshButton } from "@/components/refresh-button";
import {
  ingestion,
  type SourceInfo,
  type SourceStatus,
  type IngestionOverview,
  type IngestionRecord,
} from "@/lib/api";

const domainIcon: Record<string, typeof Database> = {
  ecommerce: Server,
  business: Server,
  crypto: TrendingUp,
  economic: Globe,
  international: Globe,
};

export default function IngestionMonitorPage() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [overview, setOverview] = useState<IngestionOverview | null>(null);
  const [statuses, setStatuses] = useState<Record<string, SourceStatus>>({});
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [history, setHistory] = useState<IngestionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [src, ov] = await Promise.all([
        ingestion.listSources(),
        ingestion.getOverview(),
      ]);
      setSources(src);
      setOverview(ov);

      // Fetch status for each source in parallel
      const entries = await Promise.allSettled(
        src.map(async (s) => {
          const st = await ingestion.getStatus(s.source_id);
          return [s.source_id, st] as const;
        }),
      );
      const map: Record<string, SourceStatus> = {};
      for (const e of entries) {
        if (e.status === "fulfilled") {
          map[e.value[0]] = e.value[1];
        }
      }
      setStatuses(map);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load ingestion data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const selectSource = async (id: string) => {
    setSelectedSource(id);
    try {
      const data = await ingestion.getHistory(id, 30);
      setHistory(data);
    } catch {
      setHistory([]);
    }
  };

  const fmtNum = (n: number) => n.toLocaleString("en-US");
  const fmtDate = (d: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-white px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ingestion Monitor</h1>
            <p className="mt-1 text-sm text-gray-500">Data source health, row counts &amp; run history</p>
          </div>
          <RefreshButton onRefresh={fetchAll} autoInterval={60} />
        </div>
      </div>

      {error && (
        <div className="mx-8 mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* KPI cards */}
        {overview && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard title="Total Sources" value={overview.total_sources} icon={Database} />
            <KPICard
              title="Healthy"
              value={overview.healthy}
              subtitle={`of ${overview.total_sources}`}
              icon={TrendingUp}
            />
            <KPICard title="Degraded / Unknown" value={overview.degraded + overview.unknown} icon={Server} />
            <KPICard title="Total Rows Ingested" value={fmtNum(overview.total_rows_ingested)} icon={Globe} />
          </div>
        )}

        {/* Source cards grid */}
        <h2 className="text-sm font-semibold uppercase text-gray-500">Data Sources</h2>
        {loading ? (
          <p className="text-sm text-gray-400">Loading sources...</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sources.map((src) => {
              const st = statuses[src.source_id];
              const Icon = domainIcon[src.domain] ?? Database;
              return (
                <button
                  key={src.source_id}
                  onClick={() => selectSource(src.source_id)}
                  className={`rounded-xl border bg-white p-4 text-left transition hover:shadow-md ${
                    selectedSource === src.source_id ? "ring-2 ring-blue-400" : ""
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-lg bg-gray-100 p-2">
                        <Icon size={16} className="text-gray-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{src.name}</p>
                        <p className="text-xs text-gray-500">
                          {src.type} &middot; {src.domain}
                        </p>
                      </div>
                    </div>
                    <StatusBadge status={st?.status ?? "unknown"} />
                  </div>
                  <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                    <span>Schedule: {src.schedule}</span>
                    {st && <span>Rows: {fmtNum(st.total_rows)}</span>}
                  </div>
                  {st?.last_ingestion && (
                    <p className="mt-1 text-xs text-gray-400">
                      Last run: {fmtDate((st.last_ingestion as Record<string, string>).completed_at)}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* History table */}
        {selectedSource && (
          <div>
            <h2 className="mb-2 text-sm font-semibold text-gray-700">
              Ingestion History &mdash; <span className="font-mono">{selectedSource}</span>
            </h2>
            {history.length === 0 ? (
              <p className="text-sm text-gray-400">No history records found.</p>
            ) : (
              <div className="overflow-hidden rounded-lg border">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Table</th>
                      <th className="px-4 py-2">Date</th>
                      <th className="px-4 py-2 text-right">Rows</th>
                      <th className="px-4 py-2">Completed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {history.map((rec, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{rec.table}</td>
                        <td className="px-4 py-2">{rec.date}</td>
                        <td className="px-4 py-2 text-right font-mono">{fmtNum(rec.row_count)}</td>
                        <td className="px-4 py-2 text-gray-500">{fmtDate(rec.completed_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
