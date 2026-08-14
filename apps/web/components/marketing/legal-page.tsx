import Link from "next/link";

import { Navbar } from "@/components/marketing/navbar";
import { Footer } from "@/components/marketing/footer";

type LegalLayoutProps = {
  title: string;
  updated: string;
  children: React.ReactNode;
};

export function LegalLayout({ title, updated, children }: LegalLayoutProps) {
  return (
    <>
      <Navbar />
      <main className="relative z-10 min-h-screen pt-28">
        <div className="mx-auto max-w-3xl px-4 pb-24 sm:px-6 lg:px-8">
          <Link
            href="/"
            className="mb-8 inline-block text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            &larr; Back to home
          </Link>
          <header className="mb-12 border-b border-white/5 pb-8">
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
            <p className="mt-3 text-sm text-muted-foreground">Last updated: {updated}</p>
          </header>
          <div className="space-y-10">{children}</div>
        </div>
      </main>
      <Footer />
    </>
  );
}

export function LegalSection({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold tracking-tight">{heading}</h2>
      <div className="space-y-4 text-sm leading-relaxed text-muted-foreground">{children}</div>
    </section>
  );
}
