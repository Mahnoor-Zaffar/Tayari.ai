"use client";

import { memo, useState } from "react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { User, Shield, Key, Palette, AlertTriangle } from "lucide-react";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { authApi } from "@/lib/api/auth";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/marketing/theme-toggle";

const profileSchema = z.object({
  display_name: z.string().min(1, "Display name is required").max(100),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

function Section({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <h3 className="text-sm font-medium">{title}</h3>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

export const SettingsPage = memo(function SettingsPage() {
  const { user, logout } = useAuth();
  const [saved, setSaved] = useState(false);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { display_name: user?.display_name ?? "" },
    values: { display_name: user?.display_name ?? "" },
  });

  const profileMutation = useMutation({
    mutationFn: (data: { display_name: string }) => authApi.updateProfile(data),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your account and preferences.</p>
      </div>

      <Section
        icon={User}
        title="Profile"
        description="Update your display name. Email changes are not supported."
      >
        <FormProvider {...form}>
          <form
            onSubmit={form.handleSubmit((data) => profileMutation.mutate(data))}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={user.email} disabled className="opacity-60" />
            </div>
            <FormField name="display_name" label="Display Name" placeholder={user.display_name} />
            {form.formState.errors.display_name && (
              <p className="text-sm text-destructive">
                {form.formState.errors.display_name.message}
              </p>
            )}
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={profileMutation.isPending}>
                {profileMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
              {saved && <span className="text-sm text-success">Saved!</span>}
            </div>
          </form>
        </FormProvider>
      </Section>

      <Section icon={Key} title="Password" description="Change your password via the reset flow.">
        <p className="text-sm text-muted-foreground">
          For security, password changes use an email-based reset link.{" "}
          <a href="/auth/forgot-password" className="text-primary hover:underline">
            Request a password reset
          </a>
          .
        </p>
      </Section>

      <Section icon={Palette} title="Appearance" description="Toggle between light and dark mode.">
        <div className="flex items-center justify-between rounded-lg border bg-muted/50 px-4 py-3">
          <div>
            <p className="text-sm font-medium">Theme</p>
            <p className="text-xs text-muted-foreground">Switch between light and dark mode</p>
          </div>
          <ThemeToggle />
        </div>
      </Section>

      <Section
        icon={AlertTriangle}
        title="Danger Zone"
        description="Permanently delete your account and all data."
      >
        <p className="mb-4 text-sm text-muted-foreground">
          This action cannot be undone. All your interviews, evaluations, and data will be
          permanently deleted.
        </p>
        <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10">
          Delete Account
        </Button>
      </Section>
    </div>
  );
});
