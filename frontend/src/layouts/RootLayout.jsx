import React from 'react';
import { Outlet } from 'react-router-dom';
import { ErrorBoundaryClass } from '../components/common/ErrorBoundary';
import { ToastProvider } from '../components/ui/toast';
import { ResumeProvider } from '../context/ResumeContext';

export function RootLayout() {
  return (
    <ToastProvider>
      <ResumeProvider>
        <ErrorBoundaryClass>
          <Outlet />
        </ErrorBoundaryClass>
      </ResumeProvider>
    </ToastProvider>
  );
}
