import * as React from "react"
import { cn } from "@/lib/utils"

const Label = React.forwardRef(({ className, required, children, ...props }, ref) => (
  <label
    ref={ref}
    className={cn(
      "text-sm font-semibold leading-none text-foreground/90 select-none flex items-center gap-1 mb-1.5",
      className
    )}
    {...props}
  >
    {children}
    {required && <span className="text-red-500 text-xs">*</span>}
  </label>
))
Label.displayName = "Label"

export { Label }
