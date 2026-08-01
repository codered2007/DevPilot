import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

function Button({
  variant = "primary",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-xl px-5 py-2.5 font-medium transition-all duration-200",
        {
          "bg-blue-600 text-white hover:bg-blue-700": variant === "primary",
          "bg-zinc-800 text-white hover:bg-zinc-700":
            variant === "secondary",
          "bg-transparent hover:bg-zinc-800 text-white":
            variant === "ghost",
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export default Button;