"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { cn } from "@/lib/utils";

interface DropdownMenuProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "start" | "end";
  className?: string;
}

export function DropdownMenu({ trigger, children, align = "end", className }: DropdownMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        close();
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);

      const firstFocusable = menuRef.current?.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      firstFocusable?.focus();
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open, close]);

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-haspopup="true"
        aria-expanded={open}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-md"
      >
        {trigger}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            ref={menuRef}
            role="menu"
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.1 }}
            className={cn(
              "absolute z-50 mt-1 min-w-[12rem] rounded-lg border bg-popover p-1 shadow-lg",
              align === "end" ? "right-0" : "left-0",
              className,
            )}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface DropdownItemProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "default" | "destructive";
  disabled?: boolean;
}

export function DropdownItem({
  children,
  onClick,
  variant = "default",
  disabled,
}: DropdownItemProps) {
  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
        variant === "destructive"
          ? "text-destructive hover:bg-destructive/10"
          : "text-popover-foreground hover:bg-accent",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      {children}
    </button>
  );
}

interface DropdownSeparatorProps {
  className?: string;
}

export function DropdownSeparator({ className }: DropdownSeparatorProps) {
  return <div role="separator" className={cn("my-1 h-px bg-border", className)} />;
}
