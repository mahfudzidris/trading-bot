'use client';

import dynamic from 'next/dynamic';
import { cn } from '@/lib/utils';

const PnLAreaChart = dynamic(
  () => import('@/components/PnLAreaChart'),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

interface PnlChartProps {
  data: { date: string; pnl: number }[];
  height?: number;
}

function ChartSkeleton() {
  return (
    <div className="flex h-[300px] animate-pulse items-center justify-center rounded-xl bg-slate-800/50">
      <div className="h-4 w-32 rounded bg-slate-700/50" />
    </div>
  );
}

export default function PnLChart({ data, height = 300 }: PnlChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl bg-slate-800/50"
        style={{ height }}
      >
        <p className="text-sm text-slate-500">No chart data available</p>
      </div>
    );
  }
  return <PnLAreaChart data={data} height={height} />;
}
