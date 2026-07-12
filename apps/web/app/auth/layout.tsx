import { ErrorBoundary } from "@/components/error/ErrorBoundary"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
}
