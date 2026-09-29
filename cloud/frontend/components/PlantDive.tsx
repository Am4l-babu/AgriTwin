"use client";

import { useEffect, useRef, useState } from "react";
import { useScroll, useTransform, motion } from "framer-motion";

const TOTAL_FRAMES = 96;
const FRAME_PATH = (n: number) =>
    `/frames/frame_${String(n).padStart(4, "0")}.png`;

const API_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";

// Fallback / initial values shown before API responds
const DEFAULT_METRICS = [
    { position: "top-left" as const,    label: "GROWTH STAGE",       value: "Vegetative", sub: "Day 14",    color: "text-emerald-400" },
    { position: "top-right" as const,   label: "WATER DEFICIT",      value: "12.3",       sub: "mm",        color: "text-cyan-400" },
    { position: "bottom-left" as const, label: "EVAPOTRANSPIRATION", value: "4.2",        sub: "mm/day",    color: "text-amber-400" },
    { position: "bottom-right" as const,label: "GDD ACCUMULATION",   value: "284",        sub: "°C·d",      color: "text-violet-400" },
];

export default function PlantDive() {
    const containerRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imagesRef = useRef<HTMLImageElement[]>([]);
    const currentFrameRef = useRef(0);
    const rafRef = useRef<number | null>(null);

    const [metrics, setMetrics] = useState(DEFAULT_METRICS);

    // Fetch live physics values from DT Brain
    useEffect(() => {
        fetch(`${API_URL}/api/v1/twin-accuracy/brain?farm_id=farm_001&hours=24`)
            .then((r) => r.json())
            .then((data) => {
                const models = data?.physics_models ?? {};
                const m1 = models["1_soil_moisture_balance"] ?? {};
                const m4 = models["4_light_influence"] ?? {};
                const et = m1.evapotranspiration_mmday ?? null;
                const deficit = m1.water_deficit_mm ?? null;
                const stage = (m4.growth_stage ?? "").replace(/^\w/, (c: string) => c.toUpperCase()) || null;
                const gdd = data?.gdd_accumulated_Cd ?? null;

                if (et === null && deficit === null) return; // no data yet

                setMetrics([
                    {
                        position: "top-left",
                        label: "GROWTH STAGE",
                        value: stage ?? "Vegetative",
                        sub: gdd !== null ? `${gdd} °C·d` : "Day 14",
                        color: "text-emerald-400",
                    },
                    {
                        position: "top-right",
                        label: "WATER DEFICIT",
                        value: deficit !== null ? deficit.toFixed(1) : "—",
                        sub: "mm",
                        color: "text-cyan-400",
                    },
                    {
                        position: "bottom-left",
                        label: "EVAPOTRANSPIRATION",
                        value: et !== null ? et.toFixed(1) : "—",
                        sub: "mm/day",
                        color: "text-amber-400",
                    },
                    {
                        position: "bottom-right",
                        label: "GDD ACCUMULATION",
                        value: gdd !== null ? String(gdd) : "—",
                        sub: "°C·d",
                        color: "text-violet-400",
                    },
                ]);
            })
            .catch(() => { /* keep defaults on error */ });
    }, []);

    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"],
    });

    // Top metrics: slide in from above (negative y → 0)
    const topY = useTransform(scrollYProgress, [0.78, 0.98], [-80, 0]);
    const topOpacity = useTransform(scrollYProgress, [0.78, 0.95], [0, 1]);

    // Bottom metrics: slide in from below (positive y → 0)
    const bottomY = useTransform(scrollYProgress, [0.78, 0.98], [80, 0]);
    const bottomOpacity = useTransform(scrollYProgress, [0.78, 0.95], [0, 1]);

    // Preload all frames
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const setSize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        setSize();
        window.addEventListener("resize", setSize);

        const images: HTMLImageElement[] = [];

        for (let i = 1; i <= TOTAL_FRAMES; i++) {
            const img = new Image();
            img.src = FRAME_PATH(i);
            img.onload = () => {
                if (i === 1) drawFrame(ctx, canvas, img);
            };
            images.push(img);
        }

        imagesRef.current = images;

        return () => {
            window.removeEventListener("resize", setSize);
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
        };
    }, []);

    // Drive animation from scroll progress
    useEffect(() => {
        const unsubscribe = scrollYProgress.on("change", (progress) => {
            const frameIndex = Math.min(
                TOTAL_FRAMES - 1,
                Math.max(0, Math.round(progress * (TOTAL_FRAMES - 1)))
            );

            if (frameIndex === currentFrameRef.current) return;
            currentFrameRef.current = frameIndex;

            const canvas = canvasRef.current;
            const img = imagesRef.current[frameIndex];
            if (!canvas || !img || !img.complete) return;

            const ctx = canvas.getContext("2d");
            if (!ctx) return;

            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            rafRef.current = requestAnimationFrame(() => {
                drawFrame(ctx, canvas, img);
            });
        });

        return () => unsubscribe();
    }, [scrollYProgress]);

    return (
        <div ref={containerRef} className="relative" style={{ height: "500vh" }}>
            <div className="sticky top-0 h-screen w-full overflow-hidden bg-black">
                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full"
                    style={{ objectFit: "cover" }}
                />

                {/* End-of-scroll corner metrics */}
                {metrics.map((metric) => {
                    const isTop = metric.position.startsWith("top");
                    const isLeft = metric.position.endsWith("left");
                    const y = isTop ? topY : bottomY;
                    const opacity = isTop ? topOpacity : bottomOpacity;

                    return (
                        <motion.div
                            key={metric.label}
                            style={{ opacity, y }}
                            className={`absolute pointer-events-none select-none flex flex-col gap-1 ${isTop ? "top-8" : "bottom-8"
                                } ${isLeft ? "left-8 items-start" : "right-8 items-end"}`}
                        >
                            {/* Label */}
                            <span className="text-xs font-bold tracking-[0.25em] text-black/60 uppercase">
                                {metric.label}
                            </span>

                            {/* Value + unit */}
                            <div className="flex items-baseline gap-1.5">
                                <span className="text-5xl font-mono font-bold text-black leading-none">
                                    {metric.value}
                                </span>
                                <span className="text-base font-medium text-black/50">
                                    {metric.sub}
                                </span>
                            </div>


                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}

function drawFrame(
    ctx: CanvasRenderingContext2D,
    canvas: HTMLCanvasElement,
    img: HTMLImageElement
) {
    const { width, height } = canvas;
    const imgAspect = img.naturalWidth / img.naturalHeight;
    const canvasAspect = width / height;

    let sx = 0, sy = 0, sw = img.naturalWidth, sh = img.naturalHeight;

    if (imgAspect > canvasAspect) {
        sw = img.naturalHeight * canvasAspect;
        sx = (img.naturalWidth - sw) / 2;
    } else {
        sh = img.naturalWidth / canvasAspect;
        sy = (img.naturalHeight - sh) / 2;
    }

    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, width, height);
}
