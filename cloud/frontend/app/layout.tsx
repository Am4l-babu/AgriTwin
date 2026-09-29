import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";
import { clsx } from "clsx";
import { SensorProvider } from "./context/SensorContext";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const robotoMono = Roboto_Mono({ subsets: ["latin"], variable: "--font-roboto-mono" });

export const metadata: Metadata = {
    title: "Smart Farming - Digital Twin Dashboard",
    description: "Real-time sensor monitoring and digital twin simulation.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={clsx(inter.variable, robotoMono.variable, "antialiased bg-black")}>
                <SensorProvider>
                    <div className="pb-24">{children}</div>
                    <Navbar />
                </SensorProvider>
            </body>
        </html>
    );
}
