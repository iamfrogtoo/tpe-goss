"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FlightCodeDisplay } from "@/utils/flightFormatter";

// 数据来源配置
// 使用 jsdelivr CDN 从 GitHub 获取数据，无需 ngrok
const API_URL = "https://cdn.jsdelivr.net/gh/iamfrogtoo/tpe-goss@main/public/live_data.json";

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
  const [dataSource, setDataSource] = useState("模擬數據");

  // 模拟数据 - 作为 fallback
  const getMockFlights = (): Flight[] => {
    return [
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
        statusText: "進場中",
        statusClass: "",
        isRemote: false
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
        statusText: "即將落地",
        statusClass: "",
        isRemote: false
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
        statusText: "已落地",
        statusClass: "",
        isRemote: true
      }
    ];
  };

  const processFlightData = (flightData: any): Flight => {
    let statusText = "進場中";
    const alt = parseInt(flightData.alt) || 0;
    
    if (alt === 0) {
      statusText = "已落地";
    } else if (alt < 1000) {
      statusText = "即將落地";
    }

    return {
      code: flightData.code || flightData.flight_no || "UNKNOWN",
      actype: flightData.actype || "",
      reg: flightData.reg || "",
      terminal: flightData.terminal || "-",
      gate: flightData.gate || "-",
      baggage: flightData.baggage || "-",
      sta: flightData.scheduled_time || flightData.sta || "",
      eta: flightData.actual_time || flightData.eta || "",
      alt: flightData.alt || "0",
      statusText,
      statusClass: "",
      isRemote: flightData.gate ? (flightData.gate.startsWith('5') || flightData.gate.startsWith('6')) : false
    };
  };

  const fetchData = async () => {
    try {
      let parsedFlights: Flight[] = [];
      let source = "模擬數據";

      // 尝试从 API 获取数据
      if (API_URL) {
        try {
          const res = await fetch(`${API_URL}?t=${Date.now()}`);
          if (res.ok) {
            const data = await res.json();
            if (data.flights && data.flights.length > 0) {
              parsedFlights = data.flights.map(processFlightData);
              source = "即時數據";
            }
          }
        } catch (apiError) {
          console.log("API 獲取失敗，使用模擬數據:", apiError);
        }
      }

      // 如果没有从 API 获取到数据，使用模拟数据
      if (parsedFlights.length === 0) {
        parsedFlights = getMockFlights();
      }

      // 处理状态类
      parsedFlights = parsedFlights.map(flight => {
        let statusClass = "border-l-[5px] border-[#444] bg-[#1e1e1e]";
        if (flight.statusText.includes("即將落地")) {
          statusClass = "border-l-[5px] border-[#ff4b4b] bg-gradient-to-r from-[rgba(255,75,75,0.1)] to-transparent";
        } else if (flight.statusText.includes("進場中")) {
          statusClass = "border-l-[5px] border-[#f1c40f] bg-gradient-to-r from-[rgba(241,196,15,0.1)] to-transparent";
        } else if (flight.statusText.includes("已落地")) {
          statusClass = "border-l-[5px] border-[#4facfe] bg-[#1e1e1e]/80";
        }

        return {
          ...flight,
          statusClass
        };
      });

      // 按高度排序（从低到高）
      const sortedFlights = [...parsedFlights].sort((a, b) => {
        const altA = parseInt(a.alt) || 0;
        const altB = parseInt(b.alt) || 0;
        return altA - altB;
      });

      setFlights(sortedFlights);
      setDataSource(source);
      setLastUpdate(`更新: ${new Date().toLocaleTimeString()} (${sortedFlights.length}架) - ${source}`);
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
