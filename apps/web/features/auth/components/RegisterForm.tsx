"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { useForm, FormProvider } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { FormField } from "@/components/ui/form-field"
import { authApi, type RegisterInput } from "@/lib/api/auth"
import { useAuth } from "@/features/auth/hooks/use-auth"

const registerSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  username: z
    .string()
    .min(3, "Username must be at least 3 characters")
    .max(50, "Username must be 50 characters or fewer")
    .regex(/^[a-zA-Z0-9_]+$/, "Only letters, numbers, and underscores"),
  display_name: z.string().min(1, "Display name is required").max(100, "Display name is too long"),
  password: z.string().min(8, "Password must be at least 8 characters"),
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterForm() {
  const { register } = useAuth()
  const router = useRouter()

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", username: "", display_name: "", password: "" },
  })

  const mutation = useMutation({
    mutationFn: (data: RegisterInput) => register(data),
    onSuccess: () => router.push("/"),
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : "Registration failed"
      form.setError("root", { message })
    },
  })

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        {form.formState.errors.root && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
            {form.formState.errors.root.message}
          </p>
        )}

        <FormField name="email" label="Email" type="email" placeholder="you@example.com" autoComplete="email" />
        <FormField
          name="username"
          label="Username"
          placeholder="your-username"
          autoComplete="username"
        />
        <FormField
          name="display_name"
          label="Display name"
          placeholder="Your name"
        />
        <FormField
          name="password"
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
        />

        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </FormProvider>
  )
}
