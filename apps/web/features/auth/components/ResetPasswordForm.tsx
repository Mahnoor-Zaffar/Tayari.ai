"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm, FormProvider } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { authApi } from "@/lib/api/auth";

const resetSchema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  });

type ResetFormValues = z.infer<typeof resetSchema>;

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const form = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: "", confirm: "" },
  });

  const mutation = useMutation({
    mutationFn: (data: { password: string }) =>
      authApi.resetPassword({ token: token!, new_password: data.password }),
    onSuccess: () => {
      setTimeout(() => router.push("/auth/login"), 2000);
    },
  });

  if (!token) {
    return (
      <p className="text-center text-sm text-destructive">
        Invalid or missing reset token. Please request a new password reset link.
      </p>
    );
  }

  if (mutation.isSuccess) {
    return (
      <p className="text-center text-sm text-muted-foreground">
        Password reset successful. Redirecting to sign in...
      </p>
    );
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <FormField
          name="password"
          label="New Password"
          type="password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
        />
        <FormField
          name="confirm"
          label="Confirm Password"
          type="password"
          placeholder="Re-enter your new password"
          autoComplete="new-password"
        />

        {mutation.isError && (
          <p className="text-sm text-destructive" role="alert">
            {(mutation.error as Error)?.message ??
              "Failed to reset password. The link may have expired."}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Resetting…" : "Reset Password"}
        </Button>
      </form>
    </FormProvider>
  );
}
