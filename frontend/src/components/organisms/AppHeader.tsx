import { useState } from "react";
import { Link } from "@inertiajs/react"; // Import Link untuk navigasi Inertia
import NavTabs from "@/components/molecules/NavTabs";
import ToggleSwitch from "@/components/atoms/ToggleSwitch";
import Avatar from "@/components/atoms/Avatar";
import { cn } from "@/lib/utils";

export default function AppHeader({
  dark,
  onToggleDark,
  mode,
  onModeChange,
  modeDisabled = false,
  user, // Update: Menerima object user lengkap, bukan cuma username
}: {
  dark: boolean;
  onToggleDark: (v: boolean) => void;
  mode: "chat" | "planner";
  onModeChange: (mode: "chat" | "planner") => void;
  modeDisabled?: boolean;
  user: { username: string; email: string };
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header
      className={cn(
        "sticky top-0 z-20 flex h-16 w-full flex-none items-center justify-between px-4 transition-all md:px-8",
        "backdrop-blur-xl backdrop-saturate-150",
        dark
          ? "border-b border-zinc-700/40 bg-zinc-900/70 text-zinc-100 shadow-[0_4px_30px_rgba(0,0,0,0.35)]"
          : "border-b border-white/20 bg-white/60 text-zinc-900 shadow-[0_4px_30px_rgba(0,0,0,0.03)]"
      )}
    >
      {/* --- LEFT SECTION (Logo) --- */}
      <div className="flex items-center gap-3 pl-12 md:pl-0">
        <div className="group flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-zinc-800 to-black shadow-lg shadow-black/20 transition-transform duration-500 hover:rotate-6 hover:scale-105">
          <span className="material-symbols-outlined text-[20px] font-light text-white">
            school
          </span>
        </div>
        <h1 className={cn("hidden text-[13px] font-semibold tracking-[0.2em] uppercase sm:block", dark ? "text-zinc-100" : "text-zinc-800")}>
          Academic AI
        </h1>
      </div>

      {/* --- CENTER SECTION (Nav) --- */}
      <div className="absolute left-1/2 hidden -translate-x-1/2 md:flex md:items-center md:gap-3">
        <NavTabs active="Chat" />
        <div className={cn("flex items-center rounded-full p-1 shadow-sm backdrop-blur-md", dark ? "border border-zinc-700/50 bg-zinc-800/70" : "border border-white/40 bg-white/55")}>
          <button
            data-testid="mode-chat"
            type="button"
            disabled={modeDisabled}
            onClick={() => onModeChange("chat")}
            className={cn(
              "rounded-full px-3 py-1 text-[11px] font-semibold tracking-wide transition",
              mode === "chat" ? "bg-zinc-900 text-white" : dark ? "text-zinc-300 hover:text-zinc-100" : "text-zinc-600 hover:text-zinc-900",
              modeDisabled && "cursor-not-allowed opacity-60"
            )}
          >
            <span className="inline-flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[14px]">chat</span>
              Chat
            </span>
          </button>
          <button
            data-testid="mode-planner"
            type="button"
            disabled={modeDisabled}
            onClick={() => onModeChange("planner")}
            className={cn(
              "rounded-full px-3 py-1 text-[11px] font-semibold tracking-wide transition",
              mode === "planner" ? "bg-zinc-900 text-white" : dark ? "text-zinc-300 hover:text-zinc-100" : "text-zinc-600 hover:text-zinc-900",
              modeDisabled && "cursor-not-allowed opacity-60"
            )}
          >
            <span className="inline-flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[14px]">event_note</span>
              Plan
            </span>
          </button>
        </div>
      </div>

      {/* --- RIGHT SECTION (Actions) --- */}
      <div className="flex items-center gap-3 md:gap-5">
        <div className={cn("flex items-center rounded-full p-1 shadow-sm backdrop-blur-md md:hidden", dark ? "border border-zinc-700/50 bg-zinc-800/70" : "border border-white/40 bg-white/55")}>
          <button
            data-testid="mode-chat-mobile"
            type="button"
            disabled={modeDisabled}
            onClick={() => onModeChange("chat")}
            className={cn(
              "rounded-full px-2.5 py-1 text-[10px] font-semibold transition",
              mode === "chat" ? "bg-zinc-900 text-white" : dark ? "text-zinc-300" : "text-zinc-600",
              modeDisabled && "cursor-not-allowed opacity-60"
            )}
          >
            <span className="material-symbols-outlined text-[14px]">chat</span>
          </button>
          <button
            data-testid="mode-planner-mobile"
            type="button"
            disabled={modeDisabled}
            onClick={() => onModeChange("planner")}
            className={cn(
              "rounded-full px-2.5 py-1 text-[10px] font-semibold transition",
              mode === "planner" ? "bg-zinc-900 text-white" : dark ? "text-zinc-300" : "text-zinc-600",
              modeDisabled && "cursor-not-allowed opacity-60"
            )}
          >
            <span className="material-symbols-outlined text-[14px]">event_note</span>
          </button>
        </div>
        
        {/* Control Group */}
        <div className={cn("flex items-center gap-1 rounded-full p-1 pr-3 backdrop-blur-md shadow-sm", dark ? "border border-zinc-700/50 bg-zinc-800/70" : "border border-white/40 bg-white/40")}>
          <div className="flex items-center gap-2 pl-1">
             <span className={cn("material-symbols-outlined text-[16px]", dark ? "text-zinc-300" : "text-zinc-400")}>
                {dark ? "dark_mode" : "light_mode"}
             </span>
             <ToggleSwitch checked={dark} onChange={onToggleDark} />
          </div>
          <div className={cn("mx-2 h-4 w-px", dark ? "bg-zinc-600/70" : "bg-zinc-300/50")} />
          <button
            type="button"
            aria-label="Notifications"
            className={cn("group relative flex size-8 items-center justify-center rounded-full transition-colors", dark ? "hover:bg-white/10" : "hover:bg-black/5")}
          >
            <span className={cn("material-symbols-outlined text-[20px] transition-colors", dark ? "text-zinc-300 group-hover:text-white" : "text-zinc-500 group-hover:text-zinc-800")}>
              notifications
            </span>
            <span className={cn("absolute right-1.5 top-1.5 size-2 rounded-full bg-red-500 shadow-sm", dark ? "border border-zinc-900" : "border border-white")} />
          </button>
        </div>

        {/* Profile Section with Dropdown */}
        <div className="relative">
            <button 
                data-testid="user-menu-button"
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-3 outline-none"
            >
                <div className="hidden text-right md:block">
                    <p className={cn("text-[12px] font-semibold leading-tight", dark ? "text-zinc-200" : "text-zinc-700")}>
                        {user.username}
                    </p>
                    <p className={cn("text-[10px] font-medium tracking-wide uppercase", dark ? "text-zinc-400" : "text-zinc-400")}>
                        Mahasiswa
                    </p>
                </div>
                
                <div className="relative transition-transform hover:scale-105 active:scale-95">
                    <div className={cn("rounded-full border-2 shadow-md transition-colors", menuOpen ? "border-black" : "border-white")}>
                        <Avatar imageUrl="https://lh3.googleusercontent.com/aida-public/AB6AXuAoTjR3RYjL2AEMA-cRAUKJ2RD9-jLlLh15wfkA75ckExydx9hpo_jeGgce18JPCU0vo2ys5ZiQ_EaSug1uZKAqe-BMsENRTlrSGbbQGssUNxu_ZfX0zw7Cel15Rdz7KFpT2MAHeD1cz-Z0cBnD0ClUnQxb1XklqULYuxZLy9UxbawMuBMdCQrDfL6Z81vJPpKPlgCzsPTfbCum3Xvjd8uuD6MEMnfJPr--MZ4Ap6HlFui0hshnJJ6Bvta7btSimet0VXW9ql3bBC_l" />
                    </div>
                    <div className="absolute bottom-0 right-0 size-2.5 rounded-full border-[1.5px] border-white bg-green-500 shadow-sm" />
                </div>
            </button>

            {/* --- DROPDOWN MENU (LOGOUT) --- */}
            {menuOpen && (
                <>
                    {/* Backdrop untuk menutup menu saat klik luar */}
                    <div 
                        className="fixed inset-0 z-30 cursor-default" 
                        onClick={() => setMenuOpen(false)} 
                    />
                    
                    {/* Menu Content */}
                    <div className={cn("absolute right-0 top-full z-40 mt-3 w-56 overflow-hidden rounded-2xl p-1 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200", dark ? "border border-zinc-700/60 bg-zinc-900/95" : "border border-white/40 bg-white/80")}>
                        <div className={cn("px-4 py-3", dark ? "border-b border-zinc-700/70" : "border-b border-black/5")}>
                            <p className={cn("text-xs font-medium", dark ? "text-zinc-400" : "text-zinc-500")}>Masuk sebagai</p>
                            <p className={cn("truncate text-sm font-bold", dark ? "text-zinc-100" : "text-zinc-900")}>{user.email}</p>
                        </div>
                        
                        <div className="p-1">
                            <Link
                                data-testid="logout-link"
                                href="/logout/" // Sesuai endpoint Django
                                className={cn("flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-red-600 transition-colors", dark ? "hover:bg-red-900/20" : "hover:bg-red-50")}
                            >
                                <span className="material-symbols-outlined text-[18px]">logout</span>
                                Keluar
                            </Link>
                        </div>
                    </div>
                </>
            )}
        </div>

      </div>
    </header>
  );
}
