import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

export default function ChatComposer({
  onSend,
  onUploadClick,
  loading,
}: {
  onSend: (message: string) => void;
  onUploadClick: () => void;
  loading?: boolean;
}) {
  const [value, setValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = Math.min(160, ta.scrollHeight) + "px";
  }, [value]);

  const submit = () => {
    const msg = value.trim();
    if (!msg || loading) return;
    onSend(msg);
    setValue("");
    if (taRef.current) taRef.current.style.height = "auto";
  };

  const canSend = !!value.trim() && !loading;

  return (
    <div className="absolute bottom-0 left-0 w-full z-20" data-testid="chat-composer">
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-white via-white/90 to-transparent pointer-events-none" />

      <div className="relative mx-auto w-full max-w-3xl px-4 pb-6 pt-4">
        <div
          className={cn(
            "relative flex items-end gap-2 p-2",
            "rounded-[32px] border border-white/40",
            "bg-white/60 backdrop-blur-[20px] backdrop-saturate-150",
            "shadow-[0_8px_40px_-10px_rgba(0,0,0,0.1)]",
            "transition-all duration-500 ease-out",
            isFocused
              ? "shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] bg-white/80 border-white/80 translate-y-[-2px]"
              : "hover:bg-white/70"
          )}
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/60 to-transparent opacity-50" />

          {/* UPLOAD BUTTON */}
          <button
            data-testid="chat-upload"
            type="button"
            onClick={onUploadClick}
            disabled={loading}
            className={cn(
              "group relative flex size-10 flex-shrink-0 items-center justify-center rounded-full transition-all duration-300",
              "text-zinc-400 hover:text-zinc-800",
              "hover:bg-zinc-100/50"
            )}
            title="Unggah dokumen"
          >
            <span className="material-symbols-outlined text-[22px] transition-transform duration-300 group-hover:rotate-12">
              add_circle
            </span>
          </button>

          {/* TEXT AREA */}
          <div className="flex-1 py-2">
            <textarea
              data-testid="chat-input"
              ref={taRef}
              value={value}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Tanya sesuatu..."
              rows={1}
              disabled={loading}
              className={cn(
                "block w-full resize-none bg-transparent px-2",
                "text-[16px] leading-relaxed text-zinc-800 placeholder:text-zinc-400 font-light",
                "border-none focus:ring-0 focus:outline-none",
                "max-h-[160px] overflow-y-auto scrollbar-hide"
              )}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
            />
          </div>

          {/* SEND BUTTON */}
          <div className="flex size-10 items-center justify-center">
            <button
              data-testid="chat-send"
              type="button"
              onClick={submit}
              disabled={!canSend}
              className={cn(
                "flex items-center justify-center rounded-full transition-all duration-500 cubic-bezier(0.34, 1.56, 0.64, 1)",
                canSend
                  ? "size-10 bg-black text-white shadow-lg scale-100 opacity-100 rotate-0"
                  : "size-8 bg-zinc-200 text-zinc-400 scale-90 opacity-0 rotate-45 pointer-events-none"
              )}
            >
              <span className="material-symbols-outlined text-[20px]">
                {loading ? "stop" : "arrow_upward"}
              </span>
            </button>
          </div>
        </div>

        <div className="mt-3 flex justify-center">
          <p className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-zinc-400/80 font-medium">
            {loading ? (
              <>
                <span className="block size-1.5 animate-pulse rounded-full bg-zinc-400" />
                Thinking...
              </>
            ) : (
              "Academic AI • Context Aware"
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
