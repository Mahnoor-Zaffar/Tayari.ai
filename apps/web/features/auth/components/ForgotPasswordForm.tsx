"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { FormField } from "@/components/ui/form-field"
import { authApi } from "@/lib/api/auth"

const forgotSchema = z.object({
  email: z.string().email("Enter a valid email address"),
})

type ForgotFormValues = z.infer<typeof forgotSchema>

export function ForgotPasswordForm() {
  const [sent, setSent] = useState(false)

  const form = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  })

  const mutation = useMutation({
    mutationFn: (data: ForgotFormValues) => authApi.forgotPassword(data),
    onSuccess: () => setSent(true),
    onError: () => setSent(true),
  })

  return (
    <FormProvider {...form}>
      {sent ? (
        <p className="text-center text-sm text-muted-foreground">
          If an account with that email exists, we have sent a password reset link.
        </p>
      ) : (
        <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
          <FormField
            name="email"
            label="Email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
          />

          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </FormProvider>
  )
}
