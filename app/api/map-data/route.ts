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
    return new Promise((resolve) => {
      const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err: Error | null) => {
        if (err) {
          resolve(NextResponse.json({ error: 'Database connection failed' }, { status: 500 }));
          return;
        }

        const today = new Date().toISOString().split('T')[0];
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
            date
          FROM source_airport 
          WHERE date LIKE ?
          ORDER BY direction, scheduled_time
        `;

        db.all(query, [`%${today}%`], (err: Error | null, rows: FlightRow[]) => {
          db.close();
          
          if (err) {
            resolve(NextResponse.json({ error: 'Query failed' }, { status: 500 }));
            return;
          }

          // 分離入境和出境航班
          const arrivals = [];
          const departures = [];

          rows.forEach((row) => {
            const flightInfo = {
              gate: row.gate,
              terminal: row.terminal,
              flight: row.flight_no,
              status: row.status,
              scheduledTime: row.scheduled_time,
              actualTime: row.actual_time,
              airline: row.airline,
              aircraftType: row.aircraft_type
            };

            if (row.direction === 'A') {
              arrivals.push(flightInfo);
            } else if (row.direction === 'D') {
              departures.push(flightInfo);
            }
          });

          resolve(NextResponse.json({ 
            arrivals, 
            departures,
            timestamp: new Date().toISOString()
          }));
        });
      });
    });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}