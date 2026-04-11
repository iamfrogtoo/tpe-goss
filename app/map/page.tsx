"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface GateInfo {
    gate: string;
    terminal: string;
    flight: string;
    status: string;
    scheduledTime: string;
    actualTime: string;
    airline: string;
    aircraftType: string;
}

export default function AirportMap() {
    const [arrivalFlights, setArrivalFlights] = useState<GateInfo[]>([]);
    const [departureFlights, setDepartureFlights] = useState<GateInfo[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchMapData = async () => {
        try {
            const res = await fetch(`/api/map-data?t=${Date.now()}`);
            if (!res.ok) throw new Error('Failed to fetch map data');
            const data = await res.json();
            return data;
        } catch (e) {
            console.error(e);
            return { arrivals: [], departures: [] };
        }
    };

    const loadData = async () => {
        try {
            setLoading(true);
            const mapData = await fetchMapData();
            
            setArrivalFlights(mapData.arrivals || []);
            setDepartureFlights(mapData.departures || []);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching map data:", error);
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 60000); // 每分鐘更新
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

    const getGateStatus = (gate: string, flights: GateInfo[]) => {
        const gateFlights = flights.filter(f => f.gate === gate);
        if (gateFlights.length === 0) return 'empty';
        
        const hasActiveFlight = gateFlights.some(f => 
            f.status === '登機中' || f.status === '已抵達'
        );
        
        return hasActiveFlight ? 'active' : 'scheduled';
    };

    const getGateColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-500';
            case 'scheduled': return 'bg-blue-500';
            default: return 'bg-gray-300';
        }
    };

    // 航廈 A 登機門
    const terminalAGates = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'];
    // 航廈 B 登機門
    const terminalBGates = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10'];

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-6xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">桃園國際機場地圖</h1>
                    <p className="text-gray-600 mt-2">{new Date().toLocaleDateString()}</p>
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="mt-2 text-gray-600">載入中...</p>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* 航廈 A */}
                        <div className="bg-white rounded-lg shadow-sm border p-6">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">第一航廈 (Terminal 1)</h2>
                            <div className="grid grid-cols-5 gap-4">
                                {terminalAGates.map(gate => {
                                    const status = getGateStatus(gate, [...arrivalFlights, ...departureFlights]);
                                    const gateFlights = [...arrivalFlights, ...departureFlights].filter(f => f.gate === gate);
                                    
                                    return (
                                        <Link 
                                            key={gate}
                                            href={`/gate/${gate}`}
                                            className={`block p-4 rounded-lg text-center text-white font-medium transition-all hover:scale-105 ${getGateColor(status)}`}
                                        >
                                            <div className="text-lg font-bold">{gate}</div>
                                            {gateFlights.length > 0 && (
                                                <div className="text-xs mt-1 opacity-90">
                                                    {gateFlights[0].flight}
                                                </div>
                                            )}
                                            <div className="text-xs mt-1 opacity-75">
                                                {status === 'active' ? '使用中' : status === 'scheduled' ? '已安排' : '空閒'}
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        {/* 航廈 B */}
                        <div className="bg-white rounded-lg shadow-sm border p-6">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">第二航廈 (Terminal 2)</h2>
                            <div className="grid grid-cols-5 gap-4">
                                {terminalBGates.map(gate => {
                                    const status = getGateStatus(gate, [...arrivalFlights, ...departureFlights]);
                                    const gateFlights = [...arrivalFlights, ...departureFlights].filter(f => f.gate === gate);
                                    
                                    return (
                                        <Link 
                                            key={gate}
                                            href={`/gate/${gate}`}
                                            className={`block p-4 rounded-lg text-center text-white font-medium transition-all hover:scale-105 ${getGateColor(status)}`}
                                        >
                                            <div className="text-lg font-bold">{gate}</div>
                                            {gateFlights.length > 0 && (
                                                <div className="text-xs mt-1 opacity-90">
                                                    {gateFlights[0].flight}
                                                </div>
                                            )}
                                            <div className="text-xs mt-1 opacity-75">
                                                {status === 'active' ? '使用中' : status === 'scheduled' ? '已安排' : '空閒'}
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        {/* 航班列表 */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* 入境航班 */}
                            <div className="bg-white rounded-lg shadow-sm border p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">入境航班</h3>
                                {arrivalFlights.length === 0 ? (
                                    <p className="text-gray-500 text-center py-4">今日無入境航班</p>
                                ) : (
                                    <div className="space-y-3">
                                        {arrivalFlights.map((flight, index) => (
                                            <div key={`${flight.gate}-${flight.flight}-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                                <div className="flex items-center space-x-3">
                                                    <Link 
                                                        href={`/gate/${flight.gate}`}
                                                        className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                                                    >
                                                        {flight.gate}
                                                    </Link>
                                                    <span className="font-mono">{flight.flight}</span>
                                                    <span className="text-sm text-gray-600">{flight.airline}</span>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <span className="text-sm text-gray-600">{flight.scheduledTime}</span>
                                                    {flight.status && (
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(flight.status)}`}>
                                                            {flight.status}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* 出境航班 */}
                            <div className="bg-white rounded-lg shadow-sm border p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">出境航班</h3>
                                {departureFlights.length === 0 ? (
                                    <p className="text-gray-500 text-center py-4">今日無出境航班</p>
                                ) : (
                                    <div className="space-y-3">
                                        {departureFlights.map((flight, index) => (
                                            <div key={`${flight.gate}-${flight.flight}-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                                <div className="flex items-center space-x-3">
                                                    <Link 
                                                        href={`/gate/${flight.gate}`}
                                                        className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                                                    >
                                                        {flight.gate}
                                                    </Link>
                                                    <span className="font-mono">{flight.flight}</span>
                                                    <span className="text-sm text-gray-600">{flight.airline}</span>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <span className="text-sm text-gray-600">{flight.scheduledTime}</span>
                                                    {flight.status && (
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(flight.status)}`}>
                                                            {flight.status}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}