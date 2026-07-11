import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Tayari AI — Ace your next technical interview",
  description:
    "Practice with live AI voice interviews across coding, system design, and behavioral. Get scored evaluations and track your progress.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
