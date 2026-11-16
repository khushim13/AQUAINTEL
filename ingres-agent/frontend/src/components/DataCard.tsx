"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  Database,
  ChevronDown,
  ChevronUp,
  MapPin,
  Calendar,
} from "lucide-react";
import ComparisonChart from "./ComparisonChart";
import TrendChart from "./TrendChart";
import BlockTable from "./BlockTable";

interface DataCardProps {
  toolCalled?: string | null;
  params?: Record<string, unknown> | null;
  data?: Record<string, unknown> | null;
}

export default function DataCard({ toolCalled, params, data }: DataCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!toolCalled && !data) return null;

  const isError = data && "error" in data;
  const isComparison = toolCalled === "compare_locations" && Array.isArray(data?.value);
  const isTrend = toolCalled === "get_trend" && Array.isArray(data?.value);
  const isBlockList = toolCalled === "list_blocks" && Array.isArray(data?.value);

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/70 text-slate-800 transition-all">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/80 bg-slate-100/70 px-3.5 py-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-md bg-emerald-100 text-emerald-700">
            <Database className="h-3.5 w-3.5" />
          </span>
          <span className="font-mono text-[11px] font-semibold text-slate-800">
            {toolCalled || "system_inquiry"}
          </span>
          {!isError && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="h-2.5 w-2.5" /> Verified INGRES
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900"
        >
          {isExpanded ? (
            <>
              Hide Technical Details <ChevronUp className="h-3 w-3" />
            </>
          ) : (
            <>
              Inspect DB Payload <ChevronDown className="h-3 w-3" />
            </>
          )}
        </button>
      </div>

      {/* Primary Key Summary Pills */}
      <div className="px-3.5 py-2.5 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {typeof data?.location === "string" && (
            <span className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1 text-slate-700 border border-slate-200 shadow-2xs font-medium">
              <MapPin className="h-3 w-3 text-sky-600" />
              {data.location}
            </span>
          )}
          {data?.year !== undefined && data?.year !== null && (
            <span className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1 text-slate-700 border border-slate-200 shadow-2xs font-medium">
              <Calendar className="h-3 w-3 text-indigo-600" />
              {String(data.year)}
            </span>
          )}
          {Boolean(data?.unit) && typeof data?.value !== "object" && (
            <span className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1 text-slate-700 border border-slate-200 shadow-2xs font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Raw Value: <strong className="text-slate-900">{String(data?.value)} {String(data?.unit)}</strong>
            </span>
          )}
        </div>

        {/* Embedded Dynamic Views */}
        {isComparison && (
          <ComparisonChart
            data={data.value as { location: string; value: number }[]}
            unit={String(data.unit || "")}
            metricName={typeof params?.metric === "string" ? params.metric : "Metric"}
          />
        )}

        {isTrend && (
          <TrendChart
            data={data.value as { year: number; value: number }[]}
            unit={String(data.unit || "")}
            location={typeof data.location === "string" ? data.location : ""}
            delta={typeof data.delta === "number" ? data.delta : undefined}
            direction={typeof data.direction === "string" ? data.direction : undefined}
          />
        )}

        {isBlockList && (
          <BlockTable
            blocks={data.value as { block: string; district: string; state: string; category?: string; stage_of_extraction_pct?: number; pre_monsoon_water_level_mbgl?: number; post_monsoon_water_level_mbgl?: number }[]}
            location={typeof data.location === "string" ? data.location : ""}
            year={data.year as number | string}
          />
        )}

        {/* Technical Raw Payload Collapse */}
        {isExpanded && (
          <div className="mt-3 space-y-2 border-t border-slate-200 pt-3 text-[11px]">
            {params && Object.keys(params).length > 0 && (
              <div>
                <p className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1">
                  Normalized Parameters
                </p>
                <pre className="overflow-x-auto rounded-lg bg-slate-900 p-2.5 text-slate-100 font-mono">
                  {JSON.stringify(params, null, 2)}
                </pre>
              </div>
            )}

            <div>
              <p className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1">
                Database Response Payload
              </p>
              <pre className="overflow-x-auto rounded-lg bg-slate-900 p-2.5 text-emerald-400 font-mono">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>

            <div className="pt-1 text-[10px] text-slate-400">
              Provenance: {typeof data?.source === "string" ? data.source : "Central Ground Water Board (CGWB) & IIT Hyderabad"}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
