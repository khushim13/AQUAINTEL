"use client";

import React, { useState } from "react";
import { Layers, Search } from "lucide-react";

interface BlockItem {
  block: string;
  district: string;
  state: string;
  category?: string;
  stage_of_extraction_pct?: number;
  pre_monsoon_water_level_mbgl?: number;
  post_monsoon_water_level_mbgl?: number;
}

interface BlockTableProps {
  blocks: BlockItem[];
  location: string;
  year?: number | string;
}

export default function BlockTable({ blocks, location, year }: BlockTableProps) {
  const [filterText, setFilterText] = useState("");

  if (!blocks || blocks.length === 0) return null;

  const filtered = blocks.filter(
    (b) =>
      b.block.toLowerCase().includes(filterText.toLowerCase()) ||
      (b.category && b.category.toLowerCase().includes(filterText.toLowerCase()))
  );

  const getCategoryBadge = (category?: string) => {
    if (!category) return null;
    const cat = category.toLowerCase();
    if (cat.includes("safe")) {
      return (
        <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
          Safe
        </span>
      );
    }
    if (cat.includes("semi")) {
      return (
        <span className="inline-flex items-center rounded-full bg-yellow-50 px-2 py-0.5 text-[10px] font-semibold text-yellow-700 border border-yellow-200">
          Semi-Critical
        </span>
      );
    }
    if (cat.includes("critical")) {
      return (
        <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 border border-amber-200">
          Critical
        </span>
      );
    }
    if (cat.includes("over")) {
      return (
        <span className="inline-flex items-center rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700 border border-rose-200">
          Over-Exploited
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700">
        {category}
      </span>
    );
  };

  return (
    <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-100 text-slate-700">
            <Layers className="h-4 w-4" />
          </span>
          <div>
            <h4 className="text-sm font-semibold text-slate-800">
              Assessment Units ({blocks.length} Blocks)
            </h4>
            <p className="text-[11px] text-slate-500">{location} ({year})</p>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Search block or status..."
            className="rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 py-1 text-xs text-slate-800 placeholder-slate-400 focus:border-sky-500 focus:bg-white focus:outline-hidden"
          />
        </div>
      </div>

      <div className="max-h-60 overflow-y-auto rounded-lg border border-slate-100">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-50 text-slate-600 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th className="px-3 py-2">Block Name</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2 text-right">SOE (%)</th>
              <th className="px-3 py-2 text-right">Pre-Monsoon (mbgl)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((b, idx) => (
              <tr key={idx} className="hover:bg-slate-50/60">
                <td className="px-3 py-2 font-medium text-slate-800">{b.block}</td>
                <td className="px-3 py-2">{getCategoryBadge(b.category)}</td>
                <td className="px-3 py-2 text-right font-medium text-slate-700">
                  {b.stage_of_extraction_pct !== undefined && b.stage_of_extraction_pct !== null
                    ? `${b.stage_of_extraction_pct}%`
                    : "—"}
                </td>
                <td className="px-3 py-2 text-right text-slate-600">
                  {b.pre_monsoon_water_level_mbgl !== undefined && b.pre_monsoon_water_level_mbgl !== null
                    ? `${b.pre_monsoon_water_level_mbgl} mbgl`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
