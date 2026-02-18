import { cn } from "@/lib/utils";

export default function Toast({
  open,
  kind,
  message,
  onClose,
}: {
  open: boolean;
  kind: "success" | "error";
  message: string;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div data-testid="toast" className="fixed right-6 top-20 z-[999]">
      <div
        className={cn(
          "glass-card min-w-[280px] max-w-[420px] rounded-2xl border px-4 py-3 shadow-sm",
          "dark:border-zinc-700/70"
        )}
      >
        <div className="flex items-start gap-3">
          <span className={cn("material-symbols-outlined text-[20px]", kind === "success" ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400")}>
            {kind === "success" ? "check_circle" : "error"}
          </span>
          <div className="flex-1">
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
              {kind === "success" ? "Success" : "Error"}
            </div>
            <div data-testid="toast-message" className="text-[13px] text-zinc-700 dark:text-zinc-200">{message}</div>
          </div>
          <button type="button" onClick={onClose} className="text-zinc-400 hover:text-black dark:hover:text-zinc-100">
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      </div>
    </div>
  );
}
