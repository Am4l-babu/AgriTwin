"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
} from "recharts";
import { Thermometer, Droplets, Sun, Wind, RefreshCw, Database } from "lucide-react";

interface SensorReading {
    timestamp: string;
    temperature: number;
    humidity: number;
    light_level: number;
    soil_moisture: number;
}

interface Stats {
    avg_temperature: number;
    min_temperature: number;
    max_temperature: number;
    avg_humidity: number;
    min_humidity: number;
    max_humidity: number;
    avg_light: number;
    min_light: number;
    max_light: number;
    avg_soil: number;
    min_soil: number;
    max_soil: number;
}

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";

export default function HistoryCharts() {
    const [readings, setReadings] = useState<SensorReading[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [totalReadings, setTotalReadings] = useState(0);
    const [hours, setHours] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${FASTAPI_URL}/api/v1/sensors/history?farm_id=farm_001&hours=${hours}&limit=500`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            const raw: Array<{ timestamp: string; temperature: number; humidity: number; light_level: number; soil_moisture: number }> = json.readings ?? [];

            // Map FastAPI fields → component field names and format time label
            const formatted: SensorReading[] = raw
                .filter((r) => r.temperature != null)
                .map((r) => ({
                    timestamp: r.timestamp,
                    temperature: r.temperature ?? 0,
                    humidity: r.humidity ?? 0,
                    light_level: r.light_level ?? 0,
                    soil_moisture: r.soil_moisture ?? 0,
                    time: new Date(r.timestamp + 'Z').toLocaleTimeString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                    }),
                }));

            setReadings(formatted);
            setTotalReadings(json.count ?? formatted.length);

            // Compute stats client-side
            if (formatted.length > 0) {
                const vals = (key: keyof SensorReading) =>
                    formatted.map((r) => r[key] as number).filter((v) => !isNaN(v) && v != null);
                const avg = (a: number[]) => a.length ? a.reduce((s, v) => s + v, 0) / a.length : 0;

                const t = vals("temperature");
                const h = vals("humidity");
                const s = vals("soil_moisture");
                const l = vals("light_level");

                setStats({
                    avg_temperature: avg(t), min_temperature: Math.min(...t), max_temperature: Math.max(...t),
                    avg_humidity: avg(h),    min_humidity: Math.min(...h),    max_humidity: Math.max(...h),
                    avg_light: avg(l),       min_light: Math.min(...l),       max_light: Math.max(...l),
                    avg_soil: avg(s),        min_soil: Math.min(...s),        max_soil: Math.max(...s),
                });
            }
        } catch (err: any) {
            setError(err.message || "Failed to load history");
        } finally {
            setLoading(false);
        }
    }, [hours]);

    useEffect(() => {
        fetchData();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const chartConfigs = [
        {
            key: "temperature",
            label: "Temperature",
            unit: "°C",
            color: "#f59e0b",
            gradient: "amber",
            icon: Thermometer,
            stat: stats
                ? { avg: stats.avg_temperature, min: stats.min_temperature, max: stats.max_temperature }
                : null,
        },
        {
            key: "humidity",
            label: "Humidity",
            unit: "%",
            color: "#06b6d4",
            gradient: "cyan",
            icon: Wind,
            stat: stats
                ? { avg: stats.avg_humidity, min: stats.min_humidity, max: stats.max_humidity }
                : null,
        },
        {
            key: "soil_moisture",
            label: "Soil Moisture",
            unit: "%",
            color: "#10b981",
            gradient: "emerald",
            icon: Droplets,
            stat: stats
                ? { avg: stats.avg_soil, min: stats.min_soil, max: stats.max_soil }
                : null,
        },
        {
            key: "light_level",
            label: "Light Intensity",
            unit: " lux",
            color: "#eab308",
            gradient: "yellow",
            icon: Sun,
            stat: stats
                ? { avg: stats.avg_light, min: stats.min_light, max: stats.max_light }
                : null,
        },
    ];

    return (
        <section className="relative z-10 w-full min-h-screen bg-gradient-to-b from-slate-100 to-slate-200 flex flex-col items-center p-8 pt-16">
            <div className="w-full max-w-7xl space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-l-2 border-emerald-500/60 pl-6">
                    <div>
                        <h2 className="text-4xl md:text-5xl font-medium tracking-tighter text-black/80">
                            SENSOR <span className="text-black/30">HISTORY</span>
                        </h2>
                        <p className="text-black/40 mt-1">
                            Historical trends from stored sensor data.
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Time Range Picker */}
                        <div className="flex bg-white rounded-xl border border-black/8 overflow-hidden shadow-sm">
                            {[1, 6, 12, 24, 48].map((h) => (
                                <button
                                    key={h}
                                    onClick={() => setHours(h)}
                                    className={`px-4 py-2 text-sm font-medium transition-colors ${hours === h
                                            ? "bg-emerald-500 text-white"
                                            : "text-black/50 hover:text-black/80 hover:bg-black/5"
                                        }`}
                                >
                                    {h}h
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="p-2.5 rounded-xl bg-white border border-black/8 shadow-sm hover:border-emerald-500/40 transition-colors disabled:opacity-50"
                        >
                            <RefreshCw size={18} className={`text-black/40 ${loading ? "animate-spin" : ""}`} />
                        </button>
                    </div>
                </div>

                {/* Stats Summary Bar */}
                <div className="flex items-center gap-3 bg-white/60 rounded-xl border border-black/8 px-6 py-3 shadow-sm">
                    <Database size={16} className="text-black/30" />
                    <span className="text-sm text-black/50">
                        <span className="font-mono text-black/70">{totalReadings}</span> total readings stored
                    </span>
                    <span className="text-black/20 mx-2">|</span>
                    <span className="text-sm text-black/50">
                        Showing <span className="font-mono text-black/70">{readings.length}</span> points over{" "}
                        <span className="font-mono text-black/70">{hours}h</span>
                    </span>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-6 py-3 text-sm">
                        {error}
                    </div>
                )}

                {/* Charts Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {chartConfigs.map((cfg) => (
                        <ChartCard
                            key={cfg.key}
                            dataKey={cfg.key}
                            label={cfg.label}
                            unit={cfg.unit}
                            color={cfg.color}
                            icon={cfg.icon}
                            data={readings}
                            stat={cfg.stat}
                            loading={loading}
                        />
                    ))}
                </div>
            </div>
        </section>
    );
}

function ChartCard({
    dataKey,
    label,
    unit,
    color,
    icon: Icon,
    data,
    stat,
    loading,
}: {
    dataKey: string;
    label: string;
    unit: string;
    color: string;
    icon: any;
    data: any[];
    stat: { avg: number; min: number; max: number } | null;
    loading: boolean;
}) {
    return (
        <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-6 hover:border-emerald-500/20 transition-colors">
            {/* Card Header */}
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                    <Icon size={18} style={{ color }} />
                    <span className="text-sm font-medium text-black/60 uppercase tracking-widest">{label}</span>
                </div>
                {stat && (
                    <div className="flex gap-3 text-xs text-black/40">
                        <span>
                            min <span className="font-mono text-black/60">{stat.min.toFixed(1)}{unit}</span>
                        </span>
                        <span>
                            avg <span className="font-mono text-black/60">{stat.avg.toFixed(1)}{unit}</span>
                        </span>
                        <span>
                            max <span className="font-mono text-black/60">{stat.max.toFixed(1)}{unit}</span>
                        </span>
                    </div>
                )}
            </div>

            {/* Chart */}
            <div className="h-48">
                {data.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-black/30 text-sm">
                        {loading ? "Loading..." : "No data yet — waiting for sensor readings"}
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                                    <stop offset="95%" stopColor={color} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#0000000a" />
                            <XAxis
                                dataKey="time"
                                tick={{ fontSize: 11, fill: "#00000050" }}
                                tickLine={false}
                                axisLine={{ stroke: "#0000000a" }}
                            />
                            <YAxis
                                tick={{ fontSize: 11, fill: "#00000050" }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                contentStyle={{
                                    borderRadius: "12px",
                                    border: "1px solid #0000000d",
                                    boxShadow: "0 4px 12px #0000000d",
                                    fontSize: "13px",
                                }}
                                formatter={(value: number | undefined) =>
                                    value !== undefined ? [`${value.toFixed(1)}${unit}`, label] : ['N/A', label]
                                }
                            />
                            <Area
                                type="monotone"
                                dataKey={dataKey}
                                stroke={color}
                                strokeWidth={2}
                                fill={`url(#grad-${dataKey})`}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 0 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
