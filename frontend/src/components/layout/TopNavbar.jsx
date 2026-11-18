import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, Search, Bell, ChevronDown } from 'lucide-react';
import { navigationItems } from './Sidebar';

export function TopNavbar({ onOpenMobile, isCollapsed, onToggleCollapse }) {
  const location = useLocation();

  // Determine current route title
  const currentItem = navigationItems.find((item) =>
    location.pathname.startsWith(item.path)
  );
  const pageTitle = currentItem ? currentItem.name : 'Dashboard';

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/95 px-4 sm:px-6 backdrop-blur-sm">
      {/* Left: Mobile Toggle & Page Title / Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobile}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 md:hidden"
          aria-label="Open sidebar menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <nav aria-label="Breadcrumb" className="flex items-center gap-2">
          <span className="hidden sm:inline text-xs font-medium text-slate-400">
            Platform /
          </span>
          <h1 className="text-base sm:text-lg font-semibold text-slate-900 tracking-tight">
            {pageTitle}
          </h1>
        </nav>
      </div>

      {/* Center: Search UI Placeholder */}
      <div className="hidden sm:flex flex-1 max-w-md mx-6">
        <div className="relative w-full">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
            <Search className="h-4 w-4" />
          </div>
          <input
            type="text"
            readOnly
            placeholder="Search features, roadmaps, skills..."
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-9 pr-14 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer"
          />
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <kbd className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-500 shadow-2xs">
              Ctrl K
            </kbd>
          </div>
        </div>
      </div>

      {/* Right: Notifications & User Profile Menu Placeholders */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Notification Icon Placeholder */}
        <button
          type="button"
          aria-label="Notifications"
          className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-teal-600"></span>
          </span>
        </button>

        <div className="h-5 w-px bg-slate-200" aria-hidden="true" />

        {/* User Profile Menu Placeholder */}
        <div className="flex items-center gap-2 pl-1 cursor-pointer select-none">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white shadow-xs">
            NX
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-xs font-medium text-slate-900 leading-none">
              Career Explorer
            </span>
            <span className="text-[10px] text-slate-500">Explorer Tier</span>
          </div>
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
