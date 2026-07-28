"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm, FormProvider } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Separator } from "@/components/ui/separator";
import { authApi, type LoginInput } from "@/lib/api/auth";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { signInWithProvider } from "@/lib/supabase";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (data: LoginInput) => login(data),
    onSuccess: () => router.push("/dashboard"),
    onError: () => form.setError("root", { message: "Invalid email or password" }),
  });

  const [socialError, setSocialError] = useState<string | null>(null);
  const [socialLoading, setSocialLoading] = useState<string | null>(null);

  const handleSocialLogin = async (provider: "google" | "github") => {
    try {
      setSocialError(null);
      setSocialLoading(provider);
      await signInWithProvider(provider);
    } catch (err) {
      setSocialError(err instanceof Error ? err.message : "Social login failed");
    } finally {
      setSocialLoading(null);
    }
  };

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        {form.formState.errors.root && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
            {form.formState.errors.root.message}
          </p>
        )}

        <FormField
          name="email"
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
        />
        <FormField
          name="password"
          label="Password"
          type="password"
          placeholder="Enter your password"
          autoComplete="current-password"
        />

        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Signing in…" : "Sign in"}
        </Button>

        <div className="relative my-4">
          <Separator />
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
            or continue with
          </span>
        </div>

        {socialError && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
            {socialError}
          </p>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="outline"
            disabled={socialLoading === "google"}
            onClick={() => handleSocialLogin("google")}
          >
            {socialLoading === "google" ? "Loading…" : "Google"}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={socialLoading === "github"}
            onClick={() => handleSocialLogin("github")}
          >
            {socialLoading === "github" ? "Loading…" : "GitHub"}
          </Button>
        </div>
      </form>
    </FormProvider>
  );
}
