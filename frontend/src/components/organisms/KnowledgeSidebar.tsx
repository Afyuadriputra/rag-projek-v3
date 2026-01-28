import DocumentItem from "@/components/molecules/DocumentItem";
import type { DocStatus } from "@/components/molecules/DocumentItem";
import ProgressBar from "@/components/atoms/ProgressBar";
import { cn } from "@/lib/utils";

type StorageInfo = {
  used_bytes: number;
  quota_bytes: number;
  used_pct: number;
  used_human?: string;
  quota_human?: string;
};

export default function KnowledgeSidebar({
  onUploadClick,
  docs,
  storage,
  storagePct = 0,
  className,
}: {
  onUploadClick: () => void;
  docs: Array<{ title: string; status: DocStatus }>;
  storage?: StorageInfo;
  storagePct?: number;
  className?: string;
}) {
  const analyzedCount = docs.filter((d) => d.status === "analyzed").length;
  const processingCount = docs.filter((d) => d.status === "processing").length;

  const usedPct = storage?.used_pct ?? storagePct;

  return (
    <aside
      data-testid="knowledge-sidebar"
      className={cn(
        "relative flex w-full flex-col h-full border-r border-zinc-200/50 bg-white/50 backdrop-blur-3xl",
        className
      )}
    >
      {/* --- Header Section --- */}
      <div className="flex flex-col gap-6 p-6 pb-2">
        {/* Title & Stats */}
        <div>
          <h2 className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-zinc-900/40">
            <span className="material-symbols-outlined text-[16px]">
              library_books
            </span>
            Knowledge Base
          </h2>
          <div className="mt-4 flex items-baseline gap-1">
            <span className="text-3xl font-light text-zinc-900">
              {docs.length}
            </span>
            <span className="text-sm font-medium text-zinc-400">Dokumen</span>
          </div>

          {(processingCount > 0 || analyzedCount > 0) && (
            <div className="mt-3 flex gap-3">
              {processingCount > 0 && (
                <div className="flex items-center gap-2 rounded-full border border-amber-100/50 bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700">
                  <span className="relative flex size-1.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
                    <span className="relative inline-flex size-1.5 rounded-full bg-amber-500"></span>
                  </span>
                  Memproses {processingCount}
                </div>
              )}
              {analyzedCount > 0 && (
                <div className="flex items-center gap-2 rounded-full border border-emerald-100/50 bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-700">
                  <span className="size-1.5 rounded-full bg-emerald-500" />
                  Siap {analyzedCount}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Upload Button */}
        <button
          onClick={onUploadClick}
          className="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-zinc-900 py-3 text-white shadow-lg shadow-zinc-200 transition-all hover:bg-zinc-800 hover:shadow-xl active:scale-[0.98]"
        >
          <span className="material-symbols-outlined text-[20px] transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5">
            cloud_upload
          </span>
          <span className="text-[13px] font-medium tracking-wide">
            Unggah Dokumen
          </span>
        </button>
      </div>

      {/* --- Scrollable List --- */}
      <div
        data-testid="doc-list"
        className="scrollbar-hide flex-1 overflow-y-auto px-4 py-2"
      >
        {docs.length > 0 ? (
          <div className="space-y-1">
            <div className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
              Daftar Berkas
            </div>
            {docs.map((d, idx) => (
              <DocumentItem key={idx} title={d.title} status={d.status} />
            ))}
          </div>
        ) : (
          <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-200 bg-zinc-50/50 p-6 text-center">
            <div className="mb-3 rounded-full bg-zinc-100 p-3">
              <span className="material-symbols-outlined text-[24px] text-zinc-300">
                folder_open
              </span>
            </div>
            <h3 className="text-sm font-medium text-zinc-900">
              Belum ada data
            </h3>
            <p className="mt-1 max-w-[180px] text-xs leading-relaxed text-zinc-500">
              Unggah file PDF/Excel akademikmu untuk memulai analisis AI.
            </p>
          </div>
        )}
      </div>

      {/* --- Footer Storage Info --- */}
      <div className="border-t border-zinc-100 bg-white/40 p-5 backdrop-blur-md">
        <div className="mb-3 flex items-end justify-between">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Penyimpanan
            </span>
          </div>
        </div>

        <ProgressBar
          value={usedPct}
          usedBytes={storage?.used_bytes}
          quotaBytes={storage?.quota_bytes}
        />

        <div className="mt-3 flex items-center gap-1.5 text-[10px] text-zinc-400">
          <span className="material-symbols-outlined text-[12px]">lock</span>
          <span>Enkripsi End-to-End • Privat</span>
        </div>
      </div>
    </aside>
  );
}
