"use client";

import { memo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, BookOpen, Mic, Target } from "lucide-react";

import { SectionHeader } from "@/components/shared/SectionHeader";
import { ActionButton } from "@/components/shared/ActionButton";
import { cn } from "@/lib/utils";

interface QuickActionsProps {
  className?: string;
}

export const QuickActions = memo(function QuickActions({ className }: QuickActionsProps) {
  const router = useRouter();

  const actions = [
    { icon: Mic, label: "New Interview", onClick: useCallback(() => router.push("/dashboard/interview/new"), [router]) },
    { icon: BarChart3, label: "View Reports", onClick: useCallback(() => router.push("/dashboard/reports"), [router]) },
    { icon: BookOpen, label: "Practice", onClick: useCallback(() => {}, []) },
    { icon: Target, label: "Set Goal", onClick: useCallback(() => {}, []) },
  ];

  return (
    <section className={cn("space-y-3", className)}>
      <SectionHeader title="Quick Actions" />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {actions.map((action) => (
          <ActionButton
            key={action.label}
            icon={action.icon}
            label={action.label}
            onClick={action.onClick}
          />
        ))}
      </div>
    </section>
  );
});
