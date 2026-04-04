"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FlightCodeDisplay } from "@/utils/flightFormatter";

// TPE GOSS Outbound Sheet CSV URL
const CSV_URL =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=2059190189&single=true&output=csv";

interface Flight {
    code: string;
    actype: string;
    reg: string;
    terminal: string;
    gate: string;
    counter: string;
    std: string;
    etd: string;
    statusText: string;
    handler: string;
    statusClass: string;
    handlerStyles: { border: string; bg: string; text: string };
    isRemote: boolean;
}

export default function Outbound() {
    const [flights, setFlights] = useState<Flight[]>([]);
    const [lastUpdate, setLastUpdate] = useState("連線中...");

    const fetchData = async () => {
        try {
            const res = await fetch(`${CSV_URL}&t=${Date.now()}`);
            // 直接获取原始字节数据
            const buffer = await res.arrayBuffer();
            // 尝试使用UTF-8编码解码（主要编码）
            let decodedText = '';
            try {
                const decoder = new TextDecoder('utf-8');
                decodedText = decoder.decode(buffer);
            } catch (e) {
                console.error('使用UTF-8编码解码失败:', e);
                // 如果UTF-8解码失败，尝试其他编码
                const encodings = ['gb2312', 'big5'];
                for (const encoding of encodings) {
                    try {
                        const decoder = new TextDecoder(encoding);
                        decodedText = decoder.decode(buffer);
                        break;
                    } catch (e) {
                        console.error(`使用${encoding}编码解码失败:`, e);
                    }
                }
            }
            
            // 状态文本映射为中文
            const statusMap: { [key: string]: string } = {
                'ON TIME': '準時',
                'SCHEDULE CHANGE': '時間更改',
                'DELAYED': '延誤',
                'CANCELLED': '取消',
                'BOARDING': '登機中',
                'DEPARTED': '已起飛'
            };
            
            // 处理状态文本的函数
            const processStatus = (status: string): string => {
                // 输出原始状态文本用于调试
                console.log('原始状态文本:', status);
                
                // 直接检查状态文本是否包含特定的英文状态关键词
                if (status.includes('ON TIME')) {
                    console.log('匹配到 ON TIME，返回 準時');
                    return '準時';
                } else if (status.includes('SCHEDULE CHANGE')) {
                    console.log('匹配到 SCHEDULE CHANGE，返回 時間更改');
                    return '時間更改';
                } else if (status.includes('DELAYED')) {
                    console.log('匹配到 DELAYED，返回 延誤');
                    return '延誤';
                } else if (status.includes('CANCELLED')) {
                    console.log('匹配到 CANCELLED，返回 取消');
                    return '取消';
                } else if (status.includes('BOARDING')) {
                    console.log('匹配到 BOARDING，返回 登機中');
                    return '登機中';
                } else if (status.includes('DEPARTED')) {
                    console.log('匹配到 DEPARTED，返回 已起飛');
                    return '已起飛';
                }
                
                console.log('未匹配到状态，返回原始状态:', status);
                return status;
            };
            
            const rows = decodedText
                .replace(/\r/g, "")
                .split("\n")
                .filter((r) => r.trim() !== "");

            if (rows.length <= 1) return;
            if (rows.length === 2 && rows[1].includes("無出境航班")) {
                setFlights([]);
                setLastUpdate(`更新: ${new Date().toLocaleTimeString()} (0架)`);
                return;
            }

            // [Dynamic header parsing]
            const headers = rows[0].split(",").map((x) => x.replace(/"/g, "").trim());
            console.log('Headers:', headers);
            const idxCode = headers.findIndex(h => h.includes("航班"));
            const idxType = headers.findIndex(h => h.includes("機型"));
            const idxReg = headers.findIndex(h => h.includes("編號") || h.includes("機號"));
            const idxTerminal = headers.findIndex(h => h.includes("航廈"));
            const idxGate = headers.findIndex(h => h.includes("機坪"));
            const idxCounter = headers.findIndex(h => h.includes("櫃檯"));
            const idxStd = headers.findIndex(h => h.includes("表定"));
            const idxEtd = headers.findIndex(h => h.includes("預計"));
            const idxStatus = headers.findIndex(h => h.includes("狀態"));
            console.log('idxStatus:', idxStatus);

            const parsedFlights: Flight[] = [];
            const now = new Date();

            for (let i = 1; i < rows.length; i++) {
                const cols = rows[i].split(",").map((x) => (x ? x.replace(/"/g, "").trim() : ""));
                if (idxCode === -1 || !cols[idxCode] || cols[idxCode].includes("航班")) continue;

                // ETD countdown logic based on ETD (or STD if ETD is missing)
                let statusClass = "border-b border-[#333] bg-[#1e1e1e]";
                const targetTime = cols[idxEtd] || cols[idxStd];
                const [h, m] = targetTime ? targetTime.split(":") : ["", ""];

                if (h && m) {
                    const etdObj = new Date();
                    etdObj.setHours(parseInt(h, 10), parseInt(m, 10), 0);
                    const diff = (etdObj.getTime() - now.getTime()) / 60000;

                    if (diff < 0) {
                        statusClass = "border-b border-[#333] bg-[#1a1a1a] opacity-60"; // Departed
                    } else if (diff <= 30) {
                        statusClass = "border-b border-[#333] bg-gradient-to-r from-[rgba(241,196,15,0.1)] to-transparent border-l-[4px] border-l-[#f1c40f]"; // Urgent
                    }
                }

                const handler = cols[idxCounter] || "-";
                let handlerStyles = { border: "", bg: "#333", text: "#fff" };

                const rawGate = cols[idxGate] || "";
                const isRemote = rawGate ? rawGate.endsWith("R") || parseInt(rawGate, 10) > 500 : false;

                parsedFlights.push({
                    code: cols[idxCode],
                    actype: cols[idxType] || "",
                    reg: cols[idxReg] || "",
                    terminal: cols[idxTerminal] || "-",
                    gate: rawGate || "-",
                    counter: handler,
                    std: cols[idxStd] || "",
                    etd: cols[idxEtd] || "",
                    statusText: processStatus(cols[idxStatus] || ""),

                    handler,
                    statusClass,
                    handlerStyles,
                    isRemote,
                });
            }

            setFlights(parsedFlights);
            setLastUpdate(`更新: ${new Date().toLocaleTimeString()} (${parsedFlights.length}架)`);
        } catch (error) {
            console.error(error);
            setLastUpdate("連線失敗");
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="container-goss">
            <div className="text-center text-[11px] text-[#666] mb-[10px]">{lastUpdate}</div>

            {flights.length === 0 && lastUpdate !== "連線中..." ? (
                <div className="text-center text-[#666] mt-[50px] text-[14px]">無離場航班</div>
            ) : (
                <div className="flex flex-col gap-[10px]">
                    {flights.map((f, idx) => (
                        <div
                            key={idx}
                            className={`rounded-[10px] p-[15px] flex justify-between items-center relative ${f.statusClass} ${
                                // Inherit handler border if not overridden by urgent left border
                                !f.statusClass.includes("border-l-") ? f.handlerStyles.border : ""
                                }`}
                        >
                            {/* Handler Tag - Removed to avoid duplicate counter display */}

                            {/* Left Column: Flight Info */}
                            <div className="w-[35%] flex flex-col justify-center">
                                <div className="flex items-baseline gap-1">
                                    <FlightCodeDisplay rawCode={f.code} />
                                </div>
                                <div className="flex flex-wrap items-center gap-[6px] mt-1 w-full">
                                    {f.actype && <span className="text-[12px] text-[#888] font-mono whitespace-nowrap overflow-hidden text-ellipsis">{f.actype}</span>}
                                    {f.reg && <span className="bg-[#333] px-[4px] py-[2px] rounded text-[10px] text-[#ddd] font-mono">{f.reg}</span>}
                                </div>
                                <span className="text-[14px] font-bold text-[#ffca28] mt-1 block">ETD {f.etd ? f.etd.slice(0, 5) : f.std.slice(0, 5)}</span>
                            </div>

                            {/* Center Column: Status & Counter */}
                            <div className="w-[30%] text-center flex flex-col justify-center items-center">
                                <span className="text-[10px] bg-[#333] px-[8px] py-[3px] rounded-[10px] mx-auto text-[#ccc] flex gap-2">
                                    {f.terminal !== "-" && <span>T{f.terminal}</span>}
                                    {f.counter !== "-" && <span className="text-[#00f260]">櫃檯 {f.counter}</span>}
                                </span>
                                <span className="text-[12px] text-[#aaa] mt-2 block px-[8px] py-[3px] bg-[#333] rounded-[4px] min-w-[60px]">
                                    {f.statusText}
                                </span>
                            </div>

                            {/* Right Column: Gate */}
                            <div className="w-[35%] text-right flex flex-col justify-center items-end">
                                {f.gate ? (
                                    <Link
                                        href={`/gate/${f.gate}`}
                                        className={`flex flex-col items-end no-underline ${f.isRemote ? "text-[#f1c40f]" : "text-[#00f260]"}`}
                                    >
                                        {f.gate.includes('/') ? (
                                            <>
                                                <span className="text-[28px] font-bold leading-none">{f.gate.split('/')[0]}</span>
                                                <span className="text-[16px] font-bold leading-none mt-1">{f.gate.split('/')[1]}</span>
                                            </>
                                        ) : (
                                            <span className="text-[28px] font-bold leading-none">{f.gate}</span>
                                        )}
                                    </Link>
                                ) : (
                                    <span className="text-[28px] font-bold leading-none text-[#00f260]">-</span>
                                )}
                                <span className="text-[10px] text-[#666] mt-1">GATE</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
