/**
 * Polls the Node.js cloud API every 5 s for the latest sensor reading.
 * Keeps the same interface as the old WebSocket hook so all consumers
 * (SensorContext, TelemetryOverlay, DashboardSection) work unchanged.
 */

import { useEffect, useState, useRef } from 'react';

const API_URL =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_FASTAPI_URL) ||
  'http://localhost:8000';

interface SensorData {
  temp: number;
  humidity: number;
  light: number;
  soil: number;
}

interface UseWebSocketReturn {
  sensorData: SensorData;
  isConnected: boolean;
  error: string | null;
}

export function useWebSocket(_url: string): UseWebSocketReturn {
  const [sensorData, setSensorData] = useState<SensorData>({
    temp: 0,
    humidity: 0,
    light: 0,
    soil: 0,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLatest = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/sensors/latest?farm_id=farm_001`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('📡 Sensor poll:', data);
      // If backend returns an error body (no readings yet) treat as disconnected
      if (data.error) {
        setIsConnected(false);
        setError(data.error);
        return;
      }
      setSensorData({
        temp: data.temperature ?? 0,
        humidity: data.humidity ?? 0,
        light: data.light_level ?? 0,
        soil: data.soil_moisture ?? 0,
      });
      setIsConnected(true);
      setError(null);
    } catch (err: any) {
      console.error('Sensor poll failed:', err.message);
      setError(err.message || 'Failed to fetch');
      setIsConnected(false);
    }
  };

  useEffect(() => {
    fetchLatest();
    intervalRef.current = setInterval(fetchLatest, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { sensorData, isConnected, error };
}
