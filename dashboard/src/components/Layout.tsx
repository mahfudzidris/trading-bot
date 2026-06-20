'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Repeat2,
  BarChart3,
  Settings,
  Menu,
  X,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/trades', label: 'Trades', icon: Repeat2 },
  { href: '/analysis', label: 'Analysis', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#0f172a]">
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform border-r border-slate-800 bg-[#0f172a] transition-transform duration-200 lg:relative lg:translate-x-0',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-5">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600">
              <TrendingUp className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-bold text-slate-100">TradeBot</span>
          </Link>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="rounded-lg p-1 text-slate-500 hover:text-slate-300 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-4 space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
                {isActive && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-slate-800 p-4">
          <div className="rounded-lg bg-slate-800/50 p-3">
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Status
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs text-slate-300">API Connected</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Top bar (mobile) */}
        <header className="flex h-14 items-center justify-between border-b border-slate-800 bg-[#0f172a] px-4 lg:hidden">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="rounded-lg p-1.5 text-slate-400 hover:text-slate-200"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600">
              <TrendingUp className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold text-slate-100">TradeBot</span>
          </div>
          <div className="w-8" /> {/* spacer */}
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
