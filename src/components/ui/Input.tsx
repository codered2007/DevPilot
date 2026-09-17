import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type InputProps =
  InputHTMLAttributes<HTMLInputElement>;

function Input({
  className,
  ...props
}: InputProps) {
  return (
    <input
      className={cn(
        "w-full rounded-xl border border-zinc-700 bg-[#0B0D10] px-4 py-3 text-white outline-none transition focus:border-blue-500",
        className
      )}
      {...props}
    />
  );
}

export default Input;