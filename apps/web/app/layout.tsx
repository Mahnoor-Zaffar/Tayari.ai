import type { Metadata } from "next";
import { Inter } from "next/font/google";

import "./globals.css";
import { Providers } from "./providers";
import { ThemeProvider } from "@/components/marketing/theme-toggle";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Tayari AI — Ace Your Next Technical Interview",
  description:
    "Practice with live AI voice interviews across coding, system design, and behavioral formats. Get scored evaluations, track your progress, and land your dream role.",
  icons: {
    icon: "/logo.png",
    apple: "/logo.png",
  },
  openGraph: {
    title: "Tayari AI — Ace Your Next Technical Interview",
    description:
      "Practice with live AI voice interviews across coding, system design, and behavioral formats.",
    type: "website",
    locale: "en_US",
    images: [{ url: "/logo.png" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Tayari AI — Ace Your Next Technical Interview",
    description:
      "Practice with live AI voice interviews. Get scored evaluations and track your progress.",
    images: ["/logo.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} dark`} suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
