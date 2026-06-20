'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface PnLAreaChartProps {
  data: { date: string; pnl: number }[];
  height: number;
}

export default function PnLAreaChart({ data, height }: PnLAreaChartProps) {
  const totalPnl = data.reduce((sum, d) => sum + d.pnl, 0);
  const isPositive = totalPnl >= 0;
  const gradientId = isPositive ? 'gradient-profit' : 'gradient-loss';
  const strokeColor = isPositive ? '#22c55e' : '#ef4444';

  const chartData = data.map((d) => ({
    ...d,
    displayDate: new Date(d.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <div className="rounded-xl bg-slate-800/50 p-4">
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#334155"
              strokeOpacity={0.4}
            />
            <XAxis
              dataKey="displayDate"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${v}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
                fontSize: '13px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              formatter={(value: unknown) => [
                `$${Number(value).toFixed(2)}`,
                'PnL',
              ]}
            />
            <Area
              type="monotone"
              dataKey="pnl"
              stroke={strokeColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{
                r: 4,
                fill: strokeColor,
                stroke: '#1e293b',
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
