import React from 'react';
import { Link } from 'react-router-dom';
import { APP_NAME } from '../../config/constants';

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-6">
      <div className="mx-auto max-w-7xl px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500 sm:px-6 lg:px-8">
        <div>
          &copy; {new Date().getFullYear()} {APP_NAME}. All rights reserved.
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/design-system"
            className="text-xs text-slate-500 hover:text-teal-700 underline underline-offset-4 transition-colors"
          >
            UI Design System
          </Link>
        </div>
      </div>
    </footer>
  );
}
