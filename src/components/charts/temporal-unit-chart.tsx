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
  "#6366f1",
  "#a78bfa",
  "#22c55e",
  "#f59e0b",
  "#06b6d4",
  "#ec4899",
  "#8b5cf6",
  "#14b8a6",
  "#f97316",
  "#84cc16",
  "#e879f9",
  "#ef4444"
];

const UNCLASSIFIED_COLOR = "#71717a";
const MUTED_FG = "#a1a1aa";
const BORDER = "#27272a";

export interface TemporalChartRow {
  yearLabel: string;
  year: number;
  isSparse?: boolean;
  examCount?: number;
  totalQuestions: number;
  totalMarks: number;
  [qtype: string]: string | number | boolean | undefined;
}

interface Props {
  data: TemporalChartRow[];
  questionTypes: string[];
  metricMode: "questions" | "marks";
}

export function formatQuestionTypeName(raw: string): string {
  if (!raw) return "Unclassified";
  const lower = raw.toLowerCase().trim();
  if (lower === "unclassified" || lower === "other / unclassified") {
    return "Other / Unclassified";
  }
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

function getQuestionTypeColor(type: string, index: number): string {
  const lower = type.toLowerCase().trim();
  if (lower === "unclassified" || lower === "other / unclassified") {
    return UNCLASSIFIED_COLOR;
  }
  return PALETTE[index % PALETTE.length];
}

interface TooltipPayloadItem {
  color?: string;
  name?: string;
  value?: number;
  dataKey?: string | number;
  payload?: TemporalChartRow;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  metricMode: "questions" | "marks";
}

const CustomTooltip = ({ active, payload, metricMode }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const row = payload[0].payload;
    if (!row) return null;
    const isMarks = metricMode === "marks";

    return (
      <div className="rounded-lg border border-[#27272a] bg-[#18181b] p-3 shadow-md max-w-xs text-xs space-y-2 z-50">
        <div className="border-b border-border/50 pb-1.5 flex items-center justify-between gap-2">
          <span className="font-semibold text-zinc-100">Exam Year {row.year}</span>
          {row.isSparse && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Sparse Data
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
        <div className="space-y-1 pt-1">
          {payload.map((entry) => {
            const val = entry.value;
            if (val === undefined || val === null || val === 0) return null;
            const typeKey = String(entry.dataKey || "");
            const count = row[`${typeKey}_count`];
            const marks = row[`${typeKey}_marks`];

            return (
              <div key={typeKey} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-1.5 truncate max-w-[150px]">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-zinc-300 truncate">{entry.name}</span>
                </span>
                <span className="font-mono text-zinc-200 font-medium">
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

export function TemporalUnitChart({ data, questionTypes, metricMode }: Props) {
  if (!data || data.length === 0 || !questionTypes || questionTypes.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-xs text-muted-foreground">
        No temporal data available for this unit.
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
              />
            )}
            cursor={{ fill: "#27272a", opacity: 0.3 }}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px", paddingTop: "12px", color: MUTED_FG }}
            formatter={(value) => <span className="text-zinc-300 mr-2">{value}</span>}
          />
          {questionTypes.map((qtype, idx) => (
            <Bar
              key={qtype}
              dataKey={qtype}
              name={formatQuestionTypeName(qtype)}
              stackId="share"
              fill={getQuestionTypeColor(qtype, idx)}
              barSize={20}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
