'use client';

import { useEffect, useRef, useState } from 'react';
import { TrendingUp, Target, BarChart3, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatCard {
  title: string;
  value: number;
  prefix?: string;
  suffix?: string;
  isCurrency?: boolean;
  isPercentage?: boolean;
  icon: React.ReactNode;
  trend?: 'up' | 'down';
}

function AnimatedNumber({ value, prefix, suffix, isCurrency, isPercentage }: Omit<StatCard, 'title' | 'icon' | 'trend'>) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const prevValue = useRef(value);

  useEffect(() => {
    // Skip animation on initial mount when value is 0
    const startVal = prevValue.current;
    const endVal = value;
    prevValue.current = value;

    // If value hasn't changed, skip
    if (startVal === endVal) return;

    const duration = 1500;
    const startTime = performance.now();

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(startVal + (endVal - startVal) * eased);
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }
    requestAnimationFrame(animate);
  }, [value]);

  const formatted = isCurrency
    ? `$${Math.abs(display).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : isPercentage
    ? `${display.toFixed(1)}%`
    : display.toLocaleString(undefined, { maximumFractionDigits: 0 });

  return (
    <span ref={ref}>
      {isCurrency && value < 0 && '- '}
      {prefix}{formatted}{suffix}
    </span>
  );
}

export default function SummaryCards({
  totalPnl,
  winRate,
  openPositions,
  dayPnl,
}: {
  totalPnl: number;
  winRate: number;
  openPositions: number;
  dayPnl: number;
}) {
  const cards: StatCard[] = [
    {
      title: 'Total PnL',
      value: totalPnl,
      isCurrency: true,
      icon: <DollarSign className="h-5 w-5" />,
      trend: totalPnl >= 0 ? 'up' : 'down',
    },
    {
      title: 'Win Rate',
      value: winRate,
      isPercentage: true,
      icon: <Target className="h-5 w-5" />,
      trend: winRate >= 50 ? 'up' : 'down',
    },
    {
      title: 'Open Positions',
      value: openPositions,
      icon: <BarChart3 className="h-5 w-5" />,
    },
    {
      title: "Today's PnL",
      value: dayPnl,
      isCurrency: true,
      icon: <TrendingUp className="h-5 w-5" />,
      trend: dayPnl >= 0 ? 'up' : 'down',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className={cn(
            'group relative overflow-hidden rounded-xl border p-4 transition-all duration-300 hover:border-slate-600',
            card.trend === 'up' && 'border-green-500/20 bg-gradient-to-br from-slate-800 to-slate-800/80',
            card.trend === 'down' && 'border-red-500/20 bg-gradient-to-br from-slate-800 to-slate-800/80',
            !card.trend && 'border-slate-700/50 bg-slate-800/50'
          )}
        >
          {/* Glow effect */}
          <div
            className={cn(
              'absolute -right-6 -top-6 h-16 w-16 rounded-full opacity-10 blur-xl transition-all duration-500 group-hover:opacity-20',
              card.trend === 'up' && 'bg-green-500',
              card.trend === 'down' && 'bg-red-500',
              !card.trend && 'bg-blue-500'
            )}
          />
          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                {card.title}
              </span>
              <span
                className={cn(
                  'rounded-lg p-1.5',
                  card.trend === 'up' && 'bg-green-500/10 text-green-400',
                  card.trend === 'down' && 'bg-red-500/10 text-red-400',
                  !card.trend && 'bg-blue-500/10 text-blue-400'
                )}
              >
                {card.icon}
              </span>
            </div>
            <div
              className={cn(
                'mt-2 text-2xl font-bold tracking-tight',
                card.trend === 'up' && 'text-green-400',
                card.trend === 'down' && 'text-red-400',
                !card.trend && 'text-slate-100'
              )}
            >
              <AnimatedNumber
                value={card.value}
                prefix={card.prefix}
                suffix={card.suffix}
                isCurrency={card.isCurrency}
                isPercentage={card.isPercentage}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
