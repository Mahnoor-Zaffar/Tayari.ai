import { type ReactNode } from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface AuthCardProps {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
}

export function AuthCard({ title, description, children, footer }: AuthCardProps) {
  return (
    <main className="flex min-h-svh items-center justify-center px-4 py-12">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1 text-center">
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>{children}</CardContent>
        {footer && <CardContent className="border-t pt-4">{footer}</CardContent>}
      </Card>
    </main>
  )
}
