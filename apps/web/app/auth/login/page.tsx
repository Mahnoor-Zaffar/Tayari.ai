import Link from "next/link"

import { AuthCard } from "@/features/auth/components/AuthCard"
import { LoginForm } from "@/features/auth/components/LoginForm"

export default function LoginPage() {
  return (
    <AuthCard
      title="Sign in"
      description="Welcome back to Tayari AI"
      footer={
        <div className="flex flex-col gap-2 text-center text-sm text-muted-foreground">
          <Link href="/auth/register" className="underline underline-offset-4 hover:text-foreground">
            Don&apos;t have an account? Sign up
          </Link>
          <Link href="/auth/forgot-password" className="underline underline-offset-4 hover:text-foreground">
            Forgot your password?
          </Link>
        </div>
      }
    >
      <LoginForm />
    </AuthCard>
  )
}
