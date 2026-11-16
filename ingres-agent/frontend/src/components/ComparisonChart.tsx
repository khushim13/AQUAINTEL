"use client";

import React, { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { BarChart3, Table as TableIcon } from "lucide-react";

interface ComparisonItem {
  location: string;
  value: number;
}

interface ComparisonChartProps {
  data: ComparisonItem[];
  unit: string;
  metricName?: string;
}

const COLORS = ["#0284c7", "#0d9488", "#6366f1", "#f59e0b", "#ec4899", "#8b5cf6"];

export default function ComparisonChart({ data, unit, metricName = "Value" }: ComparisonChartProps) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  if (!data || data.length === 0) return null;

  // Clean location labels for compact axis display
  const chartData = data.map((d) => ({
    ...d,
    shortLocation: d.location.split(",")[0],
  }));

  return (
    <div className="mt-4 rounded-xl border border-sky-100 bg-white p-4 shadow-xs">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-sky-100 text-sky-700">
            <BarChart3 className="h-4 w-4" />
          </span>
          <h4 className="text-sm font-semibold text-slate-800">
            {metricName} Comparison ({unit})
          </h4>
        </div>
        <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-xs">
          <button
            type="button"
            onClick={() => setViewMode("chart")}
            className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all ${
              viewMode === "chart"
                ? "bg-white text-sky-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <BarChart3 className="h-3 w-3" /> Chart
          </button>
          <button
            type="button"
            onClick={() => setViewMode("table")}
            className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all ${
              viewMode === "table"
                ? "bg-white text-sky-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <TableIcon className="h-3 w-3" /> Table
          </button>
        </div>
      </div>

      {viewMode === "chart" ? (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="shortLocation"
                stroke="#64748b"
                fontSize={12}
                interval={0}
                tickLine={false}
              />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0].payload as ComparisonItem;
                    return (
                      <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-md text-xs">
                        <p className="font-semibold text-slate-900">{item.location}</p>
                        <p className="mt-1 text-sky-600 font-medium">
                          {item.value} {unit}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase">
              <tr>
                <th className="px-3 py-2">Location</th>
                <th className="px-3 py-2 text-right">Value ({unit})</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="px-3 py-2 font-medium text-slate-700">{item.location}</td>
                  <td className="px-3 py-2 text-right font-semibold text-sky-700">
                    {item.value.toLocaleString()} {unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
