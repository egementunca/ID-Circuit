"use client";

import React, { useState, useEffect } from "react";
import { Activity, Database, Zap, Settings } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import MainContent from "@/components/MainContent";
import Header from "@/components/Header";
import { getStats } from "@/lib/api";
import { FactoryStats } from "@/types/api";

export default function Home() {
    const [stats, setStats] = useState<FactoryStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const data = await getStats();
            setStats(data);
            setError(null);
        } catch (err) {
            console.error("Failed to load stats:", err);
            setError("Failed to load factory statistics");
        } finally {
            setLoading(false);
        }
    };

    const refreshStats = () => {
        loadStats();
    };

    return (
        <div className="min-h-screen bg-circuit-gradient">
            <div className="p-5 w-full max-w-none">
                {/* Header */}
                <Header />

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-5 h-[calc(100vh-200px)] w-full">
                    {/* Sidebar */}
                    <Sidebar
                        stats={stats}
                        loading={loading}
                        error={error}
                        onRefreshStats={refreshStats}
                    />

                    {/* Main Content Area */}
                    <MainContent onRefreshStats={refreshStats} />
                </div>
            </div>
        </div>
    );
}
