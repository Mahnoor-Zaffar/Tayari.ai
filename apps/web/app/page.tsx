import Link from "next/link";
import { Mic, BarChart3, Target, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const features = [
  { icon: Mic, title: "AI Voice Interviews", desc: "Practice with realistic AI interviewers that adapt to your responses." },
  { icon: Target, title: "Multiple Formats", desc: "Coding, system design, and behavioral interviews tailored to your target role." },
  { icon: BarChart3, title: "Detailed Evaluations", desc: "Get scored feedback across communication, problem-solving, and technical depth." },
];

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">T</div>
          <span className="text-lg font-semibold">Tayari AI</span>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/auth/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
          <Link href="/auth/register"><Button size="sm">Get Started</Button></Link>
        </div>
      </header>

      <section className="flex flex-1 flex-col items-center justify-center px-6 py-20 text-center">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
          Ace your next<br /><span className="text-primary">technical interview</span>
        </h1>
        <p className="mt-4 max-w-lg text-lg text-muted-foreground">
          Practice with AI-powered mock interviews. Get personalized feedback and improve with every session.
        </p>
        <div className="mt-8 flex gap-3">
          <Link href="/auth/register"><Button size="lg">Start Practicing <ArrowRight className="h-4 w-4" /></Button></Link>
          <Link href="/auth/login"><Button variant="outline" size="lg">Sign In</Button></Link>
        </div>
      </section>

      <section className="border-t px-6 py-16">
        <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-3">
          {features.map((f) => (
            <div key={f.title} className="flex flex-col items-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10"><f.icon className="h-6 w-6 text-primary" /></div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t px-6 py-4 text-center text-sm text-muted-foreground">
        &copy; {new Date().getFullYear()} Tayari AI. All rights reserved.
      </footer>
    </div>
  );
}
