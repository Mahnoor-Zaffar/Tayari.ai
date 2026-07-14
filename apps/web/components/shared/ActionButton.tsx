import { type LucideIcon } from "lucide-react";

import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ActionButtonProps extends ButtonProps {
  icon: LucideIcon;
  label: string;
}

export function ActionButton({ icon: Icon, label, className, ...props }: ActionButtonProps) {
  return (
    <Button
      variant="outline"
      className={cn("h-auto flex-col gap-1.5 py-4 text-center", className)}
      {...props}
    >
      <Icon className="h-5 w-5" />
      <span className="text-xs font-medium">{label}</span>
    </Button>
  );
}
