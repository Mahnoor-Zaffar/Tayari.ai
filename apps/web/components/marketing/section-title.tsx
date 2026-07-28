import { cn } from "@/lib/utils";

interface SectionTitleProps {
  label?: string;
  title: string;
  description?: string;
  className?: string;
  align?: "center" | "left";
}

export function SectionTitle({
  label,
  title,
  description,
  className,
  align = "center",
}: SectionTitleProps) {
  return (
    <div
      className={cn("max-w-2xl space-y-4", align === "center" && "mx-auto text-center", className)}
    >
      {label && (
        <span className="inline-block rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-medium text-primary">
          {label}
        </span>
      )}
      <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">{title}</h2>
      {description && (
        <p className="text-lg leading-relaxed text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
