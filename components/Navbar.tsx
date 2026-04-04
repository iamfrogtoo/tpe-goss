"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
    const pathname = usePathname();

    const navItems = [
        { href: "/", icon: "🛬", label: "即時降落" },
        { href: "/outbound", icon: "🛫", label: "即時離場" },
        { href: "/map", icon: "🗺️", label: "機坪地圖" },
        { href: "/schedule", icon: "🔍", label: "航班查詢" },
        { href: "/about", icon: "ℹ️", label: "開發日誌" },
    ];

    return (
        <div className="fixed top-0 left-0 right-0 h-[50px] bg-[#1a1a1a] border-b border-[#333] flex items-center justify-around z-[1000] overflow-x-auto whitespace-nowrap scrollbar-hide">
            {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`flex flex-col items-center px-[10px] text-[12px] no-underline transition-colors ${isActive
                            ? "text-[#00f260] font-bold drop-shadow-[0_0_8px_rgba(0,242,96,0.4)]"
                            : "text-[#888] hover:text-[#ccc]"
                            }`}
                    >
                        <span className="text-[16px] mb-[2px]">{item.icon}</span>
                        {item.label}
                    </Link>
                );
            })}
        </div>
    );
}
