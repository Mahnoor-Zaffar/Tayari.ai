import { type InputHTMLAttributes } from "react"
import { useFormContext } from "react-hook-form"

import { cn } from "@/lib/utils"

import { Input } from "./input"
import { Label } from "./label"

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  name: string
  label: string
  inlineLabel?: boolean
}

export function FormField({ name, label, inlineLabel = false, className, ...inputProps }: FormFieldProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext()

  const error = errors[name]
  const errorId = `${name}-error`

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={name} className={cn(inlineLabel && "sr-only")}>
        {label}
      </Label>
      <Input
        id={name}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        {...register(name)}
        {...inputProps}
      />
      {error && (
        <p id={errorId} className="text-sm text-destructive" role="alert">
          {error.message as string}
        </p>
      )}
    </div>
  )
}
