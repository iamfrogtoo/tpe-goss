"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { parseFlightCode, FlightCodeDisplay } from "@/utils/flightFormatter";

const CSV_ARR = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=1969230956&single=true&output=csv";
const CSV_DEP = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=2070565332&single=true&output=csv";

interface ScheduleFlight {
    type: "ARR" | "DEP";
    displayDate: string;
    code: string;
    icao: string;
    reg: string;
    time: string;
    std: string;
    etd: string;
    gate: string;
    sortTime: number;
    actype: string;
    terminal: string;
    facility: string;
    statusText: string;
}

export default function Schedule() {
    const [flights, setFlights] = useState<ScheduleFlight[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [typeFilter, setTypeFilter] = useState<"ARR" | "DEP">("ARR");       // Default Arrivals
    const [loading, setLoading] = useState(true);

    const parseDateTime = (d: string, t: string) => {
        // 使用顯式 new Date() 建構，避免 Date.parse 在部分瀏覽器對斜線格式回傳 NaN
        try {
            const [month, day] = d.split('/').map(Number);
            const timeParts = t.split(':').map(Number);
            const [hour, min, sec = 0] = timeParts;
            if (isNaN(month) || isNaN(day) || isNaN(hour) || isNaN(min)) return 9999999999999;
            // 年份跨年修正（12月看到01月，或01月看到12月）
            let year = new Date().getFullYear();
            if (d.startsWith("12") && new Date().getMonth() === 0) year--;
            else if (d.startsWith("01") && new Date().getMonth() === 11) year++;
            return new Date(year, month - 1, day, hour, min, sec).getTime();
        } catch {
            return 9999999999999;
        }
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            const [arrRes, depRes] = await Promise.all([
                fetch(`${CSV_ARR}&t=${Date.now()}`).then((r) => r.text()),
                fetch(`${CSV_DEP}&t=${Date.now()}`).then((r) => r.text()),
            ]);

            let allData: ScheduleFlight[] = [];

            // Parse ARR CSV
            const arrRows = arrRes.replace(/\r/g, "").split("\n").filter((r) => r.trim() !== "");
            if (arrRows.length > 1) {
                if (arrRows.length === 2 && arrRows[1].includes("無資料")) {
                    // Empty state marker
                } else {
                    arrRows.slice(1).forEach((row) => {
                        const c = row.split(",").map((x) => x.replace(/"/g, "").trim());
                        if (c.length >= 5 && c[1]) {
                            const { icao, iata } = parseFlightCode(c[1]);
                            allData.push({
                                type: "ARR",
                                displayDate: c[0],
                                code: iata || icao, // use parsed code
                                icao,
                                time: c[2] || "",
                                gate: c[3] || "",
                                statusText: c[4] || "",
                                terminal: c[5] || "-",
                                facility: c[6] || "-",
                                actype: c[7] || "",
                                reg: c[8] || "",
                                std: c[9] || "",
                                etd: c[10] || "",
                                sortTime: parseDateTime(c[0], c[2]),
                            });
                        }
                    });
                }
            }

            // Parse DEP CSV
            const depRows = depRes.replace(/\r/g, "").split("\n").filter((r) => r.trim() !== "");
            if (depRows.length > 1) {
                if (depRows.length === 2 && depRows[1].includes("無資料")) {
                    // Empty state marker
                } else {
                    depRows.slice(1).forEach((row) => {
                        const c = row.split(",").map((x) => x.replace(/"/g, "").trim());
                        if (c.length >= 5 && c[1]) {
                            const { icao, iata } = parseFlightCode(c[1]);
                            allData.push({
                                type: "DEP",
                                displayDate: c[0],
                                code: iata || icao, // use parsed code
                                icao,
                                time: c[2] || "",
                                gate: c[3] || "",
                                statusText: c[4] || "",
                                terminal: c[5] || "-",
                                facility: c[6] || "-",
                                actype: c[7] || "",
                                reg: c[8] || "",
                                std: c[9] || "",
                                etd: c[10] || "",
                                sortTime: parseDateTime(c[0], c[2]),
                            });
                        }
                    });
                }
            }

            // Deduplicate flights (hide codeshares)
            const uniqueData: ScheduleFlight[] = [];
            const seenFlights = new Set<string>();
            for (const f of allData) {
                const key = `${f.type}_${f.displayDate}_${f.time}_${f.gate}`;
                if (!seenFlights.has(key)) {
                    seenFlights.add(key);
                    uniqueData.push(f);
                }
            }

            // 排序由 tracker_schedule.py 的 Python timestamp 保證正確
            // 前端不再重排序，直接信任 Google Sheets 的資料順序
            // （tracker 以凌晨4點為分隔的整天視窗寫入，Python sorted() 正確處理跨日）

            setFlights(uniqueData);
            setLoading(false);
        } catch (error) {
            console.error(error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // refresh every minute
        return () => clearInterval(interval);
    }, []);

    const filteredFlights = useMemo(() => {
        let result = flights.filter(f => f.type === typeFilter);

        // Since Python backend already filters to -5/+8 hrs window exactly, 
        // we can just passthrough without secondary Date offset logic.
        result = result.filter(f => f.sortTime !== 9999999999999);

        // Search bar filter
        if (searchTerm.trim() !== "") {
            const term = searchTerm.toUpperCase().trim();
            result = result.filter(
                (f) =>
                    f.code.toUpperCase().includes(term) ||
                    f.icao.toUpperCase().includes(term) ||
                    f.gate.toUpperCase().includes(term)
            );
        }

        // 重新依據 timestamp 排序（避免 Google Sheets 欄位排序干擾）
        result.sort((a, b) => a.sortTime - b.sortTime);

        return result;
    }, [flights, searchTerm, typeFilter]);

    return (
        <div className="container-goss">
            {/* 搜尋區塊 */}
            <div className="mb-[20px] bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="搜尋航班 (CI918) 或 機坪 (A1)"
                    className="w-full p-[12px] text-[16px] bg-[#0d0d0d] border border-[#444] text-white rounded-[8px] box-border outline-none focus:border-[#00f260] transition-colors mb-4"
                />

                {/* Toggle 1: ARR vs DEP */}
                <div className="flex gap-2 mb-3">
                    <button
                        onClick={() => setTypeFilter("ARR")}
                        className={`flex-1 py-3 px-4 text-[16px] rounded-lg font-bold transition-all flex flex-col items-center justify-center border-2 ${typeFilter === "ARR"
                            ? "bg-[rgba(0,242,96,0.15)] text-[#00f260] border-[#00f260] shadow-[0_0_15px_rgba(0,242,96,0.2)]"
                            : "bg-transparent text-[#666] border-[#333] hover:border-[#555]"
                            }`}
                    >
                        落地航班
                    </button>
                    <button
                        onClick={() => setTypeFilter("DEP")}
                        className={`flex-1 py-3 px-4 text-[16px] rounded-lg font-bold transition-all flex flex-col items-center justify-center border-2 ${typeFilter === "DEP"
                            ? "bg-[rgba(241,196,15,0.15)] text-[#f1c40f] border-[#f1c40f] shadow-[0_0_15px_rgba(241,196,15,0.2)]"
                            : "bg-transparent text-[#666] border-[#333] hover:border-[#555]"
                            }`}
                    >
                        離場航班
                    </button>
                </div>
            </div>

            <div className="text-center text-[#666] text-[12px] mb-[10px]">
                {loading ? "資料載入中..." : `顯示 ${filteredFlights.length} 筆航班`}
            </div>

            {/* 搜尋結果列表 */}
            <div className="flex flex-col gap-[8px]">
                {!loading && filteredFlights.length === 0 && (
                    <div className="text-center text-[#666] mt-[30px]">無符合結果</div>
                )}

                {filteredFlights.map((f, idx) => (
                    <div
                        key={idx}
                        className={`bg-[#1e1e1e] p-[15px] rounded-[6px] flex justify-between items-center ${f.type === "ARR" ? "border-l-[4px] border-l-[#4facfe]" : "border-l-[4px] border-l-[#f1c40f]"
                            }`}
                    >
                        <div className="flex-1">
                            <div className="flex items-baseline flex-wrap gap-2 mb-1">
                                <span className="text-[20px] font-bold text-white leading-none tracking-wide">{f.icao}</span>
                                <span className="text-[13px] text-[#888] font-mono leading-none">({f.code})</span>
                            </div>
                            <div className="flex items-center flex-wrap gap-[6px] mt-[6px]">
                                {f.type === "ARR" ? (
                                    <span className="text-[11px] text-[#4facfe] font-bold bg-[#4facfe]/10 px-[6px] py-[2px] rounded border border-[#4facfe]/30">ARR</span>
                                ) : (
                                    <span className="text-[11px] text-[#f1c40f] font-bold bg-[#f1c40f]/10 px-[6px] py-[2px] rounded border border-[#f1c40f]/30">DEP</span>
                                )}
                                <span className="text-[14px] text-[#ccc] font-mono tracking-wide ml-1">
                                    {f.displayDate} <span className="text-[#888] ml-1">表定</span> <span className="text-white">{f.std ? f.std.substring(0, 5) : f.time.substring(0, 5)}</span> <span className="text-[#888] ml-1">預估</span> <span className="text-white">{f.etd ? f.etd.substring(0, 5) : "-"}</span>
                                </span>
                            </div>

                            {/* Metadata Badges */}
                            <div className="flex items-center flex-wrap gap-[6px] mt-[8px]">
                                {f.statusText && (
                                    <span className="text-[11px] font-bold bg-[#333] px-[8px] py-[3px] rounded text-[#ddd]">{f.statusText}</span>
                                )}
                                {f.terminal !== "-" && (
                                    <span className="text-[11px] bg-[#222] px-[6px] py-[2px] rounded border border-[#444] text-[#aaa]">T{f.terminal}</span>
                                )}
                                {f.facility !== "-" && (
                                    <span className={`text-[11px] px-[6px] py-[2px] rounded border ${f.type === "ARR" ? "bg-[#0b2413] border-[#00f260]/30 text-[#00f260]" : "bg-[#2a2200] border-[#f1c40f]/30 text-[#f1c40f]"}`}>
                                        {f.type === "ARR" ? `轉盤 ${f.facility}` : `櫃檯 ${f.facility}`}
                                    </span>
                                )}
                                {f.actype && (
                                    <span className="text-[11px] bg-[#222] px-[6px] py-[2px] rounded border border-[#444] text-[#888] font-mono">{f.actype}</span>
                                )}
                                {f.reg && (
                                    <span className="text-[11px] bg-[#1a1a1a] px-[6px] py-[2px] rounded border border-[#444] text-[#eee] font-mono shadow-sm">{f.reg}</span>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center">
                            {f.gate ? (
                                <Link
                                    href={`/gate/${f.gate}`}
                                    className={`text-[20px] font-bold no-underline px-[10px] py-[5px] rounded-[4px] border transition-colors ${["B1R", "C5R", "D5R"].includes(f.gate) || parseInt(f.gate) >= 501
                                        ? "bg-[#2a1a00] text-[#f39c12] border-[#f39c12]/50" // Orange style for remote/cargo
                                        : "bg-[#222] text-[#00f260] border-[#333]"
                                        }`}
                                >
                                    {f.gate}
                                </Link>
                            ) : (
                                <span className="text-[20px] font-bold text-[#666]">-</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
