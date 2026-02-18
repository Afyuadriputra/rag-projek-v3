import { cn } from "@/lib/utils";

export default function ToggleSwitch({
  checked,
  onChange,
  label = "Toggle dark mode",
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      aria-pressed={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-6 w-[42px] cursor-pointer rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-800/60 focus-visible:ring-offset-2",
        checked ? "bg-black/80" : "bg-[#E5E5E5]"
      )}
    >
      <span
        className={cn(
          "absolute top-[2px] size-5 rounded-full bg-white shadow-sm transition-all",
          checked ? "left-[20px]" : "left-[2px]"
        )}
      />
    </button>
  );
}
