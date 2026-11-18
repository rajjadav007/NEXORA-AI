import React from 'react';
import { Link } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  Building2,
  Target,
  TrendingUp,
  Compass,
  Award,
  Sparkles,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { SidebarItem } from './SidebarItem';
import { APP_NAME } from '../../config/constants';
import { cn } from '../../utils/cn';

export const navigationItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Resume Intelligence', path: '/resume', icon: FileText },
  { name: 'Job Discovery', path: '/jobs', icon: Briefcase },
  { name: 'Employer Intelligence', path: '/employer', icon: Building2 },
  { name: 'Job Matching', path: '/matching', icon: Target },
  { name: 'Skill Gap Analysis', path: '/skill-gap', icon: TrendingUp },
  { name: 'Career Roadmap', path: '/career', icon: Compass },
  { name: 'Skill Assessment', path: '/assessment', icon: Award },
  { name: 'AI Career Copilot', path: '/copilot', icon: Sparkles },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar({
  collapsed = false,
  onToggleCollapse,
  onCloseMobile,
  isMobile = false,
}) {
  return (
    <aside
      aria-label="Sidebar navigation"
      className={cn(
        'flex h-full flex-col border-r border-slate-200 bg-white transition-all duration-200',
        collapsed && !isMobile ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-100 px-4">
        <Link
          to="/dashboard"
          className={cn(
            'flex items-center gap-2.5 overflow-hidden',
            collapsed && !isMobile && 'justify-center w-full'
          )}
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          {(!collapsed || isMobile) && (
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-slate-900 leading-tight">
                {APP_NAME}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-teal-600">
                Career Shell
              </span>
            </div>
          )}
        </Link>

        {isMobile && (
          <button
            type="button"
            onClick={onCloseMobile}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {(!collapsed || isMobile) && (
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Navigation
          </p>
        )}
        {navigationItems.map((item) => (
          <SidebarItem
            key={item.path}
            to={item.path}
            name={item.name}
            icon={item.icon}
            collapsed={collapsed && !isMobile}
            onClick={isMobile ? onCloseMobile : undefined}
          />
        ))}
      </div>

      {/* Footer / Desktop Collapse Toggle */}
      {!isMobile && (
        <div className="shrink-0 border-t border-slate-100 p-3">
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={cn(
              'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors',
              collapsed && 'justify-center px-2'
            )}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Collapse sidebar</span>
              </>
            )}
          </button>
        </div>
      )}
    </aside>
  );
}
