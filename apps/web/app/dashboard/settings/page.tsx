import type { Metadata } from "next";
import { SettingsPage } from "@/features/settings/components/SettingsPage";

export const metadata: Metadata = {
  title: "Settings — Tayari AI",
  description: "Manage your account settings and preferences.",
};

export default function SettingsRoute() {
  return <SettingsPage />;
}
