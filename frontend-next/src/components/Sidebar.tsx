"use client";

import React, { useState } from "react";
import { Play, Settings, BarChart3, RefreshCw, Bug } from "lucide-react";
import { FactoryStats, GenerationRequest } from "@/types/api";
import {
    generateCircuit,
    generateWithDebug,
    enableDebugLogging,
    disableDebugLogging,
} from "@/lib/api";

interface SidebarProps {
    stats: FactoryStats | null;
    loading: boolean;
    error: string | null;
    onRefreshStats: () => void;
}

export default function Sidebar({
    stats,
    loading,
    error,
    onRefreshStats,
}: SidebarProps) {
    const [generating, setGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState<string>("");
    const [debugStatus, setDebugStatus] = useState<string>("");
    const [formData, setFormData] = useState({
        width: 3,
        forward_length: 5,
        max_inverse_gates: 40,
        max_attempts: 10,
    });

    const handleGenerate = async () => {
        try {
            setGenerating(true);
            setGenerationStatus("Generating seed...");

            const result = await generateCircuit(formData);

            if (result.success) {
                setGenerationStatus(
                    `✅ Seed generated successfully!\nCircuit ID: ${
                        result.circuit_id
                    }\nDim Group: ${
                        result.dim_group_id
                    }\nTime: ${result.total_time.toFixed(2)}s`
                );
                onRefreshStats();
            } else {
                setGenerationStatus(
                    `❌ Generation failed: ${
                        result.error_message || "Unknown error"
                    }`
                );
            }
        } catch (error) {
            console.error("Generation error:", error);
            setGenerationStatus(`❌ Error: ${error}`);
        } finally {
            setGenerating(false);
        }
    };

    const handleDebugGenerate = async () => {
        try {
            setGenerating(true);
            setGenerationStatus("🔍 Generating seed with debug logging...");

            const result = await generateWithDebug(formData);

            if (result.success) {
                setGenerationStatus(
                    `✅ Debug generation successful!\nCircuit ID: ${result.circuit_id}\nDimension Group: ${result.dim_group_id}\nCheck server logs for detailed debug information.`
                );
                onRefreshStats();
            } else {
                setGenerationStatus(
                    `❌ Debug generation failed: ${
                        result.error_message || "Unknown error"
                    }`
                );
            }
        } catch (error) {
            console.error("Debug generation error:", error);
            setGenerationStatus(`❌ Debug generation failed: ${error}`);
        } finally {
            setGenerating(false);
        }
    };

    const handleDebugLogging = async (enable: boolean) => {
        try {
            setDebugStatus(
                enable
                    ? "Enabling debug logging..."
                    : "Disabling debug logging..."
            );

            const result = enable
                ? await enableDebugLogging()
                : await disableDebugLogging();
            setDebugStatus(`${enable ? "🔍" : "📝"} ${result.message}`);
        } catch (error) {
            console.error("Debug logging error:", error);
            setDebugStatus(
                `❌ Failed to ${
                    enable ? "enable" : "disable"
                } debug logging: ${error}`
            );
        }
    };

    const handleInputChange = (field: string, value: string | number) => {
        setFormData((prev) => ({
            ...prev,
            [field]: typeof value === "string" ? parseInt(value) || 0 : value,
        }));
    };

    return (
        <div className="glass-panel p-5 overflow-y-auto space-y-6">
            {/* Seed Generation Section */}
            <div className="form-section bg-gray-50 p-5 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <Play className="w-5 h-5" />
                    Generate New Seed
                </h3>

                <div className="space-y-4">
                    <div className="form-group">
                        <label
                            htmlFor="width"
                            className="block text-sm font-medium text-gray-700 mb-1"
                        >
                            Width (Qubits)
                        </label>
                        <input
                            type="number"
                            id="width"
                            min="1"
                            max="10"
                            value={formData.width}
                            onChange={(e) =>
                                handleInputChange("width", e.target.value)
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="form-group">
                        <label
                            htmlFor="forward_length"
                            className="block text-sm font-medium text-gray-700 mb-1"
                        >
                            Length (Gates)
                        </label>
                        <input
                            type="number"
                            id="forward_length"
                            min="1"
                            max="50"
                            value={formData.forward_length}
                            onChange={(e) =>
                                handleInputChange(
                                    "forward_length",
                                    e.target.value
                                )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="form-group">
                        <label
                            htmlFor="max_inverse"
                            className="block text-sm font-medium text-gray-700 mb-1"
                        >
                            Max Inverse Gates
                        </label>
                        <input
                            type="number"
                            id="max_inverse"
                            min="1"
                            max="100"
                            value={formData.max_inverse_gates}
                            onChange={(e) =>
                                handleInputChange(
                                    "max_inverse_gates",
                                    e.target.value
                                )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="space-y-2">
                        <button
                            onClick={handleGenerate}
                            disabled={generating}
                            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {generating ? "Generating..." : "Generate Seed"}
                        </button>

                        <button
                            onClick={handleDebugGenerate}
                            disabled={generating}
                            className="btn-secondary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            🔍 Debug Generate
                        </button>
                    </div>

                    {generationStatus && (
                        <div
                            className={`p-3 rounded-md text-sm whitespace-pre-line ${
                                generationStatus.includes("✅")
                                    ? "bg-green-100 text-green-800"
                                    : "bg-red-100 text-red-800"
                            }`}
                        >
                            {generationStatus}
                        </div>
                    )}
                </div>
            </div>

            {/* Debug Tools Section */}
            <div className="form-section bg-gray-50 p-5 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <Bug className="w-5 h-5" />
                    Debug Tools
                </h3>

                <div className="space-y-2">
                    <button
                        onClick={() => handleDebugLogging(true)}
                        className="btn-primary btn-small w-full"
                    >
                        Enable Debug Logs
                    </button>
                    <button
                        onClick={() => handleDebugLogging(false)}
                        className="btn-secondary btn-small w-full"
                    >
                        Disable Debug Logs
                    </button>
                </div>

                {debugStatus && (
                    <div
                        className={`mt-3 p-3 rounded-md text-sm ${
                            debugStatus.includes("✅") ||
                            debugStatus.includes("🔍") ||
                            debugStatus.includes("📝")
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                        }`}
                    >
                        {debugStatus}
                    </div>
                )}

                <div className="mt-3 text-xs text-gray-600">
                    Debug logging shows detailed information about circuit
                    generation in server logs. Use this to diagnose dimension
                    group and diversity issues.
                </div>
            </div>

            {/* Factory Stats Section */}
            <div className="form-section bg-gray-50 p-5 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Factory Stats
                </h3>

                {loading ? (
                    <div className="text-center text-gray-600 py-4">
                        Loading...
                    </div>
                ) : error ? (
                    <div className="text-center text-red-600 py-4">{error}</div>
                ) : stats ? (
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white p-3 rounded-md text-center">
                            <div className="text-2xl font-bold text-blue-600">
                                {stats.total_dim_groups}
                            </div>
                            <div className="text-xs text-gray-600 uppercase tracking-wider">
                                Dim Groups
                            </div>
                        </div>
                        <div className="bg-white p-3 rounded-md text-center">
                            <div className="text-2xl font-bold text-purple-600">
                                {stats.total_circuits}
                            </div>
                            <div className="text-xs text-gray-600 uppercase tracking-wider">
                                Circuits
                            </div>
                        </div>
                        <div className="bg-white p-3 rounded-md text-center">
                            <div className="text-2xl font-bold text-green-600">
                                {stats.total_representatives}
                            </div>
                            <div className="text-xs text-gray-600 uppercase tracking-wider">
                                Representatives
                            </div>
                        </div>
                        <div className="bg-white p-3 rounded-md text-center">
                            <div className="text-2xl font-bold text-orange-600">
                                {stats.total_equivalents}
                            </div>
                            <div className="text-xs text-gray-600 uppercase tracking-wider">
                                Equivalents
                            </div>
                        </div>
                    </div>
                ) : null}
            </div>

            {/* Quick Actions Section */}
            <div className="form-section bg-gray-50 p-5 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    Quick Actions
                </h3>

                <div className="space-y-2">
                    <button
                        onClick={onRefreshStats}
                        className="btn-secondary w-full flex items-center justify-center gap-2"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh All
                    </button>
                </div>
            </div>
        </div>
    );
}
