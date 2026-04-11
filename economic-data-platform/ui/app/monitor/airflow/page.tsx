"use client";

import { useCallback, useEffect, useState } from "react";
import { Play, Pause, RotateCcw, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/status-badge";
import { RefreshButton } from "@/components/refresh-button";
import { monitor, type DAGSummary, type DAGRunSummary, type TaskInstanceSummary } from "@/lib/api";

export default function AirflowMonitorPage() {
  const [dags, setDags] = useState<DAGSummary[]>([]);
  const [selectedDag, setSelectedDag] = useState<string | null>(null);
  const [runs, setRuns] = useState<DAGRunSummary[]>([]);
  const [tasks, setTasks] = useState<TaskInstanceSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDags = useCallback(async () => {
    try {
      setError(null);
      const data = await monitor.listDags();
      setDags(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load DAGs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDags();
  }, [fetchDags]);

  const selectDag = async (dagId: string) => {
    setSelectedDag(dagId);
    setSelectedRun(null);
    setTasks([]);
    try {
      const data = await monitor.getDagRuns(dagId);
      setRuns(data);
    } catch {
      setRuns([]);
    }
  };

  const selectRun = async (dagId: string, runId: string) => {
    setSelectedRun(runId);
    try {
      const data = await monitor.getTaskInstances(dagId, runId);
      setTasks(data);
    } catch {
      setTasks([]);
    }
  };

  const handleTrigger = async (dagId: string) => {
    try {
      await monitor.triggerDag(dagId);
      if (selectedDag === dagId) {
        const data = await monitor.getDagRuns(dagId);
        setRuns(data);
      }
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Trigger failed");
    }
  };

  const handleTogglePause = async (dag: DAGSummary) => {
    try {
      await monitor.togglePause(dag.dag_id, !dag.is_paused);
      await fetchDags();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Toggle failed");
    }
  };

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
            <h1 className="text-2xl font-bold text-gray-900">Airflow Monitor</h1>
            <p className="mt-1 text-sm text-gray-500">DAG status, run history &amp; task instances</p>
          </div>
          <RefreshButton onRefresh={fetchDags} autoInterval={30} />
        </div>
      </div>

      {error && (
        <div className="mx-8 mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* DAG list */}
        <div className="w-80 shrink-0 overflow-y-auto border-r bg-gray-50 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase text-gray-500">
            DAGs ({dags.length})
          </h2>
          {loading ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : dags.length === 0 ? (
            <p className="text-sm text-gray-400">No DAGs found. Is Airflow running?</p>
          ) : (
            <div className="space-y-1">
              {dags.map((dag) => (
                <button
                  key={dag.dag_id}
                  onClick={() => selectDag(dag.dag_id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                    selectedDag === dag.dag_id
                      ? "bg-white font-medium shadow-sm"
                      : "hover:bg-white/70"
                  }`}
                >
                  <span
                    className={`h-2 w-2 shrink-0 rounded-full ${dag.is_paused ? "bg-amber-400" : "bg-emerald-400"}`}
                  />
                  <span className="flex-1 truncate">{dag.dag_id}</span>
                  <ChevronRight size={14} className="text-gray-400" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedDag ? (
            <div className="flex h-full items-center justify-center text-gray-400">
              Select a DAG to view runs
            </div>
          ) : (
            <>
              {/* DAG actions */}
              {(() => {
                const dag = dags.find((d) => d.dag_id === selectedDag);
                if (!dag) return null;
                return (
                  <div className="mb-6 flex items-center gap-3">
                    <h2 className="text-lg font-bold text-gray-900">{dag.dag_id}</h2>
                    <StatusBadge status={dag.is_paused ? "paused" : "active"} />
                    <div className="flex-1" />
                    <Button size="sm" variant="outline" onClick={() => handleTogglePause(dag)}>
                      {dag.is_paused ? <Play size={14} className="mr-1" /> : <Pause size={14} className="mr-1" />}
                      {dag.is_paused ? "Unpause" : "Pause"}
                    </Button>
                    <Button size="sm" onClick={() => handleTrigger(dag.dag_id)}>
                      <RotateCcw size={14} className="mr-1" /> Trigger
                    </Button>
                  </div>
                );
              })()}

              {/* DAG Runs table */}
              <h3 className="mb-2 text-sm font-semibold text-gray-700">Recent Runs</h3>
              <div className="overflow-hidden rounded-lg border">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Run ID</th>
                      <th className="px-4 py-2">State</th>
                      <th className="px-4 py-2">Start</th>
                      <th className="px-4 py-2">End</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {runs.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-6 text-center text-gray-400">
                          No runs yet
                        </td>
                      </tr>
                    ) : (
                      runs.map((r) => (
                        <tr
                          key={r.dag_run_id}
                          className={`cursor-pointer transition hover:bg-gray-50 ${selectedRun === r.dag_run_id ? "bg-blue-50" : ""}`}
                          onClick={() => selectRun(r.dag_id, r.dag_run_id)}
                        >
                          <td className="px-4 py-2 font-mono text-xs">{r.dag_run_id}</td>
                          <td className="px-4 py-2">
                            <StatusBadge status={r.state} />
                          </td>
                          <td className="px-4 py-2 text-gray-600">{fmtDate(r.start_date)}</td>
                          <td className="px-4 py-2 text-gray-600">{fmtDate(r.end_date)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Task instances */}
              {selectedRun && tasks.length > 0 && (
                <div className="mt-6">
                  <h3 className="mb-2 text-sm font-semibold text-gray-700">
                    Tasks for <span className="font-mono">{selectedRun}</span>
                  </h3>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {tasks.map((t) => (
                      <div key={t.task_id} className="rounded-lg border bg-white p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{t.task_id}</span>
                          <StatusBadge status={t.state ?? "unknown"} />
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          {t.operator && <span className="mr-3">{t.operator}</span>}
                          {t.duration != null && <span>{t.duration.toFixed(1)}s</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
