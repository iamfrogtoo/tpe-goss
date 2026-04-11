"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { parseFlightCode, FlightCodeDisplay } from "@/utils/flightFormatter";

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
    const [typeFilter, setTypeFilter] = useState<"ARR" | "DEP">("ARR");
    const [loading, setLoading] = useState(true);

    const parseDateTime = (d: string, t: string) => {
        try {
            const [month, day] = d.split('/').map(Number);
            const timeParts = t.split(':').map(Number);
            const [hour, min, sec = 0] = timeParts;
            if (isNaN(month) || isNaN(day) || isNaN(hour) || isNaN(min)) return 9999999999999;
            let year = new Date().getFullYear();
            if (d.startsWith("12") && new Date().getMonth() === 0) year--;
            else if (d.startsWith("01") && new Date().getMonth() === 11) year++;
            return new Date(year, month - 1, day, hour, min, sec).getTime();
        } catch {
            return 9999999999999;
        }
    };

    const fetchScheduleData = async (type: "arr" | "dep" | "all") => {
        try {
            const res = await fetch(`/api/schedule-data?type=${type}&t=${Date.now()}`);
            if (!res.ok) throw new Error('Failed to fetch schedule data');
            const data = await res.json();
            return data.flights || [];
        } catch (e) {
            console.error(e);
            return [];
        }
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            const scheduleData = await fetchScheduleData("all");
            
            let allData: ScheduleFlight[] = [];

            // 將資料庫資料轉換為 ScheduleFlight 格式
            scheduleData.forEach((flight: any) => {
                const { icao, iata } = parseFlightCode(flight.code);
                const today = new Date();
                const displayDate = `${today.getMonth() + 1}/${today.getDate()}`;
                
                allData.push({
                    type: flight.type,
                    displayDate: displayDate,
                    code: iata || icao,
                    icao,
                    time: flight.time,
                    gate: flight.gate,
                    statusText: flight.statusText,
                    terminal: flight.terminal,
                    facility: flight.facility,
                    actype: flight.aircraftType || "",
                    reg: "", // 資料庫中可能沒有機尾號欄位
                    std: flight.time, // 使用 scheduled time 作為 std
                    etd: "", // 資料庫中可能沒有預計時間
                    sortTime: parseDateTime(displayDate, flight.time),
                });
            });

            setFlights(allData);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching schedule data:", error);
            setLoading(false);
        }
    };

    const filteredFlights = useMemo(() => {
        let filtered = flights.filter(f => f.type === typeFilter);
        
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(f => 
                f.code.toLowerCase().includes(term) ||
                f.gate.toLowerCase().includes(term) ||
                f.facility.toLowerCase().includes(term)
            );
        }
        
        return filtered.sort((a, b) => a.sortTime - b.sortTime);
    }, [flights, typeFilter, searchTerm]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // 每分鐘更新
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case '已抵達':
            case '準時':
                return 'bg-green-100 text-green-800';
            case '延誤':
                return 'bg-red-100 text-red-800';
            case '登機中':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-6xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">航班時刻表</h1>
                    <p className="text-gray-600 mt-2">{new Date().toLocaleDateString()}</p>
                </div>

                {/* 篩選器 */}
                <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setTypeFilter("ARR")}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    typeFilter === "ARR" 
                                        ? 'bg-blue-500 text-white' 
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                入境航班
                            </button>
                            <button
                                onClick={() => setTypeFilter("DEP")}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    typeFilter === "DEP" 
                                        ? 'bg-blue-500 text-white' 
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                出境航班
                            </button>
                        </div>
                        
                        <div className="flex-1">
                            <input
                                type="text"
                                placeholder="搜尋航班號、登機門、航空公司..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="mt-2 text-gray-600">載入中...</p>
                    </div>
                ) : filteredFlights.length === 0 ? (
                    <div className="text-center py-8">
                        <p className="text-gray-500">
                            {searchTerm ? '找不到符合搜尋條件的航班' : '今日無航班安排'}
                        </p>
                    </div>
                ) : (
                    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                        <div className="grid grid-cols-12 gap-4 p-4 bg-gray-50 border-b font-medium text-gray-700">
                            <div className="col-span-2">時間</div>
                            <div className="col-span-2">航班</div>
                            <div className="col-span-2">目的地/出發地</div>
                            <div className="col-span-1">登機門</div>
                            <div className="col-span-2">狀態</div>
                            <div className="col-span-2">機型</div>
                            <div className="col-span-1">航廈</div>
                        </div>
                        
                        <div className="divide-y">
                            {filteredFlights.map((flight, index) => (
                                <div key={`${flight.code}-${flight.time}-${index}`} className="grid grid-cols-12 gap-4 p-4 hover:bg-gray-50 transition-colors">
                                    <div className="col-span-2 font-medium text-gray-900">{flight.time}</div>
                                    <div className="col-span-2">
                                        <FlightCodeDisplay code={flight.code} />
                                    </div>
                                    <div className="col-span-2 text-gray-600">
                                        {flight.type === "ARR" ? "抵達" : "出發"}
                                    </div>
                                    <div className="col-span-1">
                                        {flight.gate ? (
                                            <Link 
                                                href={`/gate/${flight.gate}`}
                                                className="text-blue-600 hover:text-blue-800 hover:underline"
                                            >
                                                {flight.gate}
                                            </Link>
                                        ) : (
                                            <span className="text-gray-400">-</span>
                                        )}
                                    </div>
                                    <div className="col-span-2">
                                        {flight.statusText && (
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(flight.statusText)}`}>
                                                {flight.statusText}
                                            </span>
                                        )}
                                    </div>
                                    <div className="col-span-2 text-gray-600">{flight.actype || "-"}</div>
                                    <div className="col-span-1 text-gray-600">{flight.terminal}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}