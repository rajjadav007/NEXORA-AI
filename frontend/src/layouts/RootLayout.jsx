import React from 'react';
import { Outlet } from 'react-router-dom';
import { ErrorBoundaryClass } from '../components/common/ErrorBoundary';
import { ToastProvider } from '../components/ui/toast';

export function RootLayout() {
  return (
    <ToastProvider>
      <ErrorBoundaryClass>
        <Outlet />
      </ErrorBoundaryClass>
    </ToastProvider>
  );
}
