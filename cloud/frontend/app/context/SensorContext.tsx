/**
 * Sensor Data Context Provider
 * Provides real-time sensor data from ESP32 to all components
 */

"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface SensorData {
  temp: number;
  humidity: number;
  light: number;
  soil: number;
}

interface SensorContextType {
  sensorData: SensorData;
  isConnected: boolean;
  error: string | null;
}

const SensorContext = createContext<SensorContextType | undefined>(undefined);

export function SensorProvider({ children }: { children: ReactNode }) {
  // Connect to the FastAPI backend WebSocket
  // Change this URL if your backend is running on a different port
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'ws://localhost:8000';
  const { sensorData, isConnected, error } = useWebSocket(`${BACKEND_URL}/ws/farm_001`);

  return (
    <SensorContext.Provider value={{ sensorData, isConnected, error }}>
      {children}
    </SensorContext.Provider>
  );
}

export function useSensorData() {
  const context = useContext(SensorContext);
  if (context === undefined) {
    throw new Error('useSensorData must be used within a SensorProvider');
  }
  return context;
}
