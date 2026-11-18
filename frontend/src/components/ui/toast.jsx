import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const ToastContext = createContext(null);

const toastIcons = {
  success: { icon: CheckCircle2, color: 'text-green-600' },
  error: { icon: AlertCircle, color: 'text-red-600' },
  warning: { icon: AlertTriangle, color: 'text-amber-600' },
  info: { icon: Info, color: 'text-blue-600' },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(({ title, description, variant = 'info', duration = 4000 }) => {
    const id = Date.now().toString(36) + Math.random().toString(36).substring(2, 5);
    setToasts((prev) => [...prev, { id, title, description, variant }]);

    if (duration > 0) {
      setTimeout(() => {
        dismiss(id);
      }, duration);
    }
  }, [dismiss]);

  return (
    <ToastContext.Provider value={{ toast, dismiss }}>
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none p-4"
      >
        {toasts.map((t) => {
          const config = toastIcons[t.variant] || toastIcons.info;
          const Icon = config.icon;

          return (
            <div
              key={t.id}
              role="status"
              className={cn(
                'pointer-events-auto flex w-full items-start gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-lg transition-all',
                'animate-in fade-in slide-in-from-bottom-2'
              )}
            >
              <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', config.color)} aria-hidden="true" />
              <div className="flex-1 min-w-0">
                {t.title && <div className="text-sm font-semibold text-slate-900">{t.title}</div>}
                {t.description && (
                  <div className="mt-0.5 text-xs text-slate-600 leading-relaxed">{t.description}</div>
                )}
              </div>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                className="shrink-0 rounded-md p-1 text-slate-400 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label="Dismiss toast"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
