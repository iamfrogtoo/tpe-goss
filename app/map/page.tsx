"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { parseFlightCode } from "@/utils/flightFormatter";

// TPE GOSS Inbound Sheet CSV URL
const CSV_ARR =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=0&single=true&output=csv";
// TPE GOSS Outbound Sheet CSV URL
const CSV_DEP =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=2059190189&single=true&output=csv";

// Grid Layouts
const LAYOUT_NORTH = [
    "A1", "A2", "A3", "A4", "A5",
    "A6", "A7", "A8", "A9", "",
    "", "", "", "", "", // Gap
    "D1", "D2", "D3", "D4", "D5",
    "D6", "D7", "D8", "D9", "D10",
    "D11", "D12", "D13", "D14", "D15",
    "D16", "D17", "D18", "", ""
];

const LAYOUT_SOUTH = [
    "B1", "B2", "B3", "B4", "B5",
    "B6", "B7", "B8", "B9", "",
    "", "", "", "", "", // Gap
    "C1", "C2", "C3", "C4", "C5",
    "C6", "C7", "C8", "C9", "C10"
];

const LAYOUT_CARGO = Array.from({ length: 25 }, (_, i) => (501 + i).toString());
const LAYOUT_REMOTE = [
    // B1R, C5R, D5R are standard remote hubs. We show them prominently in the remote section.
    "B1R", "C5R", "D5R", "", "",
    ...Array.from({ length: 15 }, (_, i) => (601 + i).toString())
];

interface GateStatus {
    flightStr: string;
    isOccupied: boolean; // 佔貝 (Arrived but not departed)
    isArr: boolean;      // Incoming
    isDep: boolean;      // Outgoing
    activeFlights: string[]; // List of all flights assigned to this gate
}

export default function MobileMap() {
    const [gateMap, setGateMap] = useState<Record<string, GateStatus>>({});
    const [lastUpdate, setLastUpdate] = useState("連線中...");

    const checkCodeshare = (flights: any[]) => {
        // Deduplicate logic: If multiple flights have the same gate and same time,
        // they are likely codeshares. We prefer the one with a Registration (Reg) if available.
        const unique = new Map();
        flights.forEach(f => {
            const key = `${f.gate}_${f.time}`;
            if (!unique.has(key)) {
                unique.set(key, f);
            } else {
                const existing = unique.get(key);
                // If the new one has a reg and existing doesn't, replace it (mostly for ARR)
                if (f.reg && !existing.reg) {
                    unique.set(key, f);
                }
            }
        });
        return Array.from(unique.values());
    };

    const fetchData = async () => {
        try {
            const [arrRes, depRes] = await Promise.all([
                fetch(`${CSV_ARR}&t=${Date.now()}`),
                fetch(`${CSV_DEP}&t=${Date.now()}`),
            ]);

            const arrText = await arrRes.text();
            const depText = await depRes.text();

            const arrRows = arrText.replace(/\r/g, "").split("\n").map(r => r.split(",").map(x => x ? x.replace(/"/g, "").trim() : ""));
            const depRows = depText.replace(/\r/g, "").split("\n").map(r => r.split(",").map(x => x ? x.replace(/"/g, "").trim() : ""));

            const now = new Date();
            const currentMins = now.getHours() * 60 + now.getMinutes();

            const parseTimeMins = (timeStr: string) => {
                if (!timeStr || !timeStr.includes(":")) return 9999;
                const [h, m] = timeStr.split(":");
                let mins = parseInt(h, 10) * 60 + parseInt(m, 10);
                if (mins < currentMins - 720) mins += 1440;
                if (mins > currentMins + 720) mins -= 1440;
                return mins;
            };

            const arrHeaders = arrRows.length > 0 ? arrRows[0] : [];
            const depHeaders = depRows.length > 0 ? depRows[0] : [];

            const arrIdx = {
                code: arrHeaders.findIndex(h => h.includes("航班")),
                gate: arrHeaders.findIndex(h => h.includes("機坪")),
                status: arrHeaders.findIndex(h => h.includes("狀態")),
                std: arrHeaders.findIndex(h => h.includes("表定")),
                etd: arrHeaders.findIndex(h => h.includes("預計")),
            };

            const depIdx = {
                code: depHeaders.findIndex(h => h.includes("航班")),
                gate: depHeaders.findIndex(h => h.includes("機坪")),
                status: depHeaders.findIndex(h => h.includes("狀態")),
                std: depHeaders.findIndex(h => h.includes("表定")),
                etd: depHeaders.findIndex(h => h.includes("預計")),
            };

            const gateEvents = new Map<string, any[]>();

            arrRows.slice(1).forEach((r) => {
                if (arrIdx.gate === -1 || arrIdx.code === -1) return;
                const g = r[arrIdx.gate];
                const code = r[arrIdx.code];
                if (!g || !code || code.includes("航班")) return;

                if (!gateEvents.has(g)) gateEvents.set(g, []);
                const { icao, iata } = parseFlightCode(code);
                gateEvents.get(g)!.push({
                    type: "ARR",
                    icao: iata || icao,
                    status: arrIdx.status !== -1 ? r[arrIdx.status] || "" : "",
                    time: parseTimeMins((arrIdx.etd !== -1 ? r[arrIdx.etd] : null) || (arrIdx.std !== -1 ? r[arrIdx.std] : null) || "")
                });
            });

            depRows.slice(1).forEach((r) => {
                if (depIdx.gate === -1 || depIdx.code === -1) return;
                const g = r[depIdx.gate];
                const code = r[depIdx.code];
                if (!g || !code || code.includes("航班")) return;

                if (!gateEvents.has(g)) gateEvents.set(g, []);
                const { icao, iata } = parseFlightCode(code);
                gateEvents.get(g)!.push({
                    type: "DEP",
                    icao: iata || icao,
                    status: depIdx.status !== -1 ? r[depIdx.status] || "" : "",
                    time: parseTimeMins((depIdx.etd !== -1 ? r[depIdx.etd] : null) || (depIdx.std !== -1 ? r[depIdx.std] : null) || "")
                });
            });

            const newMap: Record<string, GateStatus> = {};

            for (const [g, evs] of gateEvents.entries()) {
                // Collect day's active flights for listing on remote gates
                const allIcaos = evs.map(e => e.icao).filter(x => x);
                const activeSet = Array.from(new Set(allIcaos));

                // Sort chronologically
                evs.sort((a, b) => a.time - b.time);

                let isOccupied = false;
                let isArr = false;
                let isDep = false;
                let flightStr = "";

                for (const ev of evs) {
                    if (ev.type === "ARR") {
                        if (ev.status.includes("已到") || ev.status.includes("落地") || ev.status.includes("滑行")) {
                            isOccupied = true;
                            isArr = false;
                            isDep = false;
                            flightStr = ev.icao;
                        } else if (ev.status.includes("即將") || ev.status.includes("進場")) {
                            if (!isOccupied) {
                                isArr = true;
                                isDep = false;
                                flightStr = ev.icao;
                            }
                        } else if (!isOccupied && !isArr && !isDep && !flightStr) {
                            flightStr = ev.icao; // Future
                        }
                    } else if (ev.type === "DEP") {
                        if (ev.status.includes("起飛") || ev.status.includes("已飛") || ev.status.includes("取消")) {
                            isOccupied = false;
                            isDep = false;
                            isArr = false;
                            flightStr = ""; // it's gone
                        } else if (ev.status.includes("登機") || ev.status.includes("關艙") || ev.status.includes("後推")) {
                            isOccupied = true;
                            isDep = true;
                            isArr = false;
                            flightStr = ev.icao;
                        } else if (isOccupied) {
                            // If it's a turnaround, the gate is already occupied by the ARR flight.
                            flightStr = ev.icao;
                        } else if (!isOccupied && !isArr && !isDep && !flightStr) {
                            flightStr = ev.icao;
                        }
                    }
                }

                newMap[g] = {
                    flightStr,
                    isOccupied,
                    isArr,
                    isDep,
                    activeFlights: activeSet
                };
            }

            setGateMap(newMap);
            setLastUpdate(`更新: ${new Date().toLocaleTimeString()}`);
        } catch (e) {
            console.error(e);
            setLastUpdate("連線讀取失敗");
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const renderGrid = (gates: string[]) => {
        return (
            <div className="grid grid-cols-5 gap-[6px]">
                {gates.map((g, idx) => {
                    if (!g) return <div key={idx} className="invisible"></div>;

                    const data = gateMap[g];
                    let boxClass = "bg-[#111] border-[#333] text-[#666]";
                    const isSpecialRemote = ["B1R", "C5R", "D5R"].includes(g);

                    if (data) {
                        if (isSpecialRemote) {
                            boxClass = "bg-[#111] border-[#333] text-[#eee]";
                        } else {
                            if (data.isOccupied) {
                                // 佔貝: White background, black text
                                boxClass = "bg-[#fff] border-[#fff] text-[#000] shadow-[0_0_8px_rgba(255,255,255,0.4)]";
                            } else if (data.isDep) {
                                // 離場準備: Dark yellow bg, yellow border
                                boxClass = "bg-[#2a2200] border-[#f1c40f] text-[#f1c40f]";
                            } else if (data.isArr) {
                                // 準備進場: Dark red bg, red border
                                boxClass = "bg-[#2a0000] border-[#ff4b4b] text-[#ff4b4b]";
                            } else if (data.flightStr) { // Has assignment but not active yet
                                boxClass = "bg-[#1a1a1a] border-[#555] text-[#aaa]";
                            }
                        }
                    }

                    return (
                        <Link
                            href={`/gate/${g}`}
                            key={idx}
                            className={`aspect-square rounded-[6px] border font-black relative transition-transform active:scale-95 no-underline flex flex-col ${boxClass} ${isSpecialRemote ? "p-[6px] items-start justify-start" : "p-[6px]"
                                }`}
                        >
                            {isSpecialRemote ? (
                                <>
                                    <span className="text-[14px] text-white font-bold leading-none mb-[4px]">{g}</span>
                                    <div className="flex-1 w-full flex flex-col items-center justify-center gap-[2px]">
                                        {data?.activeFlights?.slice(0, 3).map((fl, i) => (
                                            <span key={i} className="text-[11px] font-mono text-[#ccc] leading-none tracking-tight">
                                                {fl}
                                            </span>
                                        ))}
                                        {data?.activeFlights && data.activeFlights.length > 3 && (
                                            <span className="text-[10px] text-[#888] leading-none tracking-tight">
                                                +{data.activeFlights.length - 3}
                                            </span>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center w-full h-full p-1 relative">
                                    <span className="text-[clamp(14px,4vw,22px)] leading-none mb-1">{g}</span>
                                    {data?.flightStr && (
                                        <span className="text-[clamp(10px,3vw,16px)] font-bold leading-none select-none tracking-tight text-center break-all">
                                            {data.flightStr.substring(0, 6)}
                                        </span>
                                    )}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="container-goss pb-[40px] px-[10px] max-w-[500px] mx-auto">
            <div className="text-center text-[11px] text-[#666] mb-[15px]">{lastUpdate}</div>

            <div className="flex justify-between items-end border-b-2 border-[#333] mb-[12px] pb-[6px] mt-[10px]">
                <span className="text-[18px] font-bold text-[#00f260]">北機坪 (North)</span>
                <span className="text-[14px] text-[#00f260]">A / D</span>
            </div>
            {renderGrid(LAYOUT_NORTH)}

            <div className="flex justify-between items-end border-b-2 border-[#333] mb-[12px] pb-[6px] mt-[30px]">
                <span className="text-[18px] font-bold text-[#00f260]">南機坪 (South)</span>
                <span className="text-[14px] text-[#00f260]">B / C</span>
            </div>
            {renderGrid(LAYOUT_SOUTH)}

            <div className="flex justify-between items-end border-b-2 border-[#333] mb-[12px] pb-[6px] mt-[30px]">
                <span className="text-[18px] font-bold text-[#00f260]">貨機坪 (Cargo)</span>
                <span className="text-[14px] text-[#00f260]">500-525</span>
            </div>
            {renderGrid(LAYOUT_CARGO)}

            <div className="flex justify-between items-end border-b-2 border-[#333] mb-[12px] pb-[6px] mt-[30px]">
                <span className="text-[18px] font-bold text-[#00f260]">接駁坪 (Remote)</span>
                <span className="text-[14px] text-[#00f260]">601-615</span>
            </div>
            {renderGrid(LAYOUT_REMOTE)}
        </div>
    );
}
