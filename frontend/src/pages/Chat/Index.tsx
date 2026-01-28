import React, { useEffect, useMemo, useRef, useState } from "react";
import { usePage } from "@inertiajs/react";
import { cn } from "@/lib/utils"; 

// Components
import AppHeader from "@/components/organisms/AppHeader";
import KnowledgeSidebar from "@/components/organisms/KnowledgeSidebar";
import ChatThread from "@/components/organisms/ChatThread";
import ChatComposer from "@/components/molecules/ChatComposer";
import Toast from "@/components/molecules/Toast";

// API & Types
import { sendChat, uploadDocuments, getDocuments } from "@/lib/api";
import type { DocumentDto, DocumentsResponse } from "@/lib/api";
import type { ChatItem } from "@/components/molecules/ChatBubble";

// --- Types ---
type StorageInfo = {
  used_bytes: number;
  quota_bytes: number;
  used_pct: number;
  used_human?: string;
  quota_human?: string;
};

type PageProps = {
  user: { id: number; username: string; email: string };
  initialHistory: Array<{
    question: string;
    answer: string;
    time: string;
    date: string;
  }>;
  documents: DocumentDto[];
  storage: StorageInfo;
};

// --- Helper ---
function uid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

export default function Index() {
  const { props } = usePage<PageProps>();
  const {
    user,
    initialHistory,
    documents: initialDocs,
    storage: initialStorage,
  } = props;

  // State
  const [dark, setDark] = useState(false);
  const [documents, setDocuments] = useState<DocumentDto[]>(initialDocs ?? []);
  const [storage, setStorage] = useState<StorageInfo | undefined>(initialStorage);
  const [loading, setLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false); 

  // Toast State
  const [toast, setToast] = useState<{
    open: boolean;
    kind: "success" | "error";
    msg: string;
  }>({ open: false, kind: "success", msg: "" });

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // --- Effects ---
  useEffect(() => {
    const root = document.documentElement;
    if (dark) root.classList.add("dark");
    else root.classList.remove("dark");
  }, [dark]);

  // --- Data Logic ---
  const refreshDocuments = async () => {
    try {
      const res: DocumentsResponse = await getDocuments();
      setDocuments(res.documents ?? []);
      if (res.storage) setStorage(res.storage as StorageInfo);
    } catch {
      // silent fail
    }
  };

  const initialItems = useMemo<ChatItem[]>(() => {
    const arr: ChatItem[] = [];
    if (!initialHistory || initialHistory.length === 0) {
      arr.push({
        id: uid(),
        role: "assistant",
        text: "Halo! Saya siap membantu analisis akademikmu. Unggah transkrip atau KRS, lalu tanyakan rekap nilai atau IPK.",
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
      return arr;
    }
    for (const h of initialHistory) {
      arr.push({ id: uid(), role: "user", text: h.question, time: h.time });
      arr.push({ id: uid(), role: "assistant", text: h.answer, time: h.time });
    }
    return arr;
  }, [initialHistory]);

  const [items, setItems] = useState<ChatItem[]>(initialItems);

  // --- Handlers ---
  const onSend = async (message: string) => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userItem: ChatItem = {
      id: uid(),
      role: "user",
      text: message,
      time: timeStr,
    };
    setItems((prev) => [...prev, userItem]);

    setLoading(true);
    try {
      const res = await sendChat(message);
      const aiText = res.answer ?? res.error ?? "Maaf, tidak ada jawaban.";
      const aiItem: ChatItem = {
        id: uid(),
        role: "assistant",
        text: aiText,
        time: timeStr,
      };
      setItems((prev) => [...prev, aiItem]);
    } catch (e: any) {
      setToast({
        open: true,
        kind: "error",
        msg: e?.message ?? "Gagal terhubung ke AI.",
      });
    } finally {
      setLoading(false);
    }
  };

  const onUploadClick = () => fileInputRef.current?.click();

  const onUploadChange: React.ChangeEventHandler<HTMLInputElement> = async (
    e
  ) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setLoading(true);
    setMobileMenuOpen(false); 

    try {
      const res = await uploadDocuments(files);
      setToast({
        open: true,
        kind: res.status === "success" ? "success" : "error",
        msg: res.msg,
      });
      await refreshDocuments();
    } catch (err: any) {
      setToast({
        open: true,
        kind: "error",
        msg: err?.message ?? "Upload gagal.",
      });
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    // Menggunakan h-[100dvh] untuk mobile browser support
    <div className="relative flex h-[100dvh] w-full flex-col overflow-hidden bg-zinc-50 font-sans text-zinc-900 selection:bg-black selection:text-white">
      
      {/* 1. AMBIENT BACKGROUND */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -left-[10%] -top-[10%] h-[50vh] w-[50vw] rounded-full bg-blue-100/40 blur-[100px]" />
        <div className="absolute -bottom-[10%] -right-[10%] h-[50vh] w-[50vw] rounded-full bg-indigo-100/40 blur-[100px]" />
      </div>

      {/* 2. HEADER */}
      <div className="relative z-10 flex-none">
        <AppHeader
          dark={dark}
          onToggleDark={setDark}
          user={user} // UPDATE: Passing full user object untuk keperluan dropdown logout
        />
      </div>

      {/* 3. MAIN LAYOUT */}
      <div className="relative flex flex-1 overflow-hidden">
        
        {/* --- DESKTOP SIDEBAR --- */}
        <div className="hidden h-full md:flex">
            <KnowledgeSidebar
              onUploadClick={onUploadClick}
              docs={documents.map((d) => ({
                title: d.title,
                status: d.is_embedded ? "analyzed" : "processing",
              }))}
              storage={storage}
            />
        </div>

        {/* --- MOBILE SIDEBAR (Drawer) --- */}
        <div
          className={cn(
            "fixed inset-0 z-40 bg-black/20 backdrop-blur-sm transition-opacity duration-300 md:hidden",
            mobileMenuOpen ? "opacity-100" : "opacity-0 pointer-events-none"
          )}
          onClick={() => setMobileMenuOpen(false)}
        />
        <div
          className={cn(
            "fixed inset-y-0 left-0 z-50 w-[280px] bg-white/90 backdrop-blur-2xl transition-transform duration-300 ease-out md:hidden shadow-2xl",
            mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
           <KnowledgeSidebar
              onUploadClick={onUploadClick}
              docs={documents.map((d) => ({
                title: d.title,
                status: d.is_embedded ? "analyzed" : "processing",
              }))}
              storage={storage}
            />
        </div>

        {/* --- CHAT AREA --- */}
        <main className="relative z-0 flex h-full flex-1 flex-col">
          
          {/* Mobile Menu Trigger */}
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="absolute left-4 top-4 z-30 flex size-10 items-center justify-center rounded-full border border-black/5 bg-white/60 text-zinc-600 shadow-sm backdrop-blur-md transition active:scale-95 md:hidden"
          >
             <span className="material-symbols-outlined text-[20px]">menu</span>
          </button>

          {/* CHAT THREAD CONTAINER */}
          <div className="flex-1 w-full overflow-y-auto scrollbar-hide pb-60 pt-20 md:pb-36 md:pt-4">
             <ChatThread items={items} />
          </div>

          {/* Composer */}
          <ChatComposer
            onSend={onSend}
            onUploadClick={onUploadClick}
            loading={loading}
          />
        </main>
      </div>

      {/* Hidden File Input */}
<input
  data-testid="upload-input"
  ref={fileInputRef}
  type="file"
  multiple
  className="hidden"
  onChange={onUploadChange}
  accept=".pdf,.xlsx,.xls,.csv,.md,.txt"
/>


      {/* Toast */}
      <Toast
        open={toast.open}
        kind={toast.kind}
        message={toast.msg}
        onClose={() => setToast((p) => ({ ...p, open: false }))}
      />
    </div>
  );
}