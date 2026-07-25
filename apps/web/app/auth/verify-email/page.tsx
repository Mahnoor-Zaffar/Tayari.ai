import Link from "next/link";

import { AuthCard } from "@/features/auth/components/AuthCard";
import { VerifyEmailBanner } from "@/features/auth/components/VerifyEmailBanner";

export default function VerifyEmailPage() {
  return (
    <AuthCard
      title="Verify your email"
      description="Confirming your email address"
      footer={
        <p className="text-center text-sm text-muted-foreground">
          <Link href="/auth/login" className="underline underline-offset-4 hover:text-foreground">
            Back to sign in
          </Link>
        </p>
      }
    >
      <VerifyEmailBanner />
    </AuthCard>
  );
}
