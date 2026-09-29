import React, { useState } from 'react';
import { clsx } from 'clsx';
import { Leaf, Droplets, Thermometer, Sun, Activity, Sprout, Wind, Layers, Zap } from 'lucide-react';
import { useSensorData } from '../app/context/SensorContext';

const API_BASE = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

type RelayName = 'pump' | 'light';

function useRelayControl() {
    const [pumpOn, setPumpOn] = useState(false);
    const [lightOn, setLightOn] = useState(false);
    const [loading, setLoading] = useState<RelayName | null>(null);
    const [error, setError] = useState<string | null>(null);

    const toggle = async (relay: RelayName) => {
        const current = relay === 'pump' ? pumpOn : lightOn;
        const newState = !current;
        setLoading(relay);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/relay/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ relay, state: newState ? 'on' : 'off' }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            relay === 'pump' ? setPumpOn(newState) : setLightOn(newState);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(`${relay} command failed: ${msg}`);
        } finally {
            setLoading(null);
        }
    };

    return { pumpOn, lightOn, loading, error, toggle };
}

export default function DashboardSection() {
    const { sensorData, isConnected } = useSensorData();
    const relay = useRelayControl();

    // Calculate status based on sensor values
    const getSoilStatus = (moisture: number) => {
        if (moisture > 60) return "High";
        if (moisture > 30) return "Optimal";
        return "Low";
    };

    const getTempStatus = (temp: number) => {
        if (temp > 30) return "High";
        if (temp > 18 && temp < 28) return "Optimal";
        return "Low";
    };

    const getHumidityStatus = (humidity: number) => {
        if (humidity > 70) return "High";
        if (humidity > 40 && humidity < 70) return "Optimal";
        return "Low";
    };

    const getLightStatus = (light: number) => {
        if (light > 800) return "High";
        if (light > 200) return "Optimal";
        return "Low";
    };

    return (
        <section className="relative z-10 w-full min-h-screen bg-gradient-to-b from-white to-slate-100 flex flex-col items-center justify-center p-8 pt-24">
            <div className="w-full max-w-7xl space-y-12">
                {/* Header */}
                <div className="flex flex-col gap-2 border-l-2 border-emerald-500/60 pl-6">
                    <h2 className="text-4xl md:text-5xl font-medium tracking-tighter text-black/80">
                        DIGITAL TWIN <span className="text-black/30">DASHBOARD</span>
                    </h2>
                    <p className="text-black/40 max-w-xl">
                        Real-time biometric analysis from ESP32 edge device.
                        {!isConnected && <span className="text-red-500 ml-2">(Disconnected)</span>}
                    </p>
                </div>

                {/* Row 1: Live Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <MetricCard 
                        icon={Droplets} 
                        label="Soil Moisture" 
                        value={`${sensorData.soil.toFixed(0)}%`} 
                        status={getSoilStatus(sensorData.soil)} 
                        color="emerald" 
                    />
                    <MetricCard 
                        icon={Thermometer} 
                        label="Temperature" 
                        value={`${sensorData.temp.toFixed(1)}°C`} 
                        status={getTempStatus(sensorData.temp)} 
                        color="amber" 
                    />
                    <MetricCard 
                        icon={Wind} 
                        label="Humidity" 
                        value={`${sensorData.humidity.toFixed(0)}%`} 
                        status={getHumidityStatus(sensorData.humidity)} 
                        color="cyan" 
                    />
                    <MetricCard 
                        icon={Sun} 
                        label="Light Intensity" 
                        value={`${sensorData.light.toFixed(0)} lux`} 
                        status={getLightStatus(sensorData.light)} 
                        color="yellow" 
                    />
                </div>

                {/* Row 2: Deep Intelligence */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
                    {/* Main Growth Status */}
                    <div className="lg:col-span-2 bg-white border border-black/8 shadow-sm rounded-2xl p-8 flex flex-col justify-between group hover:border-emerald-500/40 transition-colors">
                        <div className="flex justify-between items-start">
                            <div>
                                <div className="flex items-center gap-2 text-emerald-600 mb-2">
                                    <Sprout size={20} />
                                    <span className="uppercase text-xs tracking-widest font-medium">Growth Stage</span>
                                </div>
                                <h3 className="text-3xl text-black/80 font-light">Vegetative Phase <span className="text-black/30">Day 14</span></h3>
                            </div>
                            <div className="h-12 w-12 rounded-full border border-black/10 flex items-center justify-center">
                                <Activity size={20} className="text-black/30" />
                            </div>
                        </div>

                        <div className="mt-8 space-y-4">
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm text-black/50">
                                    <span>Biomass Accumulation</span>
                                    <span>78%</span>
                                </div>
                                <div className="h-1 w-full bg-black/8 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500 w-[78%]" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm text-black/50">
                                    <span>Root Density</span>
                                    <span>92%</span>
                                </div>
                                <div className="h-1 w-full bg-black/8 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500 w-[92%]" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Side Stats */}
                    <div className="flex flex-col gap-6">
                        <StatRow icon={Layers} label="VPD" value="0.85 kPa" />
                        <StatRow icon={Wind} label="Evapotranspiration" value="4.2 mm/day" />
                        <StatRow icon={Sun} label="DLI" value="12.4 mol/m²/d" />
                    </div>
                </div>
            </div>

            {/* Row 3: Relay Controls */}
            <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-8">
                <div className="flex items-center gap-3 mb-6">
                    <Zap size={20} className="text-emerald-600" />
                    <h3 className="text-xs uppercase tracking-widest font-medium text-black/40">Actuator Control</h3>
                </div>
                {relay.error && (
                    <p className="text-red-500 text-xs mb-4">{relay.error}</p>
                )}
                <div className="flex gap-6 flex-wrap">
                    <RelayButton
                        label="Water Pump"
                        icon="💧"
                        isOn={relay.pumpOn}
                        loading={relay.loading === 'pump'}
                        onToggle={() => relay.toggle('pump')}
                        onColor="bg-cyan-500"
                    />
                    <RelayButton
                        label="Grow Light"
                        icon="💡"
                        isOn={relay.lightOn}
                        loading={relay.loading === 'light'}
                        onToggle={() => relay.toggle('light')}
                        onColor="bg-yellow-400"
                    />
                </div>
            </div>
        </section>
    );
}

function MetricCard({ icon: Icon, label, value, status, color }: {
    icon: any; label: string; value: string; status: string; color: string;
}) {
    const colorClasses = {
        emerald: "text-emerald-600 border-emerald-500/20 bg-emerald-50",
        amber: "text-amber-600  border-amber-500/20  bg-amber-50",
        cyan: "text-cyan-600   border-cyan-500/20   bg-cyan-50",
        yellow: "text-yellow-600 border-yellow-500/20 bg-yellow-50",
    };

    return (
        <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-6 hover:-translate-y-1 transition-transform duration-300">
            <div className="flex justify-between items-start mb-4">
                <div className={clsx("p-2 rounded-lg border", colorClasses[color as keyof typeof colorClasses])}>
                    <Icon size={20} />
                </div>
                <span className={clsx("text-xs px-2 py-1 rounded-full border", colorClasses[color as keyof typeof colorClasses])}>
                    {status}
                </span>
            </div>
            <div className="space-y-1">
                <p className="text-black/40 text-xs uppercase tracking-widest">{label}</p>
                <p className="text-3xl text-black/80 font-medium">{value}</p>
            </div>
        </div>
    );
}

function StatRow({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
    return (
        <div className="flex-1 bg-white border border-black/8 shadow-sm rounded-2xl p-6 flex items-center justify-between hover:border-emerald-500/30 transition-colors">
            <div className="flex items-center gap-4">
                <Icon size={20} className="text-black/30" />
                <span className="text-black/50 text-sm font-medium">{label}</span>
            </div>
            <span className="text-xl text-black/80 font-mono">{value}</span>
        </div>
    );
}

function RelayButton({ label, icon, isOn, loading, onToggle, onColor }: {
    label: string; icon: string; isOn: boolean; loading: boolean;
    onToggle: () => void; onColor: string;
}) {
    return (
        <button
            onClick={onToggle}
            disabled={loading}
            className={clsx(
                'flex items-center gap-3 px-6 py-4 rounded-2xl border font-medium text-sm transition-all duration-200 min-w-[160px] justify-between',
                isOn
                    ? `${onColor} text-white border-transparent shadow-md`
                    : 'bg-white border-black/10 text-black/60 hover:border-emerald-500/40',
                loading && 'opacity-60 cursor-wait',
            )}
        >
            <span className="text-lg">{icon}</span>
            <span>{label}</span>
            <span className={clsx(
                'text-xs px-2 py-0.5 rounded-full border',
                isOn ? 'border-white/30 bg-white/20 text-white' : 'border-black/10 bg-black/5 text-black/40'
            )}>
                {loading ? '…' : isOn ? 'ON' : 'OFF'}
            </span>
        </button>
    );
}
