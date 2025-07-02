"use client";

import React from "react";
import Link from "next/link";
import { Activity, Database, Zap, Settings, Play } from "lucide-react";

export default function Header() {
    return (
        <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl border border-white/20">
                        <Activity className="w-8 h-8 text-blue-300" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">
                            Identity Circuit Factory
                        </h1>
                        <p className="text-blue-200/70">
                            Quantum Circuit Analysis & Generation
                        </p>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <nav className="flex items-center gap-2">
                    <Link
                        href="/"
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
                    >
                        <Database className="w-4 h-4" />
                        Database
                    </Link>
                    <Link
                        href="/playground"
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-200 transition-colors"
                    >
                        <Play className="w-4 h-4" />
                        Playground
                    </Link>
                </nav>

                <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors">
                    <Settings className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
