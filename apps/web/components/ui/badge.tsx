import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "secondary" | "outline" | "success" | "warning" | "destructive";

interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  outline: "border text-foreground",
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100",
  destructive: "bg-destructive text-destructive-foreground",
};

export function Badge({ variant = "default", className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
