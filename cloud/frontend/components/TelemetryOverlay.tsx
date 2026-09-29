"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx } from "clsx";
import { useSensorData } from "../app/context/SensorContext";

export default function TelemetryOverlay({
  visible = true,
}: {
  visible?: boolean;
}) {
  // Get real-time sensor data from ESP32 via WebSocket
  const { sensorData, isConnected } = useSensorData();

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.8 } }}
          className="fixed inset-0 pointer-events-none z-50"
        >
          {/* Connection Status Indicator */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/10 backdrop-blur-sm px-4 py-2 rounded-full">
            <div className={clsx("w-2 h-2 rounded-full", isConnected ? "bg-emerald-400 animate-pulse" : "bg-red-400")} />
            <span className="text-xs font-medium text-black/60">
              {isConnected ? "ESP32 Connected" : "Disconnected"}
            </span>
          </div>

          {/* Top Left: Soil Moisture */}
          <CornerMetric
            position="top-left"
            label="SOIL MOISTURE"
            value={sensorData.soil}
            unit="%"
            color="text-emerald-400"
          />

          {/* Top Right: Temperature */}
          <CornerMetric
            position="top-right"
            label="TEMPERATURE"
            value={sensorData.temp}
            unit="°C"
            color="text-amber-400"
          />

          {/* Bottom Left: Humidity */}
          <CornerMetric
            position="bottom-left"
            label="HUMIDITY"
            value={sensorData.humidity}
            unit="%"
            color="text-cyan-400"
          />

          {/* Bottom Right: Light */}
          <CornerMetric
            position="bottom-right"
            label="LIGHT INTENSITY"
            value={sensorData.light}
            unit="lux"
            color="text-yellow-200"
            isInteger
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function CornerMetric({
  position,
  label,
  value,
  unit,
  color,
  isInteger = false,
}: {
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  label: string;
  value: number;
  unit: string;
  color: string;
  isInteger?: boolean;
}) {
  const alignment = position.includes("left") ? "items-start" : "items-end";
  const vertical = position.includes("top") ? "top-8" : "bottom-8";
  const horizontal = position.includes("left") ? "left-8" : "right-8";

  // Arrow direction logic
  const arrowRotation = {
    "top-left": "rotate(135deg)",
    "top-right": "rotate(-135deg)",
    "bottom-left": "rotate(45deg)",
    "bottom-right": "rotate(-45deg)",
  };

  return (
    <div className={clsx("absolute flex flex-col gap-2", vertical, horizontal, alignment)}>
      <motion.div
        layout
        className="flex items-baseline gap-1"
      >
        <span className={clsx("text-sm font-bold tracking-widest text-black/60 uppercase")}>
          {label}
        </span>
      </motion.div>

      <div className="flex items-baseline gap-1">
        <NumberTicker value={value} isInteger={isInteger} className={clsx("text-6xl font-mono font-bold tabular-nums", "text-black")} />
        <span className="text-xl font-medium text-black/60">{unit}</span>
      </div>

      {/* Decorative Line/Arrow pointing to center */}
      <svg
        width="150"
        height="150"
        className="absolute opacity-80"
        style={{
          transform: arrowRotation[position],
          [position.includes('top') ? 'top' : 'bottom']: '3rem',
          [position.includes('left') ? 'left' : 'right']: '3rem',
          pointerEvents: 'none'
        }}
      >
        <line x1="0" y1="50" x2="100" y2="50" stroke="black" strokeWidth="2" className="opacity-100" />
        <circle cx="100" cy="50" r="3" fill="black" />
      </svg>
    </div>
  );
}

function NumberTicker({ value, className, isInteger }: { value: number; className?: string; isInteger?: boolean }) {
  // Simple animated number component using native DOM for performance if needed, 
  // but for now standard React render is fine for 2s updates.
  // We format it nicely.
  const displayValue = isInteger ? Math.round(value).toLocaleString() : value.toFixed(1);

  return (
    <motion.span
      key={displayValue} // Key change triggers animation
      initial={{ opacity: 0.5, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      {displayValue}
    </motion.span>
  );
}
