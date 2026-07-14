/**
 * Feature flag system for Tayari AI.
 *
 * Flags are controlled by `NEXT_PUBLIC_FF_*` environment variables.
 * Defaults can be overridden per environment via `.env.local`.
 *
 * Usage (server / static context):
 *   import { featureFlags } from "@/lib/feature-flags"
 *   if (featureFlags.interviews) { ... }
 *
 * Usage (client context):
 *   import { useFeatureFlag, FeatureFlag } from "@/lib/feature-flags"
 *   const show = useFeatureFlag("billing")
 *   <FeatureFlag name="reports"><ReportsPanel /></FeatureFlag>
 */

export interface FeatureFlagMap {
  interviews: boolean;
  reports: boolean;
  billing: boolean;
  settings: boolean;
  newInterview: boolean;
  analytics: boolean;
}

type FlagName = keyof FeatureFlagMap;

function env(name: string, fallback: boolean): boolean {
  if (typeof process === "undefined") return fallback;
  const val = process.env[`NEXT_PUBLIC_FF_${name.toUpperCase()}`];
  if (val === undefined) return fallback;
  return val === "1" || val === "true";
}

export const featureFlags: FeatureFlagMap = {
  interviews: env("interviews", false),
  reports: env("reports", false),
  billing: env("billing", false),
  settings: env("settings", false),
  newInterview: env("newInterview", true),
  analytics: env("analytics", true),
};

export function isEnabled(name: FlagName): boolean {
  return featureFlags[name];
}
