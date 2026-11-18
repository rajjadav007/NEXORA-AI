import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../utils/cn';

export function SidebarItem({
  to,
  name,
  icon: Icon,
  collapsed = false,
  badge,
  onClick,
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      title={collapsed ? name : undefined}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
          isActive
            ? 'bg-teal-50 text-teal-700 font-semibold border-r-2 border-teal-600'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
          collapsed && 'justify-center px-2'
        )
      }
    >
      {Icon && (
        <Icon
          className="h-5 w-5 shrink-0 transition-colors"
          aria-hidden="true"
        />
      )}
      {!collapsed && <span className="truncate">{name}</span>}
      {!collapsed && badge && (
        <span className="ml-auto rounded-full bg-teal-100 px-2 py-0.5 text-xs font-semibold text-teal-800">
          {badge}
        </span>
      )}
    </NavLink>
  );
}
