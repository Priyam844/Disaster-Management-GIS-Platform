import { cn } from "@/lib/utils";

export interface ToastProps {
  title?: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
  action?: React.ReactNode;
}

const toastVariants = {
  default: "bg-background text-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  success: "bg-green-500 text-white",
};

export function Toast({ title, description, variant = "default", action }: ToastProps) {
  return (
    <div
      className={cn(
        "relative flex w-full items-center gap-2 rounded-lg border p-4 shadow-lg",
        toastVariants[variant]
      )}
    >
      <div className="flex-1">
        {title && <div className="font-semibold">{title}</div>}
        {description && <div className="text-sm opacity-90">{description}</div>}
      </div>
      {action}
    </div>
  );
}