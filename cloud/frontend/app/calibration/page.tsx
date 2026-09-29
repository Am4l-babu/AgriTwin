"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Thermometer,
  Droplets,
  Sun,
  FlaskConical,
  ArrowLeft,
  RefreshCw,
  Check,
  AlertTriangle,
  Save,
  Wand2,
  ChevronDown,
  ChevronUp,
  Settings2,
} from "lucide-react";
import { clsx } from "clsx";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ScatterChart,
  Scatter,
} from "recharts";

// â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface CalibrationProfile {
  sensor_type: string;
  calibration_method: string;
  calibration_date: string;
  description?: string;
  notes?: string;
  offset?: number;
  multiplier?: number;
  dry_value?: number;
  wet_value?: number;
  point1?: { raw: number; actual: number; buffer?: string };
  point2?: { raw: number; actual: number; buffer?: string };
  point3?: { raw: number; actual: number; buffer?: string };
  reference_points?: { reference: number; measured: number; condition?: string }[];
  interpretation?: Record<string, [number, number]>;
  conversion?: {
    formula?: string;
    output_range?: { min: number; max: number; unit: string };
  };
  temperature_compensation?: {
    enabled: boolean;
    reference_temperature: number;
    formula: string;
  };
  optimal_ranges?: Record<string, { min_lux: number; max_lux: number; description?: string }>;
}

interface ProfileSummary {
  sensor_type: string;
  method: string;
  calibration_date: string | null;
  description: string;
  notes: string;
  has_interpretation: boolean;
  has_reference_points: boolean;
}

interface WizardPoint {
  raw: string;
  actual: string;
  condition: string;
}

// â”€â”€ Constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const BACKEND_HTTP = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const SENSOR_META: Record<string, {
  icon: any;
  label: string;
  color: string;
  unit: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  gradientFrom: string;
  gradientTo: string;
}> = {
  temperature: {
    icon: Thermometer,
    label: "Temperature",
    color: "#f59e0b",
    unit: "Â°C",
    bgClass: "bg-amber-50",
    borderClass: "border-amber-500/20",
    textClass: "text-amber-600",
    gradientFrom: "from-amber-500",
    gradientTo: "to-orange-500",
  },
  humidity: {
    icon: Droplets,
    label: "Humidity",
    color: "#06b6d4",
    unit: "%",
    bgClass: "bg-cyan-50",
    borderClass: "border-cyan-500/20",
    textClass: "text-cyan-600",
    gradientFrom: "from-cyan-500",
    gradientTo: "to-sky-500",
  },
  soil_moisture: {
    icon: Droplets,
    label: "Soil Moisture",
    color: "#10b981",
    unit: "%",
    bgClass: "bg-emerald-50",
    borderClass: "border-emerald-500/20",
    textClass: "text-emerald-600",
    gradientFrom: "from-emerald-500",
    gradientTo: "to-teal-500",
  },
  light: {
    icon: Sun,
    label: "Light (LDR)",
    color: "#eab308",
    unit: "lux",
    bgClass: "bg-yellow-50",
    borderClass: "border-yellow-500/20",
    textClass: "text-yellow-600",
    gradientFrom: "from-yellow-500",
    gradientTo: "to-amber-500",
  },
  ph: {
    icon: FlaskConical,
    label: "pH Sensor",
    color: "#8b5cf6",
    unit: "pH",
    bgClass: "bg-violet-50",
    borderClass: "border-violet-500/20",
    textClass: "text-violet-600",
    gradientFrom: "from-violet-500",
    gradientTo: "to-purple-500",
  },
};

const METHOD_LABELS: Record<string, string> = {
  offset_correction: "Offset Correction",
  two_point_linear: "Two-Point Linear",
  three_point_polynomial: "Three-Point Polynomial",
  not_calibrated: "Not Calibrated",
};

// â”€â”€ Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function CalibrationPage() {
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [selectedSensor, setSelectedSensor] = useState<string | null>(null);
  const [fullProfile, setFullProfile] = useState<CalibrationProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  // Fetch profile list
  const fetchProfiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/v1/calibration/profiles`);
      if (!res.ok) throw new Error("Failed to fetch profiles");
      const data = await res.json();
      setProfiles(data.profiles || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch full profile for selected sensor
  const fetchFullProfile = useCallback(async (sensorType: string) => {
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/v1/calibration/profiles/${sensorType}`);
      if (!res.ok) throw new Error("Profile not found");
      const data = await res.json();
      setFullProfile(data);
    } catch (err: any) {
      setError(err.message);
      setFullProfile(null);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  useEffect(() => {
    if (selectedSensor) {
      fetchFullProfile(selectedSensor);
      setWizardOpen(false);
      setSuccessMsg(null);
    }
  }, [selectedSensor, fetchFullProfile]);

  // Auto-clear success message
  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(null), 4000);
      return () => clearTimeout(t);
    }
  }, [successMsg]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-white to-slate-100">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="flex items-center gap-4 mb-2">
          <Link
            href="/"
            className="p-2 rounded-lg border border-black/8 hover:border-emerald-500/40 transition-colors"
          >
            <ArrowLeft size={18} className="text-black/40" />
          </Link>
          <div className="border-l-2 border-emerald-500/60 pl-6">
            <h1 className="text-4xl md:text-5xl font-medium tracking-tighter text-black/80">
              SENSOR <span className="text-black/30">CALIBRATION</span>
            </h1>
            <p className="text-black/40 max-w-xl mt-1">
              View, edit, and recalibrate ESP32 edge sensor profiles.
            </p>
          </div>
        </div>

        {/* Status Banner */}
        {error && (
          <div className="mt-6 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            <AlertTriangle size={16} /> {error}
          </div>
        )}
        {successMsg && (
          <div className="mt-6 flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl px-4 py-3 text-sm">
            <Check size={16} /> {successMsg}
          </div>
        )}

        {/* Sensor Cards Grid */}
        <section className="mt-10">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-black/60">Calibration Profiles</h2>
            <button
              onClick={fetchProfiles}
              className="flex items-center gap-2 text-sm text-black/40 hover:text-black/70 transition-colors"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>

          {loading && profiles.length === 0 ? (
            <div className="text-center text-black/30 py-20">Loading profiles...</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {profiles.map((p) => {
                const meta = SENSOR_META[p.sensor_type];
                if (!meta) return null;
                const Icon = meta.icon;
                const isSelected = selectedSensor === p.sensor_type;
                const isCalibrated = p.method !== "not_calibrated";

                return (
                  <button
                    key={p.sensor_type}
                    onClick={() => setSelectedSensor(isSelected ? null : p.sensor_type)}
                    className={clsx(
                      "text-left bg-white border shadow-sm rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1",
                      isSelected
                        ? `border-2 ${meta.borderClass} ring-2 ring-offset-2 ring-${meta.color}`
                        : "border-black/8 hover:border-black/15"
                    )}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className={clsx("p-2 rounded-lg border", meta.bgClass, meta.borderClass)}>
                        <Icon size={20} className={meta.textClass} />
                      </div>
                      <span
                        className={clsx(
                          "text-xs px-2 py-1 rounded-full border",
                          isCalibrated
                            ? "bg-emerald-50 border-emerald-200 text-emerald-600"
                            : "bg-red-50 border-red-200 text-red-500"
                        )}
                      >
                        {isCalibrated ? "Calibrated" : "Uncalibrated"}
                      </span>
                    </div>
                    <p className="text-xs text-black/40 uppercase tracking-widest">{meta.label}</p>
                    <p className="text-sm text-black/60 mt-1">
                      {METHOD_LABELS[p.method] || p.method}
                    </p>
                    {p.calibration_date && (
                      <p className="text-xs text-black/30 mt-2">
                        Last: {p.calibration_date}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </section>

        {/* Detail Panel */}
        {selectedSensor && fullProfile && (
          <section className="mt-10 space-y-8">
            <ProfileDetailPanel
              profile={fullProfile}
              sensorType={selectedSensor}
              onSave={async (updated) => {
                setSaving(true);
                setError(null);
                try {
                  const res = await fetch(
                    `${BACKEND_HTTP}/api/v1/calibration/profiles/${selectedSensor}`,
                    {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(updated),
                    }
                  );
                  if (!res.ok) throw new Error("Save failed");
                  const data = await res.json();
                  setFullProfile(data.profile);
                  setSuccessMsg(`${SENSOR_META[selectedSensor]?.label} profile saved.`);
                  fetchProfiles();
                } catch (err: any) {
                  setError(err.message);
                } finally {
                  setSaving(false);
                }
              }}
              saving={saving}
            />

            {/* Calibration Curve Chart */}
            <CalibrationCurveChart profile={fullProfile} sensorType={selectedSensor} />

            {/* Interpretation Bands */}
            {fullProfile.interpretation && (
              <InterpretationBands
                interpretation={fullProfile.interpretation}
                sensorType={selectedSensor}
              />
            )}

            {/* Wizard */}
            <div className="bg-white border border-black/8 shadow-sm rounded-2xl overflow-hidden">
              <button
                onClick={() => setWizardOpen(!wizardOpen)}
                className="w-full flex items-center justify-between p-6 hover:bg-black/[0.02] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Wand2 size={20} className="text-emerald-500" />
                  <span className="text-lg font-medium text-black/70">Calibration Wizard</span>
                </div>
                {wizardOpen ? <ChevronUp size={18} className="text-black/30" /> : <ChevronDown size={18} className="text-black/30" />}
              </button>

              {wizardOpen && (
                <CalibrationWizard
                  sensorType={selectedSensor}
                  method={fullProfile.calibration_method}
                  onCalibrated={(profile) => {
                    setFullProfile(profile);
                    setSuccessMsg("Calibration computed and saved!");
                    fetchProfiles();
                    setWizardOpen(false);
                  }}
                  onError={(msg) => setError(msg)}
                />
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

// â”€â”€ Profile Detail Panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function ProfileDetailPanel({
  profile,
  sensorType,
  onSave,
  saving,
}: {
  profile: CalibrationProfile;
  sensorType: string;
  onSave: (update: any) => void;
  saving: boolean;
}) {
  const meta = SENSOR_META[sensorType];
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    // Initialize form from profile
    setFormData({
      offset: profile.offset ?? "",
      multiplier: profile.multiplier ?? "",
      dry_value: profile.dry_value ?? "",
      wet_value: profile.wet_value ?? "",
      notes: profile.notes ?? "",
    });
    setEditMode(false);
  }, [profile]);

  const handleSave = () => {
    const update: any = {};
    if (profile.calibration_method === "offset_correction") {
      if (formData.offset !== "") update.offset = parseFloat(formData.offset);
      if (formData.multiplier !== "") update.multiplier = parseFloat(formData.multiplier);
    } else if (profile.calibration_method === "two_point_linear") {
      if (formData.dry_value !== "") update.dry_value = parseInt(formData.dry_value);
      if (formData.wet_value !== "") update.wet_value = parseInt(formData.wet_value);
    }
    if (formData.notes !== profile.notes) update.notes = formData.notes;
    onSave(update);
    setEditMode(false);
  };

  if (!meta) return null;
  const Icon = meta.icon;

  return (
    <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className={clsx("p-3 rounded-xl border", meta.bgClass, meta.borderClass)}>
            <Icon size={24} className={meta.textClass} />
          </div>
          <div>
            <h3 className="text-2xl font-medium text-black/80">{meta.label}</h3>
            <p className="text-sm text-black/40">
              {METHOD_LABELS[profile.calibration_method]} Â· Last calibrated{" "}
              {profile.calibration_date || "unknown"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {editMode ? (
            <>
              <button
                onClick={() => setEditMode(false)}
                className="px-4 py-2 text-sm rounded-lg border border-black/10 text-black/50 hover:text-black/70 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-colors disabled:opacity-50"
              >
                <Save size={14} />
                {saving ? "Saving..." : "Save"}
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditMode(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg border border-black/10 text-black/50 hover:text-black/70 hover:border-black/20 transition-colors"
            >
              <Settings2 size={14} />
              Edit
            </button>
          )}
        </div>
      </div>

      {/* Parameters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Method-specific fields */}
        {profile.calibration_method === "offset_correction" && (
          <>
            <ParamField
              label="Offset"
              value={editMode ? formData.offset : profile.offset}
              editable={editMode}
              onChange={(v) => setFormData({ ...formData, offset: v })}
              unit={meta.unit}
            />
            <ParamField
              label="Multiplier"
              value={editMode ? formData.multiplier : profile.multiplier}
              editable={editMode}
              onChange={(v) => setFormData({ ...formData, multiplier: v })}
              unit="Ã—"
            />
          </>
        )}
        {profile.calibration_method === "two_point_linear" && (
          <>
            <ParamField
              label="Dry Value (air)"
              value={editMode ? formData.dry_value : profile.dry_value}
              editable={editMode}
              onChange={(v) => setFormData({ ...formData, dry_value: v })}
              unit="ADC"
            />
            <ParamField
              label="Wet Value (water)"
              value={editMode ? formData.wet_value : profile.wet_value}
              editable={editMode}
              onChange={(v) => setFormData({ ...formData, wet_value: v })}
              unit="ADC"
            />
          </>
        )}
        {profile.calibration_method === "three_point_polynomial" && (
          <>
            {[1, 2, 3].map((i) => {
              const pt = (profile as any)[`point${i}`];
              if (!pt) return null;
              return (
                <div key={i} className="bg-black/[0.02] rounded-xl p-4">
                  <p className="text-xs text-black/40 uppercase tracking-widest mb-2">
                    Point {i}
                  </p>
                  <div className="flex justify-between text-sm">
                    <span className="text-black/50">Raw ADC</span>
                    <span className="font-mono text-black/80">{pt.raw}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-black/50">Actual</span>
                    <span className="font-mono text-black/80">
                      {pt.actual} {meta.unit}
                    </span>
                  </div>
                  {pt.buffer && (
                    <p className="text-xs text-black/30 mt-2">{pt.buffer}</p>
                  )}
                </div>
              );
            })}
          </>
        )}

        {/* Output Range */}
        {profile.conversion?.output_range && (
          <div className="bg-black/[0.02] rounded-xl p-4">
            <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Output Range</p>
            <p className="font-mono text-lg text-black/80">
              {profile.conversion.output_range.min} â€“ {profile.conversion.output_range.max}{" "}
              <span className="text-sm text-black/40">{profile.conversion.output_range.unit}</span>
            </p>
          </div>
        )}

        {/* Formula */}
        {profile.conversion?.formula && (
          <div className="bg-black/[0.02] rounded-xl p-4 md:col-span-2">
            <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Formula</p>
            <p className="font-mono text-sm text-black/70">{profile.conversion.formula}</p>
          </div>
        )}

        {/* Temperature Compensation (pH) */}
        {profile.temperature_compensation && (
          <div className="bg-violet-50 rounded-xl p-4 border border-violet-200/50">
            <p className="text-xs text-violet-500 uppercase tracking-widest mb-2">
              Temp Compensation
            </p>
            <p className="text-sm text-black/70">
              {profile.temperature_compensation.enabled ? "Enabled" : "Disabled"} Â· Ref:{" "}
              {profile.temperature_compensation.reference_temperature}Â°C
            </p>
            <p className="font-mono text-xs text-black/40 mt-1">
              {profile.temperature_compensation.formula}
            </p>
          </div>
        )}

        {/* Notes */}
        <div className="bg-black/[0.02] rounded-xl p-4 md:col-span-2 lg:col-span-3">
          <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Notes</p>
          {editMode ? (
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full text-sm text-black/70 bg-white border border-black/10 rounded-lg p-3 resize-none focus:outline-none focus:border-emerald-500/50"
              rows={2}
            />
          ) : (
            <p className="text-sm text-black/60">{profile.notes || "No notes"}</p>
          )}
        </div>
      </div>

      {/* Reference Points Table */}
      {profile.reference_points && profile.reference_points.length > 0 && (
        <div className="mt-6">
          <p className="text-xs text-black/40 uppercase tracking-widest mb-3">Reference Points</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-black/8">
                  <th className="text-left py-2 text-black/40 font-medium">Reference</th>
                  <th className="text-left py-2 text-black/40 font-medium">Measured</th>
                  <th className="text-left py-2 text-black/40 font-medium">Condition</th>
                </tr>
              </thead>
              <tbody>
                {profile.reference_points.map((rp, i) => (
                  <tr key={i} className="border-b border-black/5">
                    <td className="py-2 font-mono text-black/70">
                      {rp.reference} {meta?.unit}
                    </td>
                    <td className="py-2 font-mono text-black/70">{rp.measured}</td>
                    <td className="py-2 text-black/50">{rp.condition || "â€”"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// â”€â”€ Parameter Field â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function ParamField({
  label,
  value,
  editable,
  onChange,
  unit,
}: {
  label: string;
  value: any;
  editable: boolean;
  onChange?: (v: string) => void;
  unit: string;
}) {
  return (
    <div className="bg-black/[0.02] rounded-xl p-4">
      <p className="text-xs text-black/40 uppercase tracking-widest mb-2">{label}</p>
      {editable ? (
        <div className="flex items-baseline gap-2">
          <input
            type="number"
            step="any"
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            className="w-full text-2xl font-mono text-black/80 bg-white border border-black/10 rounded-lg px-3 py-1 focus:outline-none focus:border-emerald-500/50"
          />
          <span className="text-sm text-black/40 whitespace-nowrap">{unit}</span>
        </div>
      ) : (
        <p className="text-2xl font-mono text-black/80">
          {value ?? "â€”"}{" "}
          <span className="text-sm text-black/40">{unit}</span>
        </p>
      )}
    </div>
  );
}

// â”€â”€ Calibration Curve Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function CalibrationCurveChart({
  profile,
  sensorType,
}: {
  profile: CalibrationProfile;
  sensorType: string;
}) {
  const meta = SENSOR_META[sensorType];
  if (!meta) return null;

  // Generate calibration curve data
  let curveData: { raw: number; calibrated: number }[] = [];
  let refPoints: { raw: number; calibrated: number }[] = [];

  if (profile.calibration_method === "offset_correction") {
    const offset = profile.offset ?? 0;
    const multiplier = profile.multiplier ?? 1;
    for (let raw = 0; raw <= 4095; raw += 100) {
      curveData.push({ raw, calibrated: parseFloat((raw * multiplier + offset).toFixed(2)) });
    }
    if (profile.reference_points) {
      refPoints = profile.reference_points.map((rp) => ({
        raw: rp.measured,
        calibrated: rp.reference,
      }));
    }
  } else if (profile.calibration_method === "two_point_linear") {
    const dry = profile.dry_value ?? 3200;
    const wet = profile.wet_value ?? 1200;
    for (let raw = 0; raw <= 4095; raw += 100) {
      const pct = ((raw - dry) / (wet - dry)) * 100;
      curveData.push({ raw, calibrated: parseFloat(Math.max(0, Math.min(100, pct)).toFixed(1)) });
    }
    refPoints = [
      { raw: dry, calibrated: 0 },
      { raw: wet, calibrated: 100 },
    ];
  } else if (profile.calibration_method === "three_point_polynomial") {
    const p1 = profile.point1;
    const p2 = profile.point2;
    const p3 = profile.point3;
    if (p1 && p2 && p3) {
      // Lagrange interpolation
      const lagrange = (x: number) => {
        const l0 =
          ((x - p2.raw) * (x - p3.raw)) /
          ((p1.raw - p2.raw) * (p1.raw - p3.raw));
        const l1 =
          ((x - p1.raw) * (x - p3.raw)) /
          ((p2.raw - p1.raw) * (p2.raw - p3.raw));
        const l2 =
          ((x - p1.raw) * (x - p2.raw)) /
          ((p3.raw - p1.raw) * (p3.raw - p2.raw));
        return p1.actual * l0 + p2.actual * l1 + p3.actual * l2;
      };
      const minRaw = Math.min(p1.raw, p2.raw, p3.raw) - 200;
      const maxRaw = Math.max(p1.raw, p2.raw, p3.raw) + 200;
      for (let raw = minRaw; raw <= maxRaw; raw += 20) {
        curveData.push({ raw, calibrated: parseFloat(lagrange(raw).toFixed(2)) });
      }
      refPoints = [
        { raw: p1.raw, calibrated: p1.actual },
        { raw: p2.raw, calibrated: p2.actual },
        { raw: p3.raw, calibrated: p3.actual },
      ];
    }
  }

  if (curveData.length === 0) return null;

  return (
    <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-8">
      <h4 className="text-lg font-medium text-black/70 mb-6">Calibration Curve</h4>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={curveData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="raw"
              label={{ value: "Raw ADC", position: "insideBottom", offset: -5, fill: "#9ca3af" }}
              tick={{ fill: "#9ca3af", fontSize: 12 }}
            />
            <YAxis
              label={{
                value: `Calibrated (${meta.unit})`,
                angle: -90,
                position: "insideLeft",
                offset: 10,
                fill: "#9ca3af",
              }}
              tick={{ fill: "#9ca3af", fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                fontSize: "13px",
              }}
              formatter={(value: any) => [`${value} ${meta.unit}`, "Calibrated"]}
              labelFormatter={(label) => `Raw ADC: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="calibrated"
              stroke={meta.color}
              strokeWidth={2}
              dot={false}
            />
            {refPoints.map((rp, i) => (
              <ReferenceLine
                key={i}
                x={rp.raw}
                stroke={meta.color}
                strokeDasharray="4 4"
                opacity={0.5}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {refPoints.length > 0 && (
        <div className="flex gap-4 mt-4 justify-center">
          {refPoints.map((rp, i) => (
            <span key={i} className="text-xs text-black/40 font-mono">
              ({rp.raw} â†’ {rp.calibrated} {meta.unit})
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// â”€â”€ Interpretation Bands â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function InterpretationBands({
  interpretation,
  sensorType,
}: {
  interpretation: Record<string, [number, number]>;
  sensorType: string;
}) {
  const meta = SENSOR_META[sensorType];
  if (!meta) return null;

  const bandColors: Record<string, string> = {
    very_dry: "bg-red-400",
    dry: "bg-orange-400",
    optimal: "bg-emerald-400",
    wet: "bg-blue-400",
    saturated: "bg-blue-600",
    very_acidic: "bg-red-500",
    acidic: "bg-orange-400",
    alkaline: "bg-blue-400",
    very_alkaline: "bg-indigo-500",
  };

  const entries = Object.entries(interpretation);
  const allMin = Math.min(...entries.map(([, [a]]) => a));
  const allMax = Math.max(...entries.map(([, [, b]]) => b));
  const range = allMax - allMin || 1;

  return (
    <div className="bg-white border border-black/8 shadow-sm rounded-2xl p-8">
      <h4 className="text-lg font-medium text-black/70 mb-6">Interpretation Bands</h4>

      {/* Visual bar */}
      <div className="relative h-8 rounded-full overflow-hidden flex">
        {entries.map(([name, [min, max]]) => {
          const widthPct = ((max - min) / range) * 100;
          return (
            <div
              key={name}
              className={clsx("h-full", bandColors[name] || "bg-gray-300")}
              style={{ width: `${widthPct}%` }}
              title={`${name}: ${min}â€“${max}`}
            />
          );
        })}
      </div>

      {/* Labels */}
      <div className="flex mt-4 gap-4 flex-wrap">
        {entries.map(([name, [min, max]]) => (
          <div key={name} className="flex items-center gap-2">
            <div className={clsx("w-3 h-3 rounded-full", bandColors[name] || "bg-gray-300")} />
            <span className="text-xs text-black/50 capitalize">
              {name.replace(/_/g, " ")}{" "}
              <span className="font-mono text-black/30">
                ({min}â€“{max})
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// â”€â”€ Calibration Wizard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function CalibrationWizard({
  sensorType,
  method,
  onCalibrated,
  onError,
}: {
  sensorType: string;
  method: string;
  onCalibrated: (profile: CalibrationProfile) => void;
  onError: (msg: string) => void;
}) {
  const meta = SENSOR_META[sensorType];

  // Guided sensors use reference-value offset correction
  const isGuidedOffset = ["temperature", "humidity", "light"].includes(sensorType);
  const isSoil = sensorType === "soil_moisture";

  // Live sensor data (polled every 3 s)
  const [liveData, setLiveData] = useState<Record<string, any> | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Offset correction state
  const [referenceValue, setReferenceValue] = useState("");

  // Soil two-point state
  const [soilStep, setSoilStep] = useState<1 | 2 | 3>(1);
  const [wetRaw, setWetRaw] = useState<number | null>(null);
  const [dryRaw, setDryRaw] = useState<number | null>(null);

  // Generic wizard state (for pH)
  const [selectedMethod, setSelectedMethod] = useState(method);
  const [points, setPoints] = useState<WizardPoint[]>([{ raw: "", actual: "", condition: "" }]);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchLive = async () => {
    setLiveLoading(true);
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/v1/sensors/latest/raw`);
      if (res.ok) setLiveData(await res.json());
    } catch {}
    setLiveLoading(false);
  };

  useEffect(() => {
    if (isGuidedOffset || isSoil) {
      fetchLive();
      pollRef.current = setInterval(fetchLive, 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const liveRawSoil = (liveData?.raw_soil as number) ?? null;
  const currentLiveValue =
    sensorType === "temperature" ? (liveData?.temperature as number) ?? null
    : sensorType === "humidity" ? (liveData?.humidity as number) ?? null
    : sensorType === "light" ? (liveData?.light_level as number) ?? null
    : null;

  const computedOffset =
    currentLiveValue !== null && referenceValue !== ""
      ? parseFloat(referenceValue) - currentLiveValue
      : null;

  const referenceHint =
    sensorType === "temperature" ? "e.g. 27.5 â€” from a reference thermometer"
    : sensorType === "humidity" ? "e.g. 65 â€” from a hygrometer or weather station"
    : "e.g. 500 â€” lux reading from your phone's light meter app";

  const referenceSubtitle =
    sensorType === "temperature"
      ? "Place a reference thermometer next to the sensor and note its value."
      : sensorType === "humidity"
      ? "Check a reference hygrometer, weather station, or weather app for the current humidity."
      : "Open a Lux Meter app on your phone and read the lux value at the sensor location.";

  const postWizard = async (body: object) => {
    const res = await fetch(`${BACKEND_HTTP}/api/v1/calibration/wizard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Failed"); }
    return (await res.json()).profile as CalibrationProfile;
  };

  const handleOffsetCalibrate = async () => {
    if (currentLiveValue === null || !referenceValue) return;
    setLoading(true);
    try {
      onCalibrated(await postWizard({
        sensor_type: sensorType, method: "offset_correction",
        points: [{ raw: currentLiveValue, actual: parseFloat(referenceValue), condition: "Reference device measurement" }],
        notes: `Reference calibration â€” ${new Date().toISOString().split("T")[0]}`,
      }));
    } catch (e: any) { onError(e.message); setLoading(false); }
  };

  const handleSoilCalibrate = async () => {
    if (wetRaw === null || dryRaw === null) return;
    setLoading(true);
    try {
      onCalibrated(await postWizard({
        sensor_type: "soil_moisture", method: "two_point_linear",
        points: [
          { raw: wetRaw, actual: 100, condition: "Sensor fully submerged in water" },
          { raw: dryRaw, actual: 0, condition: "Sensor in open air" },
        ],
        notes: `Two-point calibration â€” ${new Date().toISOString().split("T")[0]}`,
      }));
    } catch (e: any) { onError(e.message); setLoading(false); }
  };

  // Generic wizard (pH and others)
  const pointCount =
    selectedMethod === "three_point_polynomial" ? 3
    : selectedMethod === "two_point_linear" ? 2 : 1;

  useEffect(() => {
    setPoints((prev) => {
      const n = [...prev];
      while (n.length < pointCount) n.push({ raw: "", actual: "", condition: "" });
      return n.slice(0, Math.max(pointCount, 1));
    });
  }, [selectedMethod, pointCount]);

  const canSubmitGeneric = points.slice(0, pointCount).every((p) => p.raw !== "" && p.actual !== "");

  const handleGenericCalibrate = async () => {
    setLoading(true);
    try {
      onCalibrated(await postWizard({
        sensor_type: sensorType, method: selectedMethod,
        points: points.slice(0, pointCount).map((p) => ({
          raw: parseFloat(p.raw), actual: parseFloat(p.actual), condition: p.condition,
        })),
        notes,
      }));
    } catch (e: any) { onError(e.message); } finally { setLoading(false); }
  };

  // Live badge helper
  const LiveBadge = () => (
    <button
      onClick={fetchLive}
      className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-emerald-500/30 text-emerald-600 hover:bg-emerald-50 transition-colors"
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full bg-emerald-500", liveLoading ? "opacity-40" : "animate-pulse")} />
      {liveLoading ? "..." : "LIVE"}
    </button>
  );

  // â”€â”€ Guided: Offset Correction (temp / humidity / light) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  if (isGuidedOffset) {
    return (
      <div className="px-6 pb-6 pt-6 border-t border-black/5 space-y-6">
        {/* Tip */}
        <div className="flex items-start gap-3 bg-black/[0.02] border border-black/5 rounded-xl p-4">
          <span className="text-blue-500 text-base mt-0.5">â„¹</span>
          <p className="text-sm text-black/60 leading-relaxed">{referenceSubtitle}</p>
        </div>

        {/* Current reading */}
        <div>
          <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Current Sensor Reading</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-mono font-bold" style={{ color: meta?.color }}>
              {currentLiveValue !== null ? `${currentLiveValue.toFixed(1)} ${meta?.unit}` : "â€”"}
            </span>
            <LiveBadge />
          </div>
        </div>

        {/* Reference input */}
        <div>
          <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Reference Value (from external device)</p>
          <div className="flex items-center gap-3">
            <input
              type="number" step="any"
              value={referenceValue}
              onChange={(e) => setReferenceValue(e.target.value)}
              placeholder={referenceHint}
              className="flex-1 px-3 py-2.5 text-base font-mono border border-black/10 rounded-xl focus:outline-none focus:border-emerald-500/50"
            />
            <span className="text-sm text-black/40 w-10 shrink-0">{meta?.unit}</span>
          </div>
        </div>

        {/* Computed offset */}
        {computedOffset !== null && (
          <div className="bg-black/[0.02] border border-black/5 rounded-xl p-4 space-y-2">
            <p className="text-xs font-semibold text-black/50 uppercase tracking-widest">Computed Calibration</p>
            <div className="flex justify-between items-center">
              <span className="text-sm text-black/50">Offset</span>
              <span className={clsx("font-mono font-bold text-base",
                computedOffset > 0.005 ? "text-green-600"
                : computedOffset < -0.005 ? "text-orange-600"
                : "text-gray-400")}>
                {computedOffset >= 0 ? "+" : ""}{computedOffset.toFixed(2)} {meta?.unit}
              </span>
            </div>
            <p className="text-xs font-mono text-black/30">
              calibrated = reading {computedOffset >= 0 ? "+" : ""}{computedOffset.toFixed(2)}
            </p>
          </div>
        )}

        <button
          onClick={handleOffsetCalibrate}
          disabled={currentLiveValue === null || !referenceValue || loading}
          className={clsx(
            "flex items-center gap-2 w-full justify-center px-6 py-3 rounded-xl text-sm font-medium transition-all",
            currentLiveValue !== null && referenceValue
              ? "bg-emerald-500 text-white hover:bg-emerald-600 shadow-sm"
              : "bg-black/5 text-black/30 cursor-not-allowed"
          )}
        >
          <Wand2 size={16} />
          {loading ? "Applying..." : "Apply Calibration"}
        </button>
      </div>
    );
  }

  // â”€â”€ Guided: Soil Moisture Two-Point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  if (isSoil) {
    const hasRaw = liveRawSoil !== null;

    if (soilStep === 3) {
      return (
        <div className="px-6 pb-6 pt-6 border-t border-black/5 space-y-6">
          <p className="text-xs text-black/40 uppercase tracking-widest">Calibration Summary</p>
          <div className="bg-black/[0.02] border border-black/5 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm flex items-center gap-2">ðŸ’§ Wet point (100%)</span>
              <span className="font-mono font-bold text-blue-600">{wetRaw} ADC</span>
            </div>
            <hr className="border-black/5" />
            <div className="flex justify-between items-center">
              <span className="text-sm flex items-center gap-2">ðŸ’¨ Dry point (0%)</span>
              <span className="font-mono font-bold text-orange-600">{dryRaw} ADC</span>
            </div>
          </div>
          <div className="bg-black/[0.02] rounded-xl px-4 py-3">
            <p className="text-xs font-mono text-black/40">
              moisture% = (raw âˆ’ {dryRaw}) / ({wetRaw} âˆ’ {dryRaw}) Ã— 100
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => { setSoilStep(1); setWetRaw(null); setDryRaw(null); }}
              className="px-4 py-2.5 rounded-xl border border-black/10 text-sm text-black/50 hover:border-black/20 transition-colors"
            >
              Start Over
            </button>
            <button
              onClick={handleSoilCalibrate}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 transition-all disabled:opacity-50"
            >
              <Wand2 size={16} />
              {loading ? "Applying..." : "Apply Calibration"}
            </button>
          </div>
        </div>
      );
    }

    const isWetStep = soilStep === 1;
    return (
      <div className="px-6 pb-6 pt-6 border-t border-black/5 space-y-6">
        {/* Step progress */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-sm font-bold">
            {isWetStep ? "1" : <Check size={14} />}
          </div>
          <div className={clsx("flex-1 h-1 rounded", isWetStep ? "bg-black/10" : "bg-emerald-500")} />
          <div className={clsx("w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
            !isWetStep ? "bg-emerald-500 text-white" : "bg-black/10 text-black/30")}>
            2
          </div>
        </div>

        {/* Instruction */}
        <div className={clsx("rounded-xl p-4 border space-y-1",
          isWetStep ? "bg-blue-50 border-blue-200" : "bg-orange-50 border-orange-200")}>
          <p className={clsx("font-semibold", isWetStep ? "text-blue-800" : "text-orange-800")}>
            {isWetStep ? "ðŸ’§ Submerge sensor in water" : "ðŸ’¨ Hold sensor in open air"}
          </p>
          <p className={clsx("text-sm", isWetStep ? "text-blue-600" : "text-orange-600")}>
            {isWetStep
              ? "Place the probe fully in water and wait ~10 seconds for the reading to stabilise."
              : "Remove the sensor from water and hold it in open air. Wait ~10 seconds until settled."}
          </p>
        </div>

        {/* Live raw ADC */}
        <div>
          <p className="text-xs text-black/40 uppercase tracking-widest mb-2">Live Raw ADC Reading</p>
          <div className="flex items-end gap-3">
            <span className="text-4xl font-mono font-bold text-emerald-600">
              {hasRaw ? liveRawSoil : "â€”"}
            </span>
            <span className="text-sm text-black/40 mb-1">/ 4095</span>
            <div className="ml-auto"><LiveBadge /></div>
          </div>
          {!hasRaw && (
            <p className="text-xs text-amber-600 mt-2">
              âš  Raw ADC not yet available. Ensure the updated ESP32 firmware is running and sending data.
            </p>
          )}
        </div>

        <button
          onClick={() => {
            if (!hasRaw) return;
            if (isWetStep) { setWetRaw(liveRawSoil!); setSoilStep(2); }
            else { setDryRaw(liveRawSoil!); setSoilStep(3); }
          }}
          disabled={!hasRaw}
          className={clsx(
            "flex items-center gap-2 w-full justify-center px-6 py-3 rounded-xl text-sm font-medium transition-all",
            hasRaw
              ? isWetStep
                ? "bg-blue-500 text-white hover:bg-blue-600 shadow-sm"
                : "bg-orange-500 text-white hover:bg-orange-600 shadow-sm"
              : "bg-black/5 text-black/30 cursor-not-allowed"
          )}
        >
          {isWetStep
            ? `ðŸ’§ Record Wet Point${hasRaw ? ` (${liveRawSoil} ADC)` : ""}`
            : `ðŸ’¨ Record Dry Point${hasRaw ? ` (${liveRawSoil} ADC)` : ""}`}
        </button>
      </div>
    );
  }

  // â”€â”€ Generic Wizard (pH and others) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const conditionHints: Record<string, string[]> = {
    offset_correction: ["e.g. Room temperature, Ice bath, Known reference"],
    two_point_linear: ["Sensor in air (dry)", "Sensor in water (wet)"],
    three_point_polynomial: ["pH 4.0 buffer", "pH 7.0 buffer", "pH 10.0 buffer"],
  };

  return (
    <div className="px-6 pb-6 space-y-6 border-t border-black/5 pt-6">
      <p className="text-sm text-black/50">
        Enter raw ADC readings and known reference values. The system will compute calibration parameters automatically.
      </p>
      <div>
        <label className="text-xs text-black/40 uppercase tracking-widest">Method</label>
        <div className="flex gap-3 mt-2">
          {[
            { id: "offset_correction", label: "Offset", pts: "1â€“3 pts" },
            { id: "two_point_linear", label: "Two-Point", pts: "2 pts" },
            { id: "three_point_polynomial", label: "Three-Point", pts: "3 pts" },
          ].map((m) => (
            <button key={m.id} onClick={() => setSelectedMethod(m.id)}
              className={clsx("px-4 py-2 rounded-lg text-sm border transition-colors",
                selectedMethod === m.id
                  ? "bg-emerald-50 border-emerald-300 text-emerald-700"
                  : "border-black/10 text-black/50 hover:border-black/20")}>
              {m.label} <span className="text-xs text-black/30">({m.pts})</span>
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-4">
        <label className="text-xs text-black/40 uppercase tracking-widest">Reference Points</label>
        {points.slice(0, pointCount).map((pt, i) => (
          <div key={i} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-black/30">Raw ADC</label>
              <input type="number" value={pt.raw}
                onChange={(e) => { const n=[...points]; n[i]={...n[i],raw:e.target.value}; setPoints(n); }}
                placeholder="e.g. 2015"
                className="w-full mt-1 px-3 py-2 text-sm border border-black/10 rounded-lg focus:outline-none focus:border-emerald-500/50 font-mono" />
            </div>
            <div>
              <label className="text-xs text-black/30">Known Value ({meta?.unit})</label>
              <input type="number" step="any" value={pt.actual}
                onChange={(e) => { const n=[...points]; n[i]={...n[i],actual:e.target.value}; setPoints(n); }}
                placeholder="e.g. 7.0"
                className="w-full mt-1 px-3 py-2 text-sm border border-black/10 rounded-lg focus:outline-none focus:border-emerald-500/50 font-mono" />
            </div>
            <div>
              <label className="text-xs text-black/30">Condition</label>
              <input type="text" value={pt.condition}
                onChange={(e) => { const n=[...points]; n[i]={...n[i],condition:e.target.value}; setPoints(n); }}
                placeholder={conditionHints[selectedMethod]?.[i] || "Describe condition"}
                className="w-full mt-1 px-3 py-2 text-sm border border-black/10 rounded-lg focus:outline-none focus:border-emerald-500/50" />
            </div>
          </div>
        ))}
        {selectedMethod === "offset_correction" && points.length < 3 && (
          <button onClick={() => setPoints([...points, { raw: "", actual: "", condition: "" }])}
            className="text-sm text-emerald-600 hover:text-emerald-700">
            + Add reference point
          </button>
        )}
      </div>
      <div>
        <label className="text-xs text-black/40 uppercase tracking-widest">Notes (optional)</label>
        <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g. Calibrated with fresh buffer solutions at 25Â°C"
          className="w-full mt-2 px-3 py-2 text-sm border border-black/10 rounded-lg focus:outline-none focus:border-emerald-500/50" />
      </div>
      <button onClick={handleGenericCalibrate} disabled={!canSubmitGeneric || loading}
        className={clsx("flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all",
          canSubmitGeneric
            ? "bg-emerald-500 text-white hover:bg-emerald-600 shadow-sm"
            : "bg-black/5 text-black/30 cursor-not-allowed")}>
        <Wand2 size={16} />
        {loading ? "Computing..." : "Compute & Save Calibration"}
      </button>
    </div>
  );
}
