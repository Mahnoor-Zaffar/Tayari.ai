"use client";

import { useCallback, useRef, useState } from "react";
import { redirect } from "next/navigation";

import { Sidebar } from "@/components/layout/Sidebar";
import { Sheet } from "@/components/ui/sheet";
import { TopNav } from "@/components/layout/TopNav";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { ErrorBoundary } from "@/components/error/ErrorBoundary";
import { Skeleton } from "@/components/ui/skeleton";

function LoadingShell() {
  return (
    <div className="flex min-h-screen">
      <div className="hidden w-64 border-r bg-card p-4 lg:flex lg:flex-col lg:gap-4">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="flex-1 p-4">
        <Skeleton className="mb-4 h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);
  const openSidebar = useCallback(() => setSidebarOpen(true), []);

  if (isLoading) return <LoadingShell />;
  if (!isAuthenticated) redirect("/auth/login");

  return (
    <div className="flex min-h-screen bg-background">
      {/* Skip-to-content link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-ring"
      >
        Skip to main content
      </a>

      {/* Desktop sidebar */}
      <Sidebar className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64" />

      {/* Mobile sidebar drawer */}
      <Sheet open={sidebarOpen} onClose={closeSidebar} side="left" title="Navigation">
        <Sidebar className="flex-1 border-none" onNavClick={closeSidebar} />
      </Sheet>

      {/* Main area */}
      <div className="flex flex-1 flex-col lg:pl-64">
        <TopNav onMenuClick={openSidebar} />

        <main ref={mainRef} id="main-content" className="flex-1 p-4 md:p-6 lg:p-8" tabIndex={-1}>
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
