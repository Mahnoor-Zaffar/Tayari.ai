import { Navbar } from "@/components/marketing/navbar";
import { Footer } from "@/components/marketing/footer";
import { AnimatedBackground } from "@/components/marketing/animated-background";
import { Hero } from "@/sections/hero";
import { TrustedBy } from "@/sections/trusted-by";
import { Features } from "@/sections/features";
import { HowItWorks } from "@/sections/how-it-works";
import { Showcase } from "@/sections/showcase";
import { InterviewExperience } from "@/sections/interview-experience";
import { Reports } from "@/sections/reports";
import { Testimonials } from "@/sections/testimonials";
import { Pricing } from "@/sections/pricing";
import { FAQ } from "@/sections/faq";
import { CTA } from "@/sections/cta";

export default function LandingPage() {
  return (
    <>
      <AnimatedBackground />
      <Navbar />
      <main className="relative z-10">
        <Hero />
        <TrustedBy />
        <Features />
        <HowItWorks />
        <Showcase />
        <InterviewExperience />
        <Reports />
        <Testimonials />
        <Pricing />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
