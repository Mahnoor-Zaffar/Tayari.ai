import Link from "next/link"

import { AuthCard } from "@/features/auth/components/AuthCard"
import { RegisterForm } from "@/features/auth/components/RegisterForm"

export default function RegisterPage() {
  return (
    <AuthCard
      title="Create an account"
      description="Start practicing for your next interview"
      footer={
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/auth/login" className="underline underline-offset-4 hover:text-foreground">
            Sign in
          </Link>
        </p>
      }
    >
      <RegisterForm />
    </AuthCard>
  )
}
