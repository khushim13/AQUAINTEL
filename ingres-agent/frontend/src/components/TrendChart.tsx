"use client";

import React, { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, TrendingDown, Minus, LineChart as ChartIcon, Table as TableIcon } from "lucide-react";

interface TrendPoint {
  year: number;
  value: number;
}

interface TrendChartProps {
  data: TrendPoint[];
  unit: string;
  location: string;
  delta?: number;
  direction?: string;
}

export default function TrendChart({ data, unit, location, delta, direction }: TrendChartProps) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  if (!data || data.length === 0) return null;

  return (
    <div className="mt-4 rounded-xl border border-indigo-100 bg-white p-4 shadow-xs">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-100 text-indigo-700">
            <ChartIcon className="h-4 w-4" />
          </span>
          <div>
            <h4 className="text-sm font-semibold text-slate-800">
              Historical Trend ({unit})
            </h4>
            <p className="text-[11px] text-slate-500">{location}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {delta !== undefined && delta !== null && (
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${
                direction === "increasing"
                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                  : direction === "decreasing"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : "bg-slate-50 text-slate-600 border border-slate-200"
              }`}
            >
              {direction === "increasing" && <TrendingUp className="h-3 w-3" />}
              {direction === "decreasing" && <TrendingDown className="h-3 w-3" />}
              {direction === "stable" && <Minus className="h-3 w-3" />}
              {delta > 0 ? `+${delta}` : delta} {unit}
            </span>
          )}

          <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setViewMode("chart")}
              className={`flex items-center gap-1 rounded-md px-2 py-1 font-medium transition-all ${
                viewMode === "chart"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <ChartIcon className="h-3 w-3" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`flex items-center gap-1 rounded-md px-2 py-1 font-medium transition-all ${
                viewMode === "table"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <TableIcon className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {viewMode === "chart" ? (
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const pt = payload[0].payload as TrendPoint;
                    return (
                      <div className="rounded-lg border border-slate-200 bg-white p-2 shadow-md text-xs">
                        <p className="font-semibold text-slate-700">Year {pt.year}</p>
                        <p className="mt-0.5 text-indigo-600 font-bold">
                          {pt.value} {unit}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#6366f1"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#trendGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase">
              <tr>
                <th className="px-3 py-2">Year</th>
                <th className="px-3 py-2 text-right">Value ({unit})</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="px-3 py-2 font-medium text-slate-700">{item.year}</td>
                  <td className="px-3 py-2 text-right font-semibold text-indigo-700">
                    {item.value} {unit}
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
