"use client";

import { Check } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { GradientButton } from "./gradient-button";

interface PricingCardProps {
  name: string;
  price: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  className?: string;
  index?: number;
}

export function PricingCard({
  name,
  price,
  description,
  features,
  highlighted,
  className,
  index = 0,
}: PricingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className={cn(
        "relative rounded-2xl border p-8 transition-all duration-300",
        highlighted
          ? "border-primary/30 bg-gradient-to-b from-primary/5 to-transparent shadow-lg shadow-primary/5"
          : "border-white/5 bg-card",
        className,
      )}
    >
      {highlighted && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-medium text-primary-foreground">
          Most Popular
        </span>
      )}
      <h3 className="text-lg font-semibold">{name}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      <div className="mt-6 flex items-baseline gap-1">
        <span className="text-4xl font-bold">{price}</span>
        {price !== "Free" && <span className="text-sm text-muted-foreground">/month</span>}
      </div>
      <ul className="mt-6 space-y-3" role="list">
        {features.map((f) => (
          <li key={f} className="flex items-center gap-3 text-sm text-muted-foreground">
            <Check className="h-4 w-4 shrink-0 text-primary" />
            {f}
          </li>
        ))}
      </ul>
      <div className="mt-8">
        <GradientButton
          href="/auth/register"
          variant={highlighted ? "primary" : "outline"}
          className="w-full"
        >
          {price === "Free" ? "Get Started" : "Coming Soon"}
        </GradientButton>
      </div>
    </motion.div>
  );
}
