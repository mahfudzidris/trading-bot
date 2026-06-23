'use client';

import { useState, useEffect } from 'react';
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
  FlaskConical,
  Brain,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/trades', label: 'Trades', icon: Repeat2 },
  { href: '/analysis', label: 'Analysis', icon: BarChart3 },
  { href: '/strategy', label: 'Strategy', icon: Brain },
  { href: '/backtest', label: 'Backtest', icon: FlaskConical },
  { href: '/settings', label: 'Settings', icon: Settings },
];

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(true); // default true for SSR safety
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1024);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);
  return isMobile;
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMobile = useIsMobile();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close sidebar when resizing to desktop
  useEffect(() => {
    if (!isMobile) setMobileMenuOpen(false);
  }, [isMobile]);

  const toggleMenu = () => setMobileMenuOpen(v => !v);
  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <div className="flex min-h-screen bg-[#0f172a]">
      {/* Mobile overlay */}
      {isMobile && mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60"
          onClick={closeMenu}
          onTouchEnd={(e) => { e.preventDefault(); closeMenu(); }}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          // Mobile: fixed overlay; Desktop: relative in-flow
          isMobile
            ? 'fixed inset-y-0 left-0 z-50 w-64 transform border-r border-slate-800 bg-[#0f172a] transition-transform duration-200'
            : 'relative w-64 border-r border-slate-800 bg-[#0f172a]',
          isMobile && (mobileMenuOpen ? 'translate-x-0' : '-translate-x-full')
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
          {isMobile && (
            <button
              onClick={closeMenu}
              onTouchEnd={(e) => { e.preventDefault(); closeMenu(); }}
              type="button"
              className="flex items-center justify-center rounded-lg p-3 text-slate-500 hover:text-slate-300 active:bg-slate-800/50"
              aria-label="Close menu"
            >
              <span className="pointer-events-none flex items-center justify-center">
                <X className="h-5 w-5" />
              </span>
            </button>
          )}
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
                onClick={closeMenu}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                )}
              >
                <item.icon className="pointer-events-none h-5 w-5" />
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
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar (mobile only) */}
        {isMobile && (
          <header className="flex h-14 items-center justify-between border-b border-slate-800 bg-[#0f172a] px-4">
            <button
              onClick={toggleMenu}
              onTouchEnd={(e) => { e.preventDefault(); toggleMenu(); }}
              type="button"
              className="flex items-center justify-center rounded-lg p-3 text-slate-400 hover:text-slate-200 active:bg-slate-800/50"
              aria-label="Open menu"
            >
              <span className="pointer-events-none flex items-center justify-center">
                <Menu className="h-5 w-5" />
              </span>
            </button>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600">
                <TrendingUp className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="text-sm font-bold text-slate-100">TradeBot</span>
            </div>
            <div className="w-11" /> {/* spacer */}
          </header>
        )}

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
