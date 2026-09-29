"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { Camera, RefreshCw, ArrowLeft, Wifi, WifiOff, Trash2, ZoomIn } from "lucide-react";

const API_BASE =
    (typeof process !== "undefined" && process.env.NEXT_PUBLIC_FASTAPI_URL) ||
    "http://localhost:8000";

interface ImageMeta {
    filename: string;
    url: string;
    size_bytes: number;
    captured_at: string;
}

interface GalleryResponse {
    total: number;
    page: number;
    page_size: number;
    images: ImageMeta[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatBytes(bytes: number) {
    return bytes < 1024
        ? `${bytes} B`
        : bytes < 1024 ** 2
        ? `${(bytes / 1024).toFixed(1)} KB`
        : `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString();
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function CameraPage() {
    const [latest, setLatest] = useState<ImageMeta | null>(null);
    const [gallery, setGallery] = useState<ImageMeta[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [liveMode, setLiveMode] = useState(false);
    const [loading, setLoading] = useState(true);
    const [capturing, setCapturing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
    const [cacheBust, setCacheBust] = useState(Date.now());
    const liveTimer = useRef<ReturnType<typeof setInterval> | null>(null);

    const PAGE_SIZE = 12;

    // ── Fetch latest image ────────────────────────────────────────────────────
    const fetchLatest = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/camera/latest`);
            if (res.ok) {
                const data: ImageMeta = await res.json();
                setLatest(data);
                setError(null);
            } else if (res.status === 404) {
                setLatest(null);
            } else {
                setError("Failed to load latest image");
            }
        } catch {
            setError("Cannot reach camera API");
        }
    }, []);

    // ── Fetch gallery ─────────────────────────────────────────────────────────
    const fetchGallery = useCallback(async (p = 1) => {
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/camera/list?page=${p}&page_size=${PAGE_SIZE}`
            );
            if (res.ok) {
                const data: GalleryResponse = await res.json();
                setGallery(data.images);
                setTotal(data.total);
                setPage(p);
            }
        } catch {
            // gallery error is non-critical
        }
    }, []);

    // ── Initial load ──────────────────────────────────────────────────────────
    useEffect(() => {
        Promise.all([fetchLatest(), fetchGallery(1)]).finally(() =>
            setLoading(false)
        );
    }, [fetchLatest, fetchGallery]);

    // ── Live-mode interval ────────────────────────────────────────────────────
    useEffect(() => {
        if (liveMode) {
            // Trigger an immediate capture when entering live mode
            fetch(`${API_BASE}/api/v1/camera/capture`, { method: "POST" }).catch(() => {});
            liveTimer.current = setInterval(() => {
                fetchLatest();
                fetchGallery(1);
                setCacheBust(Date.now());
            }, 3000);
        } else {
            if (liveTimer.current) clearInterval(liveTimer.current);
        }
        return () => {
            if (liveTimer.current) clearInterval(liveTimer.current);
        };
    }, [liveMode, fetchLatest, fetchGallery]);

    // ── Trigger on-demand capture ─────────────────────────────────────────────
    const handleCapture = async () => {
        setCapturing(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/camera/capture`, {
                method: "POST",
            });
            if (res.ok) {
                // Refresh after a short delay (Pi needs ~2 s to capture + upload)
                setTimeout(() => {
                    fetchLatest();
                    fetchGallery(1);
                }, 4000);
            } else {
                setError("Capture trigger failed");
            }
        } catch {
            setError("Cannot reach camera API");
        } finally {
            setCapturing(false);
        }
    };

    // ── Delete an image ───────────────────────────────────────────────────────
    const handleDelete = async (filename: string) => {
        if (!confirm(`Delete ${filename}?`)) return;
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/camera/image/${filename}`,
                { method: "DELETE" }
            );
            if (res.ok) {
                setGallery((g) => g.filter((img) => img.filename !== filename));
                setTotal((t) => t - 1);
                if (latest?.filename === filename) setLatest(null);
            }
        } catch {
            setError("Delete failed");
        }
    };

    // ── Render ────────────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
            {/* Header */}
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="flex items-center gap-2 text-gray-400 hover:text-emerald-400 transition-colors"
                        >
                            <ArrowLeft size={18} />
                            <span className="text-sm">Dashboard</span>
                        </Link>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-emerald-500/10 rounded-lg">
                                <Camera size={22} className="text-emerald-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold">Plant Camera</h1>
                                <p className="text-xs text-gray-400">
                                    Raspberry Pi · {total} image{total !== 1 ? "s" : ""}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-3">
                        {/* Live toggle */}
                        <button
                            onClick={() => setLiveMode((v) => !v)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                liveMode
                                    ? "bg-emerald-500 text-white"
                                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                            }`}
                        >
                            {liveMode ? (
                                <Wifi size={15} />
                            ) : (
                                <WifiOff size={15} />
                            )}
                            {liveMode ? "Live" : "Live off"}
                        </button>

                        {/* Manual refresh */}
                        <button
                            onClick={() => {
                                setLoading(true);
                                Promise.all([
                                    fetchLatest(),
                                    fetchGallery(1),
                                ]).finally(() => setLoading(false));
                            }}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-all"
                        >
                            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
                            Refresh
                        </button>

                        {/* Capture now */}
                        <button
                            onClick={handleCapture}
                            disabled={capturing}
                            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium transition-all"
                        >
                            <Camera size={15} className={capturing ? "animate-pulse" : ""} />
                            {capturing ? "Capturing…" : "Capture Now"}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
                        {error}
                    </div>
                )}

                {/* Latest image ──────────────────────────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
                        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
                            <span className="text-sm font-medium text-gray-200">
                                Latest Capture
                            </span>
                            {liveMode && (
                                <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                    Live (3 s)
                                </span>
                            )}
                        </div>

                        {latest ? (
                            <div className="relative group cursor-pointer" onClick={() => setLightboxSrc(`${API_BASE}${latest.url}?t=${cacheBust}`)}>
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                    src={`${API_BASE}${latest.url}?t=${cacheBust}`}
                                    alt="Latest plant capture"
                                    className="w-full h-72 object-cover"
                                    key={`${latest.filename}-${cacheBust}`}
                                />
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                                    <ZoomIn size={32} className="text-white" />
                                </div>
                            </div>
                        ) : (
                            <div className="h-72 flex flex-col items-center justify-center text-gray-600">
                                <Camera size={40} className="mb-2" />
                                <p>No images yet</p>
                                <p className="text-xs mt-1">
                                    Start the Pi camera service or press &quot;Capture Now&quot;
                                </p>
                            </div>
                        )}

                        {latest && (
                            <div className="px-5 py-3 text-xs text-gray-500 space-y-0.5">
                                <div>
                                    <span className="text-gray-400">File: </span>
                                    {latest.filename}
                                </div>
                                <div>
                                    <span className="text-gray-400">Captured: </span>
                                    {formatDate(latest.captured_at)}
                                </div>
                                <div>
                                    <span className="text-gray-400">Size: </span>
                                    {formatBytes(latest.size_bytes)}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Info / status panel */}
                    <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5 flex flex-col gap-4">
                        <h2 className="text-sm font-medium text-gray-200">Camera Status</h2>
                        
                        <div className="space-y-3">
                            <StatusRow
                                label="Camera service"
                                value={latest ? "Online" : "No data"}
                                ok={!!latest}
                            />
                            <StatusRow
                                label="Live refresh"
                                value={liveMode ? "Active (3 s)" : "Off"}
                                ok={liveMode}
                            />
                            <StatusRow
                                label="Total images"
                                value={`${total}`}
                                ok={total > 0}
                            />
                            {latest && (
                                <StatusRow
                                    label="Last capture"
                                    value={formatDate(latest.captured_at)}
                                    ok
                                />
                            )}
                        </div>

                        <div className="mt-auto pt-4 border-t border-gray-800 text-xs text-gray-500 space-y-1">
                            <p>The Pi camera service captures every 5 minutes automatically.</p>
                            <p>
                                Use <strong className="text-gray-400">Capture Now</strong> for
                                an on-demand photo via MQTT.
                            </p>
                            <p>
                                Toggle <strong className="text-gray-400">Live</strong> to
                                auto-refresh the view every 3 s.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Gallery ─────────────────────────────────────────────────── */}
                <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-medium text-gray-200">Gallery</h2>
                        <span className="text-xs text-gray-500">{total} images</span>
                    </div>

                    {gallery.length === 0 ? (
                        <p className="text-sm text-gray-600 text-center py-10">
                            No images in the gallery yet.
                        </p>
                    ) : (
                        <>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                                {gallery.map((img) => (
                                    <div
                                        key={img.filename}
                                        className="relative group rounded-xl overflow-hidden border border-gray-800 bg-gray-950"
                                    >
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img
                                            src={`${API_BASE}${img.url}`}
                                            alt={img.filename}
                                            className="w-full h-28 object-cover cursor-pointer"
                                            onClick={() =>
                                                setLightboxSrc(`${API_BASE}${img.url}`)
                                            }
                                        />
                                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all" />
                                        <button
                                            onClick={() => handleDelete(img.filename)}
                                            className="absolute top-1.5 right-1.5 p-1 rounded-md bg-black/60 text-red-400 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-300"
                                            title="Delete"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                        <div className="absolute bottom-0 left-0 right-0 px-2 py-1 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <p className="text-xs text-gray-200 truncate">
                                                {formatDate(img.captured_at)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Pagination */}
                            {total > PAGE_SIZE && (
                                <div className="flex items-center justify-center gap-3 mt-5">
                                    <button
                                        onClick={() => fetchGallery(page - 1)}
                                        disabled={page <= 1}
                                        className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-sm transition-all"
                                    >
                                        ← Prev
                                    </button>
                                    <span className="text-sm text-gray-400">
                                        {page} / {Math.ceil(total / PAGE_SIZE)}
                                    </span>
                                    <button
                                        onClick={() => fetchGallery(page + 1)}
                                        disabled={page * PAGE_SIZE >= total}
                                        className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-sm transition-all"
                                    >
                                        Next →
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Lightbox */}
            {lightboxSrc && (
                <div
                    className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
                    onClick={() => setLightboxSrc(null)}
                >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={lightboxSrc}
                        alt="Full size"
                        className="max-w-full max-h-full object-contain rounded-lg"
                    />
                    <button
                        className="absolute top-4 right-4 text-white/70 hover:text-white text-3xl"
                        onClick={() => setLightboxSrc(null)}
                    >
                        ×
                    </button>
                </div>
            )}
        </div>
    );
}

// ── Sub-components ────────────────────────────────────────────────────────────
function StatusRow({
    label,
    value,
    ok,
}: {
    label: string;
    value: string;
    ok: boolean;
}) {
    return (
        <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">{label}</span>
            <span
                className={`font-medium ${ok ? "text-emerald-400" : "text-gray-500"}`}
            >
                {value}
            </span>
        </div>
    );
}
