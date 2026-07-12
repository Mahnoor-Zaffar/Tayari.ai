import type { Metadata } from "next"

import "./globals.css"
import { Providers } from "./providers"

export const metadata: Metadata = {
  title: "Tayari AI — Ace your next technical interview",
  description:
    "Practice with live AI voice interviews across coding, system design, and behavioral. Get scored evaluations and track your progress.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
