import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '../components/common/Header';
import { Footer } from '../components/common/Footer';
import { ErrorBoundaryClass } from '../components/common/ErrorBoundary';

export function RootLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900">
      <Header />
      <main className="flex-1">
        <ErrorBoundaryClass>
          <Outlet />
        </ErrorBoundaryClass>
      </main>
      <Footer />
    </div>
  );
}
