"use client";

import { memo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CreditCard,
  LayoutDashboard,
  Mic,
  Settings,
  type LucideIcon,
} from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/interviews", label: "Interviews", icon: Mic },
  { href: "/dashboard/reports", label: "Reports", icon: BarChart3 },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  className?: string;
  onNavClick?: () => void;
}

export const Sidebar = memo(function Sidebar({ className, onNavClick }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside
      className={cn("flex h-full flex-col border-r bg-background", className)}
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
          T
        </div>
        <span className="text-lg font-semibold">Tayari</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <Badge variant="secondary" className="ml-auto">
                  {item.badge}
                </Badge>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User info at bottom */}
      <Separator />
      <div className="flex items-center gap-3 px-5 py-4">
        <Avatar fallback={user?.display_name ?? "U"} size="sm" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{user?.display_name ?? "User"}</p>
          <p className="truncate text-xs text-muted-foreground">{user?.email ?? ""}</p>
        </div>
      </div>
    </aside>
  );
});
