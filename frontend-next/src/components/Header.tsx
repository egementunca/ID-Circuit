"use client";

import React from "react";
import { Zap } from "lucide-react";

export default function Header() {
    return (
        <div className="glass-panel p-6 mb-5 text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
                <Zap className="w-8 h-8 text-blue-600" />
                <h1 className="text-4xl font-bold text-gray-800">
                    Identity Circuit Factory
                </h1>
            </div>
            <p className="text-lg text-gray-600">
                Seed Generator & Database Explorer
            </p>
        </div>
    );
}
