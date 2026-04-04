"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FlightCodeDisplay } from "@/utils/flightFormatter";

interface Flight {
  code: string;
  actype: string;
  reg: string;
  terminal: string;
  gate: string;
  baggage: string;
  sta: string;
  eta: string;
  alt: string;
  statusText: string;
  statusClass: string;
  isRemote: boolean;
}

export default function Home() {
  const [flights, setFlights] = useState<Flight[]>([]);
  const [lastUpdate, setLastUpdate] = useState("連線中...");

  const fetchData = async () => {
    try {
      // 模擬從後端 API 获取数据
      // 实际项目中，这里应该调用后端 API 获取 goss_v4.db 中的数据
      
      // 模拟数据 - 使用桃园机场真实机坪和正确的入境航班信息
      // 注意：这是模拟数据，后续将整合 goss_v4.db 中的实时数据
      const mockFlights = [
        {
          code: "CI101",
          actype: "A330-300",
          reg: "B-18301",
          terminal: "1",
          gate: "A5",
          baggage: "5",
          sta: "10:30",
          eta: "10:25",
          alt: "5280",
          statusText: "進場中"
        },
        {
          code: "EVA221",
          actype: "B777-300ER",
          reg: "B-16708",
          terminal: "2",
          gate: "B7",
          baggage: "12",
          sta: "11:15",
          eta: "11:10",
          alt: "3450",
          statusText: "即將落地"
        },
        {
          code: "CA185",
          actype: "B737-800",
          reg: "B-5488",
          terminal: "1",
          gate: "505",
          baggage: "8",
          sta: "12:00",
          eta: "12:00",
          alt: "0",
          statusText: "已落地"
        },
        {
          code: "ANA879",
          actype: "B787-9",
          reg: "JA832A",
          terminal: "2",
          gate: "D12",
          baggage: "15",
          sta: "12:45",
          eta: "12:50",
          alt: "8760",
          statusText: "進場中"
        },
        {
          code: "JAL809",
          actype: "B767-300ER",
          reg: "JA606J",
          terminal: "2",
          gate: "610",
          baggage: "10",
          sta: "13:30",
          eta: "13:25",
          alt: "6230",
          statusText: "進場中"
        }
      ];

      // 处理状态类和远程机坪判断
      const parsedFlights = mockFlights.map(flight => {
        let statusClass = "border-l-[5px] border-[#444] bg-[#1e1e1e]"; // default
        if (flight.statusText.includes("即將落地")) {
          statusClass = "border-l-[5px] border-[#ff4b4b] bg-gradient-to-r from-[rgba(255,75,75,0.1)] to-transparent";
        } else if (flight.statusText.includes("進場中")) {
          statusClass = "border-l-[5px] border-[#f1c40f] bg-gradient-to-r from-[rgba(241,196,15,0.1)] to-transparent";
        } else if (flight.statusText.includes("已落地")) {
          statusClass = "border-l-[5px] border-[#4facfe] bg-[#1e1e1e]/80";
        }

        // 正确判断远程机坪（500和600系列）
        const isRemote = flight.gate ? 
          (flight.gate.startsWith('5') || flight.gate.startsWith('6')) : 
          false;

        return {
          ...flight,
          statusClass,
          isRemote
        };
      });

      // 按高度排序（从低到高，符合航班进近逻辑）
      const sortedFlights = [...parsedFlights].sort((a, b) => {
        const altA = parseInt(a.alt) || 0;
        const altB = parseInt(b.alt) || 0;
        return altA - altB;
      });

      setFlights(sortedFlights);
      setLastUpdate(`更新: ${new Date().toLocaleTimeString()} (${sortedFlights.length}架)`);
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
        <div className="text-center text-[#666] mt-[50px] text-[14px]">無進場航班</div>
      ) : (
        <div className="flex flex-col gap-[10px]">
          {flights.map((f, idx) => (
            <div
              key={idx}
              className={`rounded-[10px] p-[15px] flex justify-between items-center shadow-md relative ${f.statusClass}`}
            >
              {/* Left Column: Flight Info */}
              <div className="w-[35%] flex flex-col justify-center">
                <div className="flex items-baseline gap-1">
                  <FlightCodeDisplay rawCode={f.code} />
                </div>
                {f.reg && <span className="text-[12px] text-[#888] font-mono mt-1">{f.reg}</span>}
                {f.actype && <span className="text-[12px] text-[#888] font-mono whitespace-nowrap overflow-hidden text-ellipsis w-full block">{f.actype}</span>}
                <span className="text-[10px] text-[#aaa] mt-1 pr-2">STA: {f.sta.slice(0, 5)} {f.eta && `| ETA: ${f.eta.slice(0, 5)}`}</span>
              </div>

              {/* Center Column: Altitude & Bags */}
              <div className="w-[30%] text-center flex flex-col justify-center items-center">
                <span className="text-[22px] font-bold text-white font-mono">{f.alt}</span>
                <span className="text-[10px] bg-[#333] px-[8px] py-[3px] rounded-[10px] mx-auto mt-1 text-[#ccc] flex gap-2">
                  {f.terminal !== "-" && <span>T{f.terminal}</span>}
                  {f.baggage !== "-" && <span className="text-[#00f260]">轉盤 {f.baggage}</span>}
                </span>
                <span className="text-[10px] text-[#666] mt-1">{f.statusText}</span>
              </div>

              {/* Right Column: Gate */}
              <div className="w-[35%] text-right flex flex-col justify-center items-end">
                {f.gate ? (
                  <Link
                    href={`/gate/${f.gate}`}
                    className={`text-[30px] font-bold leading-none no-underline ${f.isRemote ? "text-[#f1c40f]" : "text-[#00f260]"
                      }`}
                  >
                    {f.gate}
                  </Link>
                ) : (
                  <span className="text-[30px] font-bold leading-none text-[#00f260]">-</span>
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
