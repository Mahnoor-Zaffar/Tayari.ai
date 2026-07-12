import Link from "next/link"

import { AuthCard } from "@/features/auth/components/AuthCard"
import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm"

export default function ForgotPasswordPage() {
  return (
    <AuthCard
      title="Reset your password"
      description="Enter your email and we'll send you a reset link"
      footer={
        <p className="text-center text-sm text-muted-foreground">
          <Link href="/auth/login" className="underline underline-offset-4 hover:text-foreground">
            Back to sign in
          </Link>
        </p>
      }
    >
      <ForgotPasswordForm />
    </AuthCard>
  )
}
