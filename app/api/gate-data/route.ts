import { NextRequest, NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'goss_v4.db');

interface FlightRow {
  flight_no: string;
  direction: string;
  gate: string;
  terminal: string;
  scheduled_time: string;
  actual_time: string;
  status: string;
  airline: string;
  aircraft_type: string;
  date: string;
  baggage_carousel?: string;
  checkin_counter?: string;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const gate = searchParams.get('gate');
    
    if (!gate) {
      return NextResponse.json({ error: 'Gate parameter is required' }, { status: 400 });
    }

    return new Promise((resolve) => {
      const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err: Error | null) => {
        if (err) {
          resolve(NextResponse.json({ error: 'Database connection failed' }, { status: 500 }));
          return;
        }

        // 查詢指定登機門的航班資料
        const query = `
          SELECT 
            flight_no, 
            direction,
            gate, 
            terminal,
            scheduled_time, 
            actual_time, 
            status, 
            airline, 
            aircraft_type,
            date,
            baggage_carousel,
            checkin_counter
          FROM source_airport 
          WHERE gate = ? 
          AND date LIKE ?
          ORDER BY scheduled_time
        `;

        const today = new Date().toISOString().split('T')[0];
        
        db.all(query, [gate, `%${today}%`], (err: Error | null, rows: FlightRow[]) => {
          db.close();
          
          if (err) {
            resolve(NextResponse.json({ error: 'Query failed' }, { status: 500 }));
            return;
          }

          // 轉換為前端需要的格式
          const events = rows.map((row) => ({
            code: row.flight_no,
            direction: row.direction,
            gate: row.gate,
            terminal: row.terminal,
            scheduledTime: row.scheduled_time,
            actualTime: row.actual_time,
            status: row.status,
            airline: row.airline,
            aircraftType: row.aircraft_type,
            baggageCarousel: row.baggage_carousel,
            checkinCounter: row.checkin_counter
          }));

          resolve(NextResponse.json({ events }));
        });
      });
    });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}