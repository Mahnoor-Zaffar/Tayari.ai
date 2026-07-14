"use client";

import { useMemo } from "react";
import { featureFlags, type FeatureFlagMap } from "@/lib/feature-flags";

type FlagName = keyof FeatureFlagMap;

export function useFeatureFlag(name: FlagName): boolean {
  return useMemo(() => featureFlags[name], [name]);
}

export function FeatureFlag({
  name,
  children,
  fallback,
}: {
  name: FlagName;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const enabled = useFeatureFlag(name);
  if (enabled) return <>{children}</>;
  if (fallback) return <>{fallback}</>;
  return null;
}
