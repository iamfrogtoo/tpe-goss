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
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const type = searchParams.get('type') || 'all'; // 'arr', 'dep', 'all'
    
    return new Promise((resolve) => {
      const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err: Error | null) => {
        if (err) {
          resolve(NextResponse.json({ error: 'Database connection failed' }, { status: 500 }));
          return;
        }

        let query = '';
        let params: string[] = [];

        if (type === 'arr') {
          query = `
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
              date
            FROM source_airport 
            WHERE direction = 'A' 
            AND date LIKE ?
            ORDER BY scheduled_time
          `;
          params = [`%${new Date().toISOString().split('T')[0]}%`];
        } else if (type === 'dep') {
          query = `
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
              date
            FROM source_airport 
            WHERE direction = 'D' 
            AND date LIKE ?
            ORDER BY scheduled_time
          `;
          params = [`%${new Date().toISOString().split('T')[0]}%`];
        } else {
          query = `
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
              date
            FROM source_airport 
            WHERE date LIKE ?
            ORDER BY direction, scheduled_time
          `;
          params = [`%${new Date().toISOString().split('T')[0]}%`];
        }

        db.all(query, params, (err: Error | null, rows: FlightRow[]) => {
          db.close();
          
          if (err) {
            resolve(NextResponse.json({ error: 'Query failed' }, { status: 500 }));
            return;
          }

          // 轉換為前端需要的格式
          const flights = rows.map((row) => ({
            type: row.direction === 'A' ? 'ARR' : 'DEP',
            displayDate: row.date?.split(' ')[0] || '',
            code: row.flight_no,
            time: row.scheduled_time,
            gate: row.gate,
            statusText: row.status,
            terminal: row.terminal || '-',
            facility: row.airline || '-',
            aircraftType: row.aircraft_type
          }));

          resolve(NextResponse.json({ flights }));
        });
      });
    });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}