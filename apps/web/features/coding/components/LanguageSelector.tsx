"use client";

import { memo } from "react";
import { cn } from "@/lib/utils";

interface LanguageSelectorProps {
  value: string;
  onChange: (value: string) => void;
  languages: Array<{ id: string; name: string }>;
  disabled?: boolean;
  className?: string;
}

export const LanguageSelector = memo(function LanguageSelector({
  value,
  onChange,
  languages,
  disabled = false,
  className,
}: LanguageSelectorProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={cn(
        "rounded-md border border-input bg-background px-2.5 py-1.5 text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      aria-label="Programming language"
    >
      {languages.map((lang) => (
        <option key={lang.id} value={lang.id}>{lang.name}</option>
      ))}
    </select>
  );
});
