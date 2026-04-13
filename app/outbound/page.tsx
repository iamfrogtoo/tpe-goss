"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { parseFlightCode, FlightCodeDisplay } from "@/utils/flightFormatter";

interface OutboundFlight {
    code: string;
    icao: string;
    time: string;
    gate: string;
    statusText: string;
    terminal: string;
    facility: string;
    aircraftType: string;
    sortTime: number;
}

export default function OutboundFlights() {
    const [flights, setFlights] = useState<OutboundFlight[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(true);

    const parseDateTime = (t: string) => {
        try {
            const today = new Date();
            const timeParts = t.split(':').map(Number);
            const [hour, min, sec = 0] = timeParts;
            if (isNaN(hour) || isNaN(min)) return 9999999999999;
            return new Date(today.getFullYear(), today.getMonth(), today.getDate(), hour, min, sec).getTime();
        } catch {
            return 9999999999999;
        }
    };

    const fetchOutboundData = async () => {
        try {
            const res = await fetch(`/api/schedule-data?type=dep&t=${Date.now()}`);
            if (!res.ok) throw new Error('Failed to fetch outbound data');
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
            const outboundData = await fetchOutboundData();
            
            let allData: OutboundFlight[] = [];

            // 將資料庫資料轉換為 OutboundFlight 格式
            outboundData.forEach((flight: any) => {
                const { icao, iata } = parseFlightCode(flight.code);
                
                allData.push({
                    code: iata || icao,
                    icao,
                    time: flight.time,
                    gate: flight.gate,
                    statusText: flight.statusText,
                    terminal: flight.terminal,
                    facility: flight.facility,
                    aircraftType: flight.aircraftType || "",
                    sortTime: parseDateTime(flight.time),
                });
            });

            setFlights(allData);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching outbound data:", error);
            setLoading(false);
        }
    };

    const filteredFlights = useMemo(() => {
        if (!searchTerm.trim()) {
            return flights.sort((a, b) => a.sortTime - b.sortTime);
        }
        
        const term = searchTerm.toLowerCase();
        const filtered = flights.filter(f => 
            f.code.toLowerCase().includes(term) ||
            f.gate.toLowerCase().includes(term) ||
            f.facility.toLowerCase().includes(term)
        );
        
        return filtered.sort((a, b) => a.sortTime - b.sortTime);
    }, [flights, searchTerm]);

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
                    <h1 className="text-3xl font-bold text-gray-900">出境航班</h1>
                    <p className="text-gray-600 mt-2">{new Date().toLocaleDateString()}</p>
                </div>

                {/* 搜尋框 */}
                <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
                    <input
                        type="text"
                        placeholder="搜尋航班號、登機門、航空公司..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="mt-2 text-gray-600">載入中...</p>
                    </div>
                ) : filteredFlights.length === 0 ? (
                    <div className="text-center py-8">
                        <p className="text-gray-500">
                            {searchTerm ? '找不到符合搜尋條件的出境航班' : '今日無出境航班'}
                        </p>
                    </div>
                ) : (
                    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                        <div className="grid grid-cols-12 gap-4 p-4 bg-gray-50 border-b font-medium text-gray-700">
                            <div className="col-span-2">時間</div>
                            <div className="col-span-3">航班</div>
                            <div className="col-span-1">登機門</div>
                            <div className="col-span-2">狀態</div>
                            <div className="col-span-2">航空公司</div>
                            <div className="col-span-2">機型</div>
                        </div>
                        
                        <div className="divide-y">
                            {filteredFlights.map((flight, index) => (
                                <div key={`${flight.code}-${flight.time}-${index}`} className="grid grid-cols-12 gap-4 p-4 hover:bg-gray-50 transition-colors">
                                    <div className="col-span-2 font-medium text-gray-900">{flight.time}</div>
                                    <div className="col-span-3">
                                        <FlightCodeDisplay rawCode={flight.code} />
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
                                    <div className="col-span-2 text-gray-600">{flight.facility || "-"}</div>
                                    <div className="col-span-2 text-gray-600">{flight.aircraftType || "-"}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 統計資訊 */}
                <div className="mt-6 bg-white rounded-lg shadow-sm border p-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                            <div className="text-2xl font-bold text-blue-600">{flights.length}</div>
                            <div className="text-sm text-gray-600">總航班數</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-green-600">
                                {flights.filter(f => f.statusText === '準時' || f.statusText === '登機中').length}
                            </div>
                            <div className="text-sm text-gray-600">準時航班</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-red-600">
                                {flights.filter(f => f.statusText === '延誤').length}
                            </div>
                            <div className="text-sm text-gray-600">延誤航班</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}