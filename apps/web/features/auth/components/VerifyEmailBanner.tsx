"use client";

import { useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";

type Status = "verifying" | "success" | "error";

export function VerifyEmailBanner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<Status>("verifying");

  const mutation = useMutation({
    mutationFn: () => authApi.verifyEmail({ token: token! }),
    onSuccess: () => setStatus("success"),
    onError: () => setStatus("error"),
  });

  useEffect(() => {
    if (token && status === "verifying") {
      mutation.mutate();
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!token) {
    return (
      <p className="text-center text-sm text-destructive">
        Invalid or missing verification token. Please check the link in your email.
      </p>
    );
  }

  if (status === "verifying") {
    return (
      <p className="text-center text-sm text-muted-foreground">Verifying your email address...</p>
    );
  }

  if (status === "success") {
    return (
      <p className="text-center text-sm text-green-600">
        Email verified successfully! You can close this window.
      </p>
    );
  }

  return (
    <p className="text-center text-sm text-destructive">
      This verification link has expired or is invalid. Please try signing up again.
    </p>
  );
}
