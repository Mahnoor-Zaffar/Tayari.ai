"use client";

import { useRouter } from "next/navigation";
import { Menu } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { DropdownMenu, DropdownItem, DropdownSeparator } from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "@/components/marketing/theme-toggle";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { cn } from "@/lib/utils";

interface TopNavProps {
  title?: string;
  onMenuClick: () => void;
  className?: string;
}

export function TopNav({ title, onMenuClick, className }: TopNavProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60",
        className,
      )}
    >
      {/* Mobile menu button */}
      <button
        type="button"
        onClick={onMenuClick}
        className="rounded-md p-1.5 hover:bg-accent md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Title */}
      <div className="flex-1">
        <h1 className="text-lg font-semibold">{title ?? "Dashboard"}</h1>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <ThemeToggle />

        {/* Profile dropdown */}
        <DropdownMenu
          trigger={
            <Avatar fallback={user?.display_name ?? "U"} size="sm" className="cursor-pointer" />
          }
        >
          <div className="px-3 py-2">
            <p className="text-sm font-medium">{user?.display_name ?? "User"}</p>
            <p className="text-xs text-muted-foreground">{user?.email ?? ""}</p>
          </div>
          <DropdownSeparator />
          <DropdownItem onClick={() => router.push("/dashboard/settings")}>Settings</DropdownItem>
          <DropdownSeparator />
          <DropdownItem onClick={logout} variant="destructive">
            Sign out
          </DropdownItem>
        </DropdownMenu>
      </div>
    </header>
  );
}
