"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { parseFlightCode, FlightCodeDisplay } from "@/utils/flightFormatter";

interface GateEvent {
    type: "ARR" | "DEP" | "TRANSIT" | "TURNAROUND";
    flight: string;
    status?: string;
    arrFlight?: string;
    depFlight?: string;
    reg?: string;
    actype?: string;
    counter?: string;
    baggage?: string;
    time: string;
    eta?: string;
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

    const activeEventRef = useRef<HTMLDivElement>(null);

    const fetchGateData = async (gate: string) => {
        try {
            const res = await fetch(`/api/gate-data?gate=${gate}&t=${Date.now()}`);
            if (!res.ok) throw new Error('Failed to fetch gate data');
            const data = await res.json();
            return data.events || [];
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

        const gateEvents = await fetchGateData(gate);
        let parsedEvents: GateEvent[] = [];

        // 將資料庫資料轉換為 GateEvent 格式
        gateEvents.forEach((event: any) => {
            const timeMins = parseTimeMins(event.scheduledTime);
            
            if (event.direction === 'A') {
                // 入境航班
                parsedEvents.push({
                    type: "ARR",
                    flight: event.code,
                    status: event.status,
                    reg: event.aircraftType || '',
                    actype: event.aircraftType,
                    baggage: event.baggageCarousel,
                    time: event.scheduledTime,
                    eta: event.actualTime,
                    rawTime: timeMins
                });
            } else if (event.direction === 'D') {
                // 出境航班
                parsedEvents.push({
                    type: "DEP",
                    flight: event.code,
                    status: event.status,
                    reg: event.aircraftType || '',
                    actype: event.aircraftType,
                    counter: event.checkinCounter,
                    time: event.scheduledTime,
                    eta: event.actualTime,
                    rawTime: timeMins
                });
            }
        });

        // 去重處理
        const dedupedEvents = checkCodeshare(parsedEvents);
        
        // 按時間排序
        const sortedEvents = dedupedEvents.sort((a, b) => a.rawTime - b.rawTime);
        
        setEvents(sortedEvents);
        setLoading(false);
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // 每30秒更新
        return () => clearInterval(interval);
    }, [gate]);

    useEffect(() => {
        if (activeEventRef.current) {
            activeEventRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [events]);

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

    const getTypeLabel = (type: string) => {
        switch (type) {
            case 'ARR': return '入境';
            case 'DEP': return '出境';
            case 'TRANSIT': return '過境';
            case 'TURNAROUND': return '轉機';
            default: return type;
        }
    };

    if (!gate) {
        return <div className="p-4 text-red-500">錯誤：未指定登機門</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">登機門 {gate}</h1>
                    <p className="text-gray-600 mt-2">{dateSubtitle}</p>
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="mt-2 text-gray-600">載入中...</p>
                    </div>
                ) : events.length === 0 ? (
                    <div className="text-center py-8">
                        <p className="text-gray-500">今日無航班安排</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {events.map((event, index) => (
                            <div
                                key={`${event.flight}-${event.time}-${index}`}
                                ref={event.rawTime <= currentMins + 30 && event.rawTime >= currentMins - 60 ? activeEventRef : null}
                                className={`bg-white rounded-lg shadow-sm border p-4 transition-all duration-200 ${
                                    event.rawTime <= currentMins + 30 && event.rawTime >= currentMins - 60 
                                        ? 'border-blue-500 ring-2 ring-blue-100' 
                                        : 'border-gray-200'
                                }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center space-x-3">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(event.status || '')}`}>
                                            {getTypeLabel(event.type)}
                                        </span>
                                        <FlightCodeDisplay rawCode={event.flight} />
                                        {event.status && (
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(event.status)}`}>
                                                {event.status}
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-right">
                                        <div className="text-lg font-semibold text-gray-900">{event.time}</div>
                                        {event.eta && event.eta !== event.time && (
                                            <div className="text-sm text-gray-500">預計: {event.eta}</div>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                    <div>
                                        {event.actype && <div>機型: {event.actype}</div>}
                                        {event.reg && <div>機尾號: {event.reg}</div>}
                                    </div>
                                    <div>
                                        {event.type === 'ARR' && event.baggage && <div>行李轉盤: {event.baggage}</div>}
                                        {event.type === 'DEP' && event.counter && <div>報到櫃檯: {event.counter}</div>}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}