"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Settings2, Camera, Sparkles } from "lucide-react";

const NAV_ITEMS = [
    {
        href: "/",
        label: "Dashboard",
        icon: <Home size={16} />,
        gradient: "from-emerald-400 to-teal-500",
        activeClass: "bg-gradient-to-r from-emerald-400 to-teal-500 text-white shadow-emerald-500/40",
        glowColor: "shadow-emerald-500/60",
    },
    {
        href: "/calibration",
        label: "Sensor Calibration",
        icon: <Settings2 size={16} />,
        gradient: "from-sky-400 to-cyan-500",
        activeClass: "bg-gradient-to-r from-sky-400 to-cyan-500 text-white shadow-sky-500/40",
        glowColor: "shadow-cyan-500/60",
    },
    {
        href: "/mas",
        label: "Multi-Agent System",
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <circle cx="12" cy="21" r="1" />
            </svg>
        ),
        gradient: "from-green-500 to-blue-500",
        activeClass: "bg-gradient-to-r from-green-500 to-blue-500 text-white shadow-green-500/40",
        glowColor: "shadow-green-500/60",
    },
    {
        href: "/camera",
        label: "Plant Camera",
        icon: <Camera size={16} />,
        gradient: "from-orange-400 to-pink-500",
        activeClass: "bg-gradient-to-r from-orange-400 to-pink-500 text-white shadow-orange-500/40",
        glowColor: "shadow-pink-500/60",
    },
    {
        href: "/ai",
        label: "AI Assistant",
        icon: <Sparkles size={16} />,
        gradient: "from-violet-500 to-fuchsia-500",
        activeClass: "bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white shadow-fuchsia-500/40",
        glowColor: "shadow-fuchsia-500/60",
    },
    {
        href: "/dt-brain",
        label: "DT Brain",
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
                <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
                <path d="M15 13a4.5 4.5 0 0 1-3 4 4.5 4.5 0 0 1-3-4" />
                <path d="M12 18v4" />
                <path d="M9.5 9.4h.01" />
                <path d="M14.5 9.4h.01" />
            </svg>
        ),
        gradient: "from-indigo-500 to-violet-500",
        activeClass: "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-violet-500/40",
        glowColor: "shadow-violet-500/60",
    },
];

export default function Navbar() {
    const pathname = usePathname();

    return (
        <div className="fixed bottom-6 left-0 right-0 z-50 flex justify-center pointer-events-none">
            <nav className="pointer-events-auto flex items-center gap-1.5 px-3 py-2.5 rounded-2xl
                bg-gray-950/80 backdrop-blur-2xl
                border border-white/10
                shadow-[0_8px_32px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.05),inset_0_1px_0_rgba(255,255,255,0.08)]
                overflow-x-auto max-w-[95vw]"
            >
                {NAV_ITEMS.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium
                                whitespace-nowrap transition-all duration-200
                                ${isActive
                                    ? `bg-gradient-to-r ${item.gradient} text-white scale-[1.06]
                                       shadow-[0_0_16px_2px] ${item.glowColor} brightness-110`
                                    : `bg-gradient-to-r ${item.gradient} opacity-30
                                       hover:opacity-80 hover:scale-[1.03] hover:shadow-md hover:brightness-110`
                                }
                            `}
                        >
                            {item.icon}
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
