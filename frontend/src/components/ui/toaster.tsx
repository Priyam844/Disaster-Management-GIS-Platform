"use client";

import * as React from "react";
import { Toast, ToastProps } from "./toast";

interface ToastWithId extends ToastProps {
  id: string;
}

export function Toaster() {
  const [toasts, setToasts] = React.useState<ToastWithId[]>([]);

  React.useEffect(() => {
    // Listen for custom toast events
    const handleToast = (event: CustomEvent<ToastProps>) => {
      const id = Math.random().toString(36).substring(7);
      setToasts((prev) => [...prev, { ...event.detail, id }]);
    };

    window.addEventListener("toast", handleToast as EventListener);
    return () => window.removeEventListener("toast", handleToast as EventListener);
  }, []);

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 md:w-96">
      {toasts.map((toast) => (
        <div key={toast.id} className="animate-in slide-in-from-right">
          <Toast {...toast} />
        </div>
      ))}
    </div>
  );
}

export function useToast() {
  return React.useCallback((props: ToastProps) => {
    window.dispatchEvent(new CustomEvent("toast", { detail: props }));
  }, []);
}