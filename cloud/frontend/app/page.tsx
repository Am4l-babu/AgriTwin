"use client";

import { useScroll, useTransform, useMotionValueEvent } from "framer-motion";
import { useRef, useState } from "react";
import PlantDive from "@/components/PlantDive";
import TelemetryOverlay from "@/components/TelemetryOverlay";
import DashboardSection from "@/components/DashboardSection";
import HistoryCharts from "@/components/HistoryCharts";

export default function Home() {
    const containerRef = useRef<HTMLDivElement>(null);
    const [telemetryVisible, setTelemetryVisible] = useState(true);

    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"],
    });

    // Telemetry fade out logic: visible at start, fades out by 10% scroll
    useMotionValueEvent(scrollYProgress, "change", (latest) => {
        if (latest > 0.05 && telemetryVisible) {
            setTelemetryVisible(false);
        } else if (latest <= 0.05 && !telemetryVisible) {
            setTelemetryVisible(true);
        }
    });

    return (
        <main ref={containerRef} className="relative bg-black min-h-screen">
            {/* Fixed Telemetry Overlay */}
            <TelemetryOverlay visible={telemetryVisible} />

            {/* Scrollytelling Section */}
            {/* 
         This section needs to be tall enough to drive the animation.
         PlantDive contains a sticky canvas. 
       */}
            <PlantDive />

            {/* Dashboard Section */}
            {/* 
         Appears naturally after the PlantDive relative container ends.
         Since PlantDive is 500vh tall with sticky content, this will appear
         after 500vh of scrolling.
       */}
            <DashboardSection />

            {/* Historical Charts Section */}
            <HistoryCharts />



        </main>
    );
}
