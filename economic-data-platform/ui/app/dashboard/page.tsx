"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ShoppingCart,
  DollarSign,
  Users,
  Truck,
  Star,
  Clock,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { KPICard } from "@/components/kpi-card";
import { RefreshButton } from "@/components/refresh-button";
import {
  dashboard,
  type KPIs,
  type RevenueTrendPoint,
  type TopProduct,
  type CustomerSegment,
  type DeliveryMetrics,
  type OrderStatusCount,
} from "@/lib/api";

const PIE_COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"];

const fmtCurrency = (n: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n);

const fmtNum = (n: number) => n.toLocaleString("en-US");

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [revenue, setRevenue] = useState<RevenueTrendPoint[]>([]);
  const [products, setProducts] = useState<TopProduct[]>([]);
  const [segments, setSegments] = useState<CustomerSegment[]>([]);
  const [delivery, setDelivery] = useState<DeliveryMetrics | null>(null);
  const [orderStatus, setOrderStatus] = useState<OrderStatusCount[]>([]);
  const [granularity, setGranularity] = useState<string>("monthly");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [k, r, p, s, d, os] = await Promise.all([
        dashboard.getKPIs(),
        dashboard.getRevenueTrends(granularity),
        dashboard.getTopProducts(10),
        dashboard.getCustomerSegments(),
        dashboard.getDeliveryPerformance(),
        dashboard.getOrderStatus(),
      ]);
      setKpis(k);
      setRevenue(r);
      setProducts(p);
      setSegments(s);
      setDelivery(d);
      setOrderStatus(os);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, [granularity]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-white px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">Olist E-Commerce KPIs, trends &amp; segmentation</p>
          </div>
          <RefreshButton onRefresh={fetchAll} />
        </div>
      </div>

      {error && (
        <div className="mx-8 mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        {loading ? (
          <p className="text-gray-400">Loading dashboard...</p>
        ) : (
          <>
            {/* KPI row */}
            {kpis && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
                <KPICard title="Total Orders" value={fmtNum(kpis.total_orders)} icon={ShoppingCart} />
                <KPICard title="Revenue" value={fmtCurrency(kpis.total_revenue)} icon={DollarSign} />
                <KPICard title="Customers" value={fmtNum(kpis.total_customers)} icon={Users} />
                <KPICard
                  title="Avg Order Value"
                  value={fmtCurrency(kpis.avg_order_value)}
                  icon={DollarSign}
                />
                <KPICard
                  title="Avg Delivery"
                  value={kpis.avg_delivery_days != null ? `${kpis.avg_delivery_days} days` : "—"}
                  icon={Truck}
                />
                <KPICard
                  title="Avg Review"
                  value={kpis.avg_review_score != null ? `${kpis.avg_review_score} / 5` : "—"}
                  icon={Star}
                />
              </div>
            )}

            {/* Revenue trend chart */}
            <div className="rounded-xl border bg-white p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-semibold text-gray-900">Revenue Trends</h2>
                <div className="flex gap-1 rounded-lg border p-0.5">
                  {["daily", "weekly", "monthly"].map((g) => (
                    <button
                      key={g}
                      onClick={() => setGranularity(g)}
                      className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                        granularity === g ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"
                      }`}
                    >
                      {g.charAt(0).toUpperCase() + g.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenue}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                  <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Top products */}
              <div className="rounded-xl border bg-white p-6">
                <h2 className="mb-4 text-base font-semibold text-gray-900">Top Product Categories</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={products} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis dataKey="product_category" type="category" tick={{ fontSize: 10 }} width={120} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="revenue" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Customer segments */}
              <div className="rounded-xl border bg-white p-6">
                <h2 className="mb-4 text-base font-semibold text-gray-900">Customer Segments (RFM)</h2>
                {segments.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={segments}
                        dataKey="customer_count"
                        nameKey="segment"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      >
                        {segments.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400">No segment data available</p>
                )}
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Delivery performance */}
              {delivery && (
                <div className="rounded-xl border bg-white p-6">
                  <h2 className="mb-4 text-base font-semibold text-gray-900">Delivery Performance</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-lg bg-emerald-50 p-4 text-center">
                      <p className="text-2xl font-bold text-emerald-700">{delivery.on_time_pct}%</p>
                      <p className="text-xs text-emerald-600">On Time</p>
                    </div>
                    <div className="rounded-lg bg-red-50 p-4 text-center">
                      <p className="text-2xl font-bold text-red-700">{delivery.late_pct}%</p>
                      <p className="text-xs text-red-600">Late</p>
                    </div>
                    <div className="rounded-lg bg-blue-50 p-4 text-center">
                      <p className="text-2xl font-bold text-blue-700">{delivery.avg_delivery_days}</p>
                      <p className="text-xs text-blue-600">Avg Days</p>
                    </div>
                    <div className="rounded-lg bg-amber-50 p-4 text-center">
                      <p className="text-2xl font-bold text-amber-700">
                        R$ {delivery.avg_freight_value.toFixed(2)}
                      </p>
                      <p className="text-xs text-amber-600">Avg Freight</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-gray-400 text-right">
                    {fmtNum(delivery.total_delivered)} delivered orders
                  </p>
                </div>
              )}

              {/* Order status */}
              <div className="rounded-xl border bg-white p-6">
                <h2 className="mb-4 text-base font-semibold text-gray-900">Order Status Distribution</h2>
                {orderStatus.length > 0 ? (
                  <div className="space-y-3">
                    {orderStatus.map((os) => (
                      <div key={os.status} className="flex items-center gap-3">
                        <span className="w-24 text-sm font-medium capitalize text-gray-700">{os.status}</span>
                        <div className="flex-1 rounded-full bg-gray-100 h-3">
                          <div
                            className="h-3 rounded-full bg-blue-500"
                            style={{ width: `${Math.min(os.pct, 100)}%` }}
                          />
                        </div>
                        <span className="w-20 text-right text-xs text-gray-500">
                          {fmtNum(os.count)} ({os.pct}%)
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No data</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
