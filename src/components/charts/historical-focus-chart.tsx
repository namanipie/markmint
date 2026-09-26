"use client";

import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const PALETTE = [
  "#6366f1", // Indigo
  "#8b5cf6", // Purple
  "#06b6d4", // Cyan
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#3b82f6", // Blue
  "#14b8a6", // Teal
  "#f97316", // Orange
  "#84cc16", // Lime
  "#a855f7", // Violet
  "#e11d48"  // Rose
];

const UNMAPPED_COLOR = "#71717a"; // Neutral zinc for unmapped
const MUTED_FG = "#a1a1aa";
const BORDER = "#27272a";

export interface FocusChartRow {
  yearLabel: string;
  year: number;
  isSparse?: boolean;
  examCount?: number;
  totalQuestions: number;
  totalMarks: number;
  [seriesKey: string]: string | number | boolean | undefined;
}

interface Props {
  data: FocusChartRow[];
  seriesKeys: string[];
  metricMode: "questions" | "marks";
  categoryName?: "Unit" | "Topic";
}

function getSeriesColor(seriesName: string, index: number): string {
  const lower = (seriesName || "").toLowerCase().trim();
  if (lower.includes("unmapped") || lower.includes("unknown") || lower.includes("unspecified")) {
    return UNMAPPED_COLOR;
  }
  return PALETTE[index % PALETTE.length];
}

interface TooltipPayloadItem {
  color?: string;
  name?: string;
  value?: number;
  dataKey?: string | number;
  payload?: FocusChartRow;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  metricMode: "questions" | "marks";
  categoryName?: string;
}

const CustomTooltip = ({ active, payload, metricMode, categoryName = "Item" }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const row = payload[0].payload;
    if (!row) return null;
    const isMarks = metricMode === "marks";

    return (
      <div className="rounded-lg border border-[#27272a] bg-[#18181b] p-3 shadow-md max-w-sm text-xs space-y-2 z-50">
        <div className="border-b border-border/50 pb-1.5 flex items-center justify-between gap-2">
          <span className="font-semibold text-zinc-100">Exam Year {row.year}</span>
          {row.isSparse && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Sparse Historical Data
            </span>
          )}
        </div>
        <div className="text-[11px] text-zinc-400">
          Evaluated: <span className="text-zinc-200 font-medium">{row.totalQuestions} Questions</span>
          {row.totalMarks > 0 && (
            <span> • <span className="text-zinc-200 font-medium">{row.totalMarks} Marks</span></span>
          )}
          {row.examCount !== undefined && row.examCount > 0 && (
            <span> ({row.examCount} {row.examCount === 1 ? "paper" : "papers"})</span>
          )}
        </div>
        <div className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider pt-0.5">
          Historical {categoryName} Distribution:
        </div>
        <div className="space-y-1.5 pt-1 max-h-56 overflow-y-auto pr-1">
          {payload.map((entry) => {
            const val = entry.value;
            if (val === undefined || val === null || val === 0) return null;
            const key = String(entry.dataKey || "");
            const count = row[`${key}_count`];
            const marks = row[`${key}_marks`];

            return (
              <div key={key} className="flex items-center justify-between gap-3 text-[11px]">
                <span className="flex items-center gap-1.5 truncate max-w-[190px]">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-zinc-300 truncate" title={entry.name}>
                    {entry.name}
                  </span>
                </span>
                <span className="font-mono text-zinc-200 font-medium shrink-0">
                  {val}%
                  <span className="text-zinc-500 ml-1 font-normal text-[10px]">
                    ({isMarks ? `${marks ?? 0}m` : `${count ?? 0} Qs`})
                  </span>
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

export function HistoricalFocusChart({
  data,
  seriesKeys,
  metricMode,
  categoryName = "Unit"
}: Props) {
  if (!data || data.length === 0 || !seriesKeys || seriesKeys.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-xs text-muted-foreground">
        No historical focus data recorded for this selection.
      </div>
    );
  }

  // Calculate dynamic chart height based on number of years
  const chartHeight = Math.max(220, data.length * 64);

  return (
    <div style={{ height: `${chartHeight}px` }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 12, right: 24, left: 10, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={BORDER} horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            unit="%"
            tick={{ fill: MUTED_FG, fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: BORDER }}
          />
          <YAxis
            dataKey="yearLabel"
            type="category"
            tick={{ fill: MUTED_FG, fontSize: 11, fontWeight: 500 }}
            tickLine={false}
            axisLine={{ stroke: BORDER }}
            width={70}
          />
          <Tooltip
            content={(props) => (
              <CustomTooltip
                active={props.active}
                payload={props.payload as unknown as TooltipPayloadItem[]}
                metricMode={metricMode}
                categoryName={categoryName}
              />
            )}
            cursor={{ fill: "#27272a", opacity: 0.3 }}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px", paddingTop: "12px", color: MUTED_FG }}
            formatter={(value) => (
              <span className="text-zinc-300 mr-2 max-w-[200px] inline-block truncate align-bottom" title={value}>
                {value}
              </span>
            )}
          />
          {seriesKeys.map((key, idx) => (
            <Bar
              key={key}
              dataKey={key}
              name={key}
              stackId="focusShare"
              fill={getSeriesColor(key, idx)}
              barSize={20}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
