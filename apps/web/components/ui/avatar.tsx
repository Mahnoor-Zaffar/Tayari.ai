"use client";

import { forwardRef, useMemo, type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = "md", ...props }, ref) => {
    const initials = useMemo(() => (fallback ? getInitials(fallback) : "?"), [fallback]);

    return (
      <div
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center overflow-hidden rounded-full bg-muted",
          sizeMap[size],
          className,
        )}
        {...props}
      >
        {src ? (
          <img src={src} alt={alt ?? fallback ?? ""} className="h-full w-full object-cover" />
        ) : (
          <span className="font-medium text-muted-foreground" aria-hidden="true">
            {initials}
          </span>
        )}
      </div>
    );
  },
);
Avatar.displayName = "Avatar";

export { Avatar };
