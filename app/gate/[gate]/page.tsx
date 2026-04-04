"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { parseFlightCode, FlightCodeDisplay } from "@/utils/flightFormatter";

const CSV_ARR =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=0&single=true&output=csv";
const CSV_DEP =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=2059190189&single=true&output=csv";
const CSV_BAY =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=214244940&single=true&output=csv";

interface GateEvent {
    type: "ARR" | "DEP" | "TRANSIT" | "TURNAROUND";
    flight: string;
    status?: string;
    arrFlight?: string;
    depFlight?: string;
    reg?: string;
    actype?: string;
    counter?: string;
    baggage?: string; // 加入轉盤
    time: string; // schedule time 
    eta?: string; // actual time
    arrTime?: string;
    arrEta?: string;
    depTime?: string;
    depEta?: string;
    rawTime: number;
}

export default function GateDetail() {
    const params = useParams();
    const router = useRouter();
    const gate = params.gate as string;

    const [dateSubtitle, setDateSubtitle] = useState("Loading...");
    const [events, setEvents] = useState<GateEvent[]>([]);
    const [loading, setLoading] = useState(true);

    // Reference for auto-scrolling
    const activeEventRef = useRef<HTMLDivElement>(null);

    const fetchCSV = async (url: string) => {
        try {
            const res = await fetch(`${url}&t=${Date.now()}`);
            const text = await res.text();
            return text.split("\n").map((r) => r.split(",").map((x) => (x ? x.replace(/"/g, "").trim() : "")));
        } catch (e) {
            console.error(e);
            return [];
        }
    };

    const nowLocal = new Date();
    const currentMins = nowLocal.getHours() * 60 + nowLocal.getMinutes();

    const parseTimeMins = (timeStr: string) => {
        if (!timeStr || !timeStr.includes(":")) return 9999;
        const [h, m] = timeStr.split(":");
        let mins = parseInt(h, 10) * 60 + parseInt(m, 10);
        if (mins < currentMins - 720) mins += 1440;
        if (mins > currentMins + 720) mins -= 1440;
        return mins;
    };

    const checkCodeshare = (data: GateEvent[]) => {
        // Deduplicate logic: Same type and time = codeshare. Prefer one with Aircraft Reg.
        const unique = new Map();
        data.forEach(f => {
            const key = `${f.type}_${f.time}`;
            if (!unique.has(key)) {
                unique.set(key, f);
            } else {
                const existing = unique.get(key);
                if (f.reg && !existing.reg) {
                    unique.set(key, f);
                }
            }
        });
        return Array.from(unique.values()) as GateEvent[];
    };

    const loadData = async () => {
        if (!gate) return;
        setDateSubtitle(new Date().toLocaleDateString());

        const [arrData, depData, bayData] = await Promise.all([
            fetchCSV(CSV_ARR),
            fetchCSV(CSV_DEP),
            fetchCSV(CSV_BAY)
        ]);
        let parsedEvents: GateEvent[] = [];

        const arrHeaders = arrData.length > 0 ? arrData[0] : [];
        const depHeaders = depData.length > 0 ? depData[0] : [];

        const arrIdx = {
            code: arrHeaders.findIndex((h: string) => h.includes("航班")),
            actype: arrHeaders.findIndex((h: string) => h.includes("機型")),
            reg: arrHeaders.findIndex((h: string) => h.includes("編號") || h.includes("機號")),
            baggage: arrHeaders.findIndex((h: string) => h.includes("轉盤")),
            std: arrHeaders.findIndex((h: string) => h.includes("表定")),
            etd: arrHeaders.findIndex((h: string) => h.includes("預計")),
        };
        const depIdx = {
            code: depHeaders.findIndex((h: string) => h.includes("航班")),
            actype: depHeaders.findIndex((h: string) => h.includes("機型")),
            reg: depHeaders.findIndex((h: string) => h.includes("編號") || h.includes("機號")),
            counter: depHeaders.findIndex((h: string) => h.includes("櫃檯")),
            std: depHeaders.findIndex((h: string) => h.includes("表定")),
            etd: depHeaders.findIndex((h: string) => h.includes("預計")),
        };

        // Parse Bay_Chart for full day data
        for (let i = 1; i < bayData.length; i++) {
            const r = bayData[i];
            // [0]機坪, [1]icon, [2]flight, [3]time, [4]action(落/離), [5]status, [6]sortStr
            if (r.length < 5 || r[0] !== gate) continue;

            const action = r[4];
            const flight = r[2];
            const time = r[7] || r[3]; // scheduled time fallback to old time
            const status = r[5] || "";

            let reg = "";
            let actype = "";
            let eta = r[8] || ""; // estimated time
            let handler = "";
            let baggage = "";

            const stripSeconds = (t: string) => t ? t.split(':').slice(0, 2).join(':') : "";
            const safeTime = stripSeconds(r[3]); // old merged time for backwards compatibility matching

            // Cross-reference ARR/DEP sheets for extra metadata dynamically
            if (action === "落") {
                // 先尝试按航班号和时间匹配
                let matchRow = arrData.find((row: any) => {
                    if (arrIdx.code === -1 || row[arrIdx.code] !== flight) return false;
                    const rStd = stripSeconds(row[arrIdx.std]);
                    const rEtd = stripSeconds(row[arrIdx.etd]);
                    return rStd === safeTime || rEtd === safeTime;
                });
                
                // 如果没有匹配到，尝试只按航班号匹配
                if (!matchRow && arrIdx.code !== -1) {
                    matchRow = arrData.find((row: any) => row[arrIdx.code] === flight);
                }
                
                if (matchRow) {
                    actype = arrIdx.actype !== -1 ? (matchRow[arrIdx.actype] || "") : "";
                    reg = arrIdx.reg !== -1 ? (matchRow[arrIdx.reg] || "") : "";
                    baggage = arrIdx.baggage !== -1 ? (matchRow[arrIdx.baggage] || "") : "";
                    eta = eta || (arrIdx.etd !== -1 ? (matchRow[arrIdx.etd] || "") : "");
                }
            } else if (action === "離") {
                // 先尝试按航班号和时间匹配
                let matchRow = depData.find((row: any) => {
                    if (depIdx.code === -1 || row[depIdx.code] !== flight) return false;
                    const rStd = stripSeconds(row[depIdx.std]);
                    const rEtd = stripSeconds(row[depIdx.etd]);
                    return rStd === safeTime || rEtd === safeTime;
                });
                
                // 如果没有匹配到，尝试只按航班号匹配
                if (!matchRow && depIdx.code !== -1) {
                    matchRow = depData.find((row: any) => row[depIdx.code] === flight);
                }
                
                if (matchRow) {
                    actype = depIdx.actype !== -1 ? (matchRow[depIdx.actype] || "") : "";
                    handler = depIdx.counter !== -1 ? (matchRow[depIdx.counter] || "") : "";
                    eta = eta || (depIdx.etd !== -1 ? (matchRow[depIdx.etd] || "") : "");
                    reg = depIdx.reg !== -1 ? (matchRow[depIdx.reg] || "") : "";
                }
            }

            parsedEvents.push({
                type: action === "落" ? "ARR" : "DEP",
                flight: flight,
                reg: reg,
                actype: actype,
                counter: handler,
                baggage: baggage,
                time: stripSeconds(time),
                eta: stripSeconds(eta),
                rawTime: parseTimeMins(eta && eta.includes(":") ? eta : time),
                status: status
            });
        }

        parsedEvents = checkCodeshare(parsedEvents);
        parsedEvents.sort((a, b) => a.rawTime - b.rawTime);

        // 將所有 ARR 按時間排序（已排序），建立「某時間點之後到下一個 ARR 之前」的窗口
        // 配對規則：airline prefix 相同 + DEP 在 ARR 之後 + 兩者之間無其他未配對 ARR 停靠
        const groupedEvents: GateEvent[] = [];
        const arrEvents = parsedEvents.filter(e => e.type === "ARR");
        const depEvents = parsedEvents.filter(e => e.type === "DEP");
        const usedDeps = new Set<number>();

        for (let ai = 0; ai < arrEvents.length; ai++) {
            const arr = arrEvents[ai];
            let bestDep: GateEvent | null = null;
            let bestDepIdx = -1;

            // 找下一個「不同飛機來的 ARR」的時間點，作為配對的上限
            // （即：在下一班飛機落地之前，需找到對應的 DEP）
            const nextArrTime = ai + 1 < arrEvents.length ? arrEvents[ai + 1].rawTime : 9999;

            // 取得真實時間用於比較 (若有 ETA 則用 ETA，否則用表定)
            const getActualMins = (ev: GateEvent) => {
                return parseTimeMins(ev.eta && ev.eta.includes(":") ? ev.eta : ev.time);
            };
            const arrActual = getActualMins(arr);

            for (let i = 0; i < depEvents.length; i++) {
                if (usedDeps.has(i)) continue;
                const dep = depEvents[i];
                const depActual = getActualMins(dep);

                // DEP 必須在 ARR 之後 (真實出發時間不能早於真實抵達時間，允許極端容差 -15 分鐘)
                if (depActual < arrActual - 15) continue;

                // DEP 必須在「下一班ARR降落前」完成（否則意味中間有其他飛機佔用，不能配對）
                if (dep.rawTime >= nextArrTime) continue;

                // airline prefix 必須相同（如 TTW、APJ、CAL 等）
                const arrPrefix = arr.flight.replace(/[0-9].*/, "");
                const depPrefix = dep.flight.replace(/[0-9].*/, "");
                if (arrPrefix !== depPrefix) continue;

                // 若兩者都有機號且機號不同，絕對不是接飛！
                if (arr.reg && dep.reg && arr.reg !== dep.reg) continue;

                bestDep = dep;
                bestDepIdx = i;
                break; // 找到最早符合的 DEP
            }

            if (bestDep) {
                usedDeps.add(bestDepIdx);

                const { icao: arrIcao } = parseFlightCode(arr.flight);
                const { icao: depIcao } = parseFlightCode(bestDep.flight);

                // 相同航班號 = 過境 (Transit)，不同 = 接飛 (Turnaround)
                const isTransit = (arr.flight === bestDep.flight) || (arrIcao && depIcao && arrIcao === depIcao);

                groupedEvents.push({
                    type: isTransit ? "TRANSIT" : "TURNAROUND",
                    flight: isTransit ? arr.flight : `${arr.flight} ➔ ${bestDep.flight}`,
                    arrFlight: arr.flight,
                    depFlight: bestDep.flight,
                    reg: arr.reg || bestDep.reg, // transit uses either reg
                    actype: arr.actype || bestDep.actype,
                    counter: bestDep.counter,
                    baggage: arr.baggage,
                    time: arr.time,
                    arrTime: arr.time,
                    arrEta: arr.eta,
                    depTime: bestDep.time,
                    depEta: bestDep.eta,
                    eta: arr.eta || bestDep.eta,
                    rawTime: arr.rawTime,
                    status: `${arr.status} / ${bestDep.status}` // Combine both statuses for display if needed
                });
            } else {
                // 沒有找到對應的 DEP（可能是過夜停機或拖機）
                groupedEvents.push(arr);
            }
        }

        // 加入未配對的 DEP（航班已停靠在此，直接出發）
        for (let i = 0; i < depEvents.length; i++) {
            if (!usedDeps.has(i)) {
                groupedEvents.push(depEvents[i]);
            }
        }

        // 最終依時間重排
        groupedEvents.sort((a, b) => a.rawTime - b.rawTime);

        setEvents(groupedEvents);
        setLoading(false);
    };

    useEffect(() => {
        loadData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gate]);

    useEffect(() => {
        if (!loading && activeEventRef.current) {
            // Small delay to ensure DOM layout is complete before scrolling
            setTimeout(() => {
                activeEventRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
            }, 100);
        }
    }, [loading, events]);

    // We already have currentMins from earlier
    const nowMins = currentMins;

    // Find the event closest to now to attach the ref
    let closestIndex = 0;
    let minDiff = 9999;
    events.forEach((ev, idx) => {
        const diff = Math.abs(ev.rawTime - nowMins);
        if (diff < minDiff) {
            minDiff = diff;
            closestIndex = idx;
        }
    });

    const isRemote = ["B1R", "C5R", "D5R"].includes(gate) || parseInt(gate) >= 501;

    return (
        <div className="container-goss pb-[40px]">
            {/* Header */}
            <div className={`flex items-center mb-[30px] border-b pb-[15px] sticky top-0 bg-[#0d0d0d] z-20 pt-[10px] ${isRemote ? "border-[#f39c12]/30" : "border-[#333]"
                }`}>
                <button
                    onClick={() => router.back()}
                    className="flex items-center justify-center w-[40px] h-[40px] bg-[#222] rounded-full text-white text-[20px] mr-[15px] border-none cursor-pointer hover:bg-[#333] transition-colors shadow-md"
                >
                    ←
                </button>
                <div className="flex flex-col">
                    <div className={`text-[24px] font-black ${isRemote ? "text-[#f39c12]" : "text-[#00f260]"}`}>
                        Gate {gate || "--"}
                    </div>
                    <div className="text-[12px] text-[#888]">{dateSubtitle}</div>
                </div>
            </div>

            {loading ? (
                <div className="text-center text-[#666] mt-[50px]">載入航班資料中...</div>
            ) : events.length === 0 ? (
                <div className="text-center text-[#666] mt-[50px]">今日無航班</div>
            ) : (
                <div className="relative pl-[20px] border-l-[2px] border-[#333] ml-[10px]">
                    {events.map((ev, idx) => {
                        const isClosest = idx === closestIndex;
                        const isActive = Math.abs(ev.rawTime - nowMins) < 45; // within 45 mins

                        const detail = ev.reg || "無編號";
                        const isPaired = ev.type === "TURNAROUND" || ev.type === "TRANSIT";

                        return (
                            <div
                                key={idx}
                                className="relative mb-[30px] pl-[20px]"
                                ref={isClosest ? activeEventRef : null}
                            >
                                {/* Timeline Dot */}
                                <div
                                    className={`absolute left-[-26px] top-[15px] w-[10px] h-[10px] rounded-full border-[2px] ${isActive
                                        ? "bg-[#00f260] border-[#00f260] shadow-[0_0_10px_#00f260]"
                                        : "bg-[#0d0d0d] border-[#666]"
                                        }`}
                                />

                                <div className={`px-[12px] py-[15px] rounded-[8px] border transition-colors ${isActive ? "bg-[#1f291f] border-[#00f260]/30 shadow-[0_0_15px_rgba(0,242,96,0.1)]" : "bg-[#1e1e1e] border-[#333]"
                                    }`}>
                                    {isPaired && ev.arrFlight && ev.depFlight ? (
                                        <div className="flex flex-col gap-[8px]">
                                            {/* Top Row: Time */}
                                            <div className="flex justify-between items-center text-[12px] font-mono border-b border-[#333] pb-[8px]">
                                                <div className="text-[#4facfe]">表定{ev.arrTime} 預估{ev.arrEta || "-"}</div>
                                                <div className="text-[#666]">/</div>
                                                <div className="text-[#f1c40f]">表定{ev.depTime} 預估{ev.depEta || "-"}</div>
                                            </div>
                                            {/* Middle Row: Flight Code & Tag */}
                                            <div className="flex justify-between items-center mt-[4px]">
                                                <div className="flex items-center w-full">
                                                    {ev.type === "TRANSIT" ? (
                                                        <div className="flex-1 flex justify-center items-center">
                                                            <FlightCodeDisplay rawCode={ev.arrFlight!} />
                                                        </div>
                                                    ) : (
                                                        <>
                                                            <div className="flex-1 flex justify-center items-center">
                                                                <FlightCodeDisplay rawCode={ev.arrFlight!} />
                                                            </div>
                                                            <div className="flex-initial flex justify-center text-[#666] text-[16px] font-bold px-2">
                                                                ➔
                                                            </div>
                                                            <div className="flex-1 flex justify-center items-center">
                                                                <FlightCodeDisplay rawCode={ev.depFlight!} />
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                            {/* Bottom Row: Metadata Grid */}
                                            <div className="flex w-full mt-[8px] bg-[#111] p-[12px] rounded-[8px]">
                                                {/* Left Half: ARR Metadata */}
                                                <div className="flex-1 flex flex-col gap-[6px] items-center text-[13px] text-[#aaa] border-r border-[#333]">
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>機型</span><span className="text-[#ddd] font-mono">{ev.actype || "-"}</span>
                                                    </div>
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>轉盤</span><span className="text-[#ddd]">{ev.baggage || "-"}</span>
                                                    </div>
                                                </div>
                                                {/* Right Half: DEP Metadata */}
                                                <div className="flex-1 flex flex-col gap-[6px] items-center text-[13px] text-[#aaa] pl-[12px]">
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>機號</span><span className="text-[#ddd]">{ev.reg || "-"}</span>
                                                    </div>
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>櫃檯</span><span className="text-[#ddd]">{ev.counter || "-"}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col gap-[8px]">
                                            {/* Top Row: Time */}
                                            <div className="flex justify-between items-center text-[12px] font-mono border-b border-[#333] pb-[8px]">
                                                {ev.type === "ARR" ? (
                                                    <div className="text-[#4facfe]">表定{ev.time} 預估{ev.eta || "-"}</div>
                                                ) : (
                                                    <div className="text-[#f1c40f]">表定{ev.time} 預估{ev.eta || "-"}</div>
                                                )}
                                                {ev.type === "ARR" && (
                                                    <span className="px-[6px] py-[2px] rounded-[4px] text-[10px] bg-[rgba(79,172,254,0.2)] text-[#4facfe] font-bold ml-auto">
                                                        進場 ARR
                                                    </span>
                                                )}
                                                {ev.type === "DEP" && (
                                                    <span className="px-[6px] py-[2px] rounded-[4px] text-[10px] bg-[rgba(241,196,15,0.2)] text-[#f1c40f] font-bold ml-auto">
                                                        離場 DEP
                                                    </span>
                                                )}
                                            </div>
                                            {/* Middle Row: Flight Code */}
                                            <div className="flex mt-[4px] justify-center items-center">
                                                <div className="flex items-baseline gap-2">
                                                    <FlightCodeDisplay rawCode={ev.flight} />
                                                </div>
                                            </div>
                                            {/* Bottom Row: Metadata Grid (Aligned like Turnaround) */}
                                            <div className="flex w-full mt-[8px] bg-[#111] p-[12px] rounded-[8px]">
                                                {/* Left Half: ARR Metadata (Empty if DEP) */}
                                                <div className="flex-1 flex flex-col gap-[6px] items-center text-[13px] text-[#aaa] border-r border-[#333]">
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>機型</span><span className="text-[#ddd] font-mono">{ev.actype || "-"}</span>
                                                    </div>
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>轉盤</span><span className="text-[#ddd]">{ev.type === "ARR" ? ev.baggage || "-" : "-"}</span>
                                                    </div>
                                                </div>
                                                {/* Right Half: DEP Metadata (Empty if ARR) */}
                                                <div className="flex-1 flex flex-col gap-[6px] items-center text-[13px] text-[#aaa] pl-[12px]">
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>機號</span><span className="text-[#ddd]">{ev.reg || "-"}</span>
                                                    </div>
                                                    <div className="w-[100px] flex justify-between">
                                                        <span>櫃檯</span><span className="text-[#ddd]">{ev.type === "DEP" ? ev.counter || "-" : "-"}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            {/* Status Row */}
                                            <div className="text-center text-[#ddd] text-[12px] bg-[#222] py-[4px] rounded-[4px] mt-[4px]">
                                                動態: {ev.status || "-"}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
