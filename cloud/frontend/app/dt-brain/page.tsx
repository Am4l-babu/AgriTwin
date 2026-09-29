"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Brain, Activity, Droplets, Sun, Thermometer, Sprout, Clock, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";

interface PhysicsModel {
    equation: string;
    [key: string]: any;
}

interface BrainData {
    twin_accuracy_pct: number | null;
    model_reliability_pct: number | null;
    avg_prediction_error: number;
    sample_count: number;
    latest_prediction: {
        predicted_soil_moisture: number;
        actual_soil_moisture: number;
        error: number;
    };
    physics_models: {
        "1_soil_moisture_balance": PhysicsModel;
        "2_evaporation_model": PhysicsModel;
        "3_plant_water_uptake": PhysicsModel;
        "4_light_influence": PhysicsModel;
        "5_temperature_effect": PhysicsModel;
        "6_time_evolution": PhysicsModel;
    };
}

interface AccuracyRecord {
    timestamp: string;
    predicted_soil_moisture: number;
    actual_soil_moisture: number;
    soil_moisture_error: number;
}

export default function DTBrainPage() {
    const [brain, setBrain] = useState<BrainData | null>(null);
    const [history, setHistory] = useState<AccuracyRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [hours, setHours] = useState(24);

    const fetchData = useCallback(async () => {
        try {
            const [brainRes, histRes] = await Promise.all([
                fetch(`${API_URL}/api/v1/twin-accuracy/brain?farm_id=farm_001&hours=${hours}`),
                fetch(`${API_URL}/api/v1/twin-accuracy/history?farm_id=farm_001&hours=${hours}&limit=200`),
            ]);
            if (brainRes.ok) setBrain(await brainRes.json());
            if (histRes.ok) {
                const data = await histRes.json();
                setHistory(data.records || []);
            }
        } catch (e) {
            console.error("DT Brain fetch error:", e);
        } finally {
            setLoading(false);
        }
    }, [hours]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const accuracy = brain?.twin_accuracy_pct ?? 0;
    const avgErr = brain?.avg_prediction_error ?? 0;

    // Accuracy ring color
    const ringColor =
        accuracy >= 90 ? "text-emerald-400" :
        accuracy >= 70 ? "text-yellow-400" :
        "text-red-400";

    const ringBg =
        accuracy >= 90 ? "stroke-emerald-400" :
        accuracy >= 70 ? "stroke-yellow-400" :
        "stroke-red-400";

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
            {/* Header */}
            <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/70 border-b border-white/5">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 rounded-lg hover:bg-white/5 transition">
                            <ArrowLeft size={20} className="text-white/60" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/30">
                                <Brain size={22} className="text-violet-400" />
                            </div>
                            <div>
                                <h1 className="text-lg font-semibold">Digital Twin Brain</h1>
                                <p className="text-xs text-white/40">Physics Model Monitor</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={hours}
                            onChange={(e) => setHours(Number(e.target.value))}
                            className="bg-[#1e2433] border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-orange-400 [&>option]:bg-[#1e2433] [&>option]:text-white"
                        >
                            <option value={1}>1 hour</option>
                            <option value={6}>6 hours</option>
                            <option value={12}>12 hours</option>
                            <option value={24}>24 hours</option>
                            <option value={48}>48 hours</option>
                        </select>
                        <button onClick={fetchData} className="p-2 rounded-lg hover:bg-white/5 transition">
                            <RefreshCw size={16} className="text-white/40" />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
                {loading ? (
                    <div className="flex items-center justify-center h-96">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-violet-400 border-t-transparent" />
                    </div>
                ) : !brain ? (
                    <div className="text-center py-20 text-white/40">
                        <Brain size={48} className="mx-auto mb-4 opacity-30" />
                        <p>No twin accuracy data yet. Sensor readings will populate this page.</p>
                    </div>
                ) : (
                    <>
                        {/* Accuracy Hero Card */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Big accuracy ring */}
                            <div className="bg-white/[0.03] rounded-2xl border border-white/5 p-8 flex flex-col items-center justify-center">
                                <div className="relative w-40 h-40">
                                    <svg className="w-40 h-40 -rotate-90" viewBox="0 0 120 120">
                                        <circle cx="60" cy="60" r="54" fill="none" stroke="currentColor" strokeWidth="8" className="text-white/5" />
                                        <circle
                                            cx="60" cy="60" r="54"
                                            fill="none"
                                            strokeWidth="8"
                                            strokeLinecap="round"
                                            strokeDasharray={`${(accuracy / 100) * 339.3} 339.3`}
                                            className={ringBg}
                                            style={{ transition: "stroke-dasharray 1s ease" }}
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className={`text-3xl font-bold ${ringColor}`}>
                                            {accuracy > 0 ? `${accuracy}%` : "—"}
                                        </span>
                                        <span className="text-xs text-white/40 mt-1">Twin Accuracy</span>
                                    </div>
                                </div>
                                <p className="mt-4 text-sm text-white/50">
                                    {brain.sample_count} predictions tracked
                                </p>
                            </div>

                            {/* Stats cards */}
                            <div className="space-y-4">
                                <StatCard
                                    icon={<Activity size={18} />}
                                    label="Average Prediction Error"
                                    value={`${avgErr}%`}
                                    color="text-orange-400"
                                    bg="from-orange-500/10 to-orange-500/5"
                                />
                                <StatCard
                                    icon={<TrendingUp size={18} />}
                                    label="Model Reliability"
                                    value={`${brain.model_reliability_pct ?? 0}%`}
                                    color="text-emerald-400"
                                    bg="from-emerald-500/10 to-emerald-500/5"
                                />
                                <StatCard
                                    icon={<Droplets size={18} />}
                                    label="Water Deficit"
                                    value={`${brain.physics_models["1_soil_moisture_balance"].water_deficit_mm?.toFixed(1) ?? 0} mm`}
                                    color="text-blue-400"
                                    bg="from-blue-500/10 to-blue-500/5"
                                />
                            </div>

                            {/* Latest prediction comparison */}
                            <div className="bg-white/[0.03] rounded-2xl border border-white/5 p-6">
                                <h3 className="text-sm font-medium text-white/60 mb-4">Latest Prediction</h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-end">
                                        <div>
                                            <p className="text-xs text-white/40">Twin Predicted</p>
                                            <p className="text-2xl font-bold text-violet-400">
                                                {brain.latest_prediction.predicted_soil_moisture.toFixed(1)}%
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-white/40">Sensor Actual</p>
                                            <p className="text-2xl font-bold text-emerald-400">
                                                {brain.latest_prediction.actual_soil_moisture.toFixed(1)}%
                                            </p>
                                        </div>
                                    </div>
                                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-violet-500 to-emerald-500 rounded-full transition-all duration-500"
                                            style={{ width: `${Math.max(5, 100 - brain.latest_prediction.error * 5)}%` }}
                                        />
                                    </div>
                                    <p className="text-xs text-white/40 text-center">
                                        Error: <span className={brain.latest_prediction.error > 10 ? "text-red-400" : "text-emerald-400"}>
                                            {brain.latest_prediction.error.toFixed(1)}%
                                        </span>
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Physics Models Grid */}
                        <h2 className="text-lg font-semibold flex items-center gap-2 pt-4">
                            <Brain size={20} className="text-violet-400" />
                            Physics Models — DT Brain
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                            <PhysicsCard
                                number={1}
                                title="Soil Moisture Balance"
                                icon={<Droplets size={20} />}
                                color="blue"
                                model={brain.physics_models["1_soil_moisture_balance"]}
                                details={[
                                    { label: "Current Moisture", value: `${brain.physics_models["1_soil_moisture_balance"].current_moisture_pct?.toFixed(1)}%` },
                                    { label: "Predicted", value: `${brain.physics_models["1_soil_moisture_balance"].predicted_moisture_pct?.toFixed(1)}%` },
                                    { label: "Evaporation Loss", value: `${brain.physics_models["1_soil_moisture_balance"].evaporation_loss}%` },
                                    { label: "Water Deficit", value: `${brain.physics_models["1_soil_moisture_balance"].water_deficit_mm?.toFixed(1)} mm` },
                                    { label: "Status", value: brain.physics_models["1_soil_moisture_balance"].status },
                                ]}
                            />
                            <PhysicsCard
                                number={2}
                                title="Evaporation Model"
                                icon={<TrendingDown size={20} />}
                                color="orange"
                                model={brain.physics_models["2_evaporation_model"]}
                                details={[
                                    { label: "Temperature", value: `${brain.physics_models["2_evaporation_model"].temperature_c}°C` },
                                    { label: "Humidity", value: `${brain.physics_models["2_evaporation_model"].humidity_pct}%` },
                                    { label: "Evap Factor", value: `${brain.physics_models["2_evaporation_model"].evaporation_factor}` },
                                    { label: "Rate", value: brain.physics_models["2_evaporation_model"].rate_label },
                                ]}
                            />
                            <PhysicsCard
                                number={3}
                                title="Plant Water Uptake"
                                icon={<Sprout size={20} />}
                                color="green"
                                model={brain.physics_models["3_plant_water_uptake"]}
                                details={[
                                    { label: "Plant k", value: `${brain.physics_models["3_plant_water_uptake"].plant_constant_k}` },
                                    { label: "Light", value: `${brain.physics_models["3_plant_water_uptake"].light_estimate_pct}%` },
                                    { label: "Uptake Rate", value: `${brain.physics_models["3_plant_water_uptake"].uptake_rate}` },
                                ]}
                            />
                            <PhysicsCard
                                number={4}
                                title="Light Influence"
                                icon={<Sun size={20} />}
                                color="yellow"
                                model={brain.physics_models["4_light_influence"]}
                                details={[
                                    { label: "Light Level", value: `${brain.physics_models["4_light_influence"].light_level_pct}%` },
                                    { label: "Growth Stage", value: brain.physics_models["4_light_influence"].growth_stage },
                                    { label: "Prediction", value: brain.physics_models["4_light_influence"].prediction },
                                ]}
                            />
                            <PhysicsCard
                                number={5}
                                title="Temperature Effect"
                                icon={<Thermometer size={20} />}
                                color="red"
                                model={brain.physics_models["5_temperature_effect"]}
                                details={[
                                    { label: "Temperature", value: `${brain.physics_models["5_temperature_effect"].temperature_c}°C` },
                                    { label: "Effect", value: brain.physics_models["5_temperature_effect"].effect_label },
                                ]}
                            />
                            <PhysicsCard
                                number={6}
                                title="Time Evolution"
                                icon={<Clock size={20} />}
                                color="violet"
                                model={brain.physics_models["6_time_evolution"]}
                                details={[
                                    { label: "Current Moisture", value: `${brain.physics_models["6_time_evolution"].current_moisture_pct}%` },
                                    { label: "Loss/Hour", value: `${brain.physics_models["6_time_evolution"].moisture_loss_per_hour_pct}%` },
                                    { label: "Hours to Stress", value: `${brain.physics_models["6_time_evolution"].hours_until_stress}h` },
                                    { label: "Forecast", value: brain.physics_models["6_time_evolution"].prediction },
                                ]}
                            />
                        </div>

                        {/* Accuracy History Chart (simple bar visualization) */}
                        {history.length > 0 && (
                            <div className="bg-white/[0.03] rounded-2xl border border-white/5 p-6">
                                <h3 className="text-sm font-medium text-white/60 mb-4">Prediction Error History</h3>
                                <div className="flex items-end gap-[2px] h-32 overflow-hidden">
                                    {history.slice(-100).map((rec, i) => {
                                        const err = rec.soil_moisture_error ?? 0;
                                        const h = Math.min(100, err * 5);
                                        const barColor = err > 10 ? "bg-red-500" : err > 5 ? "bg-yellow-500" : "bg-emerald-500";
                                        return (
                                            <div
                                                key={i}
                                                className={`flex-1 min-w-[2px] rounded-t ${barColor} opacity-80 transition-all`}
                                                style={{ height: `${h}%` }}
                                                title={`${rec.timestamp}: error ${err.toFixed(1)}%`}
                                            />
                                        );
                                    })}
                                </div>
                                <div className="flex justify-between mt-2 text-[10px] text-white/30">
                                    <span>{history[0]?.timestamp?.slice(11, 16)}</span>
                                    <span>{history[history.length - 1]?.timestamp?.slice(11, 16)}</span>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}

/* ─── Reusable components ─── */

function StatCard({ icon, label, value, color, bg }: {
    icon: React.ReactNode;
    label: string;
    value: string;
    color: string;
    bg: string;
}) {
    return (
        <div className={`bg-gradient-to-r ${bg} rounded-xl border border-white/5 p-4 flex items-center gap-4`}>
            <div className={`${color}`}>{icon}</div>
            <div>
                <p className="text-xs text-white/40">{label}</p>
                <p className={`text-lg font-bold ${color}`}>{value}</p>
            </div>
        </div>
    );
}

const colorMap: Record<string, { border: string; icon: string; eq: string }> = {
    blue:   { border: "border-blue-500/20",   icon: "text-blue-400",   eq: "text-blue-300/60" },
    orange: { border: "border-orange-500/20", icon: "text-orange-400", eq: "text-orange-300/60" },
    green:  { border: "border-emerald-500/20", icon: "text-emerald-400", eq: "text-emerald-300/60" },
    yellow: { border: "border-yellow-500/20", icon: "text-yellow-400", eq: "text-yellow-300/60" },
    red:    { border: "border-red-500/20",    icon: "text-red-400",    eq: "text-red-300/60" },
    violet: { border: "border-violet-500/20", icon: "text-violet-400", eq: "text-violet-300/60" },
};

function PhysicsCard({ number, title, icon, color, model, details }: {
    number: number;
    title: string;
    icon: React.ReactNode;
    color: string;
    model: PhysicsModel;
    details: { label: string; value: string }[];
}) {
    const c = colorMap[color] || colorMap.blue;
    return (
        <div className={`bg-white/[0.03] rounded-2xl border ${c.border} p-5 hover:bg-white/[0.05] transition`}>
            <div className="flex items-center gap-3 mb-3">
                <div className={c.icon}>{icon}</div>
                <div>
                    <p className="text-sm font-semibold">{number}. {title}</p>
                    <p className={`text-[11px] font-mono ${c.eq}`}>{model.equation}</p>
                </div>
            </div>
            <div className="space-y-2">
                {details.map((d, i) => (
                    <div key={i} className="flex justify-between text-xs">
                        <span className="text-white/40">{d.label}</span>
                        <span className="text-white/80 font-medium">{d.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
