"use client";

import React from "react";
import {
    Activity,
    Zap,
    Target,
    Hash,
    CheckCircle2,
    AlertTriangle,
    Upload,
    TrendingUp,
} from "lucide-react";
import { PlaygroundCircuit, LiveMetrics } from "@/types/api";

interface MetricsPanelProps {
    circuit: PlaygroundCircuit;
    metrics: LiveMetrics;
}

interface MetricCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
    trend?: "up" | "down" | "stable";
}

function MetricCard({
    title,
    value,
    icon,
    color,
    subtitle,
    trend,
}: MetricCardProps) {
    return (
        <div
            className={`p-4 rounded-xl border bg-slate-800/40 ${color} backdrop-blur-sm`}
        >
            <div className="flex items-center gap-3 mb-3">
                <div
                    className={`p-2.5 rounded-lg ${color} ring-1 ring-white/10`}
                >
                    {icon}
                </div>
                <div className="flex-1">
                    <h4 className="font-semibold text-white text-sm">
                        {title}
                    </h4>
                    {subtitle && (
                        <p className="text-xs text-slate-400">{subtitle}</p>
                    )}
                </div>
                {trend && (
                    <div
                        className={`text-xs ${
                            trend === "up"
                                ? "text-green-400"
                                : trend === "down"
                                ? "text-red-400"
                                : "text-slate-400"
                        }`}
                    >
                        <TrendingUp className="w-3 h-3" />
                    </div>
                )}
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
        </div>
    );
}

function GateCompositionChart({
    composition,
}: {
    composition: [number, number, number];
}) {
    const [notCount, cnotCount, ccnotCount] = composition;
    const total = notCount + cnotCount + ccnotCount;

    if (total === 0) {
        return (
            <div className="text-center text-slate-400 py-8 bg-slate-800/30 rounded-lg border border-slate-600/30">
                <Zap className="w-8 h-8 mx-auto mb-2 text-slate-500" />
                <div className="text-sm">No gates in circuit</div>
            </div>
        );
    }

    const notPercent = (notCount / total) * 100;
    const cnotPercent = (cnotCount / total) * 100;
    const ccnotPercent = (ccnotCount / total) * 100;

    const gates = [
        {
            name: "X (NOT)",
            count: notCount,
            percent: notPercent,
            color: "bg-red-500",
            textColor: "text-red-300",
        },
        {
            name: "CX (CNOT)",
            count: cnotCount,
            percent: cnotPercent,
            color: "bg-blue-500",
            textColor: "text-blue-300",
        },
        {
            name: "CCX (Toffoli)",
            count: ccnotCount,
            percent: ccnotPercent,
            color: "bg-purple-500",
            textColor: "text-purple-300",
        },
    ];

    return (
        <div className="space-y-4">
            {gates.map((gate, index) => (
                <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                        <span
                            className={`text-sm font-medium ${gate.textColor}`}
                        >
                            {gate.name}
                        </span>
                        <div className="flex items-center gap-2">
                            <span
                                className={`text-sm font-bold ${gate.textColor}`}
                            >
                                {gate.count}
                            </span>
                            <span className="text-xs text-slate-500">
                                ({gate.percent.toFixed(1)}%)
                            </span>
                        </div>
                    </div>
                    <div className="w-full bg-slate-700/50 rounded-full h-3 overflow-hidden">
                        <div
                            className={`${gate.color} h-3 rounded-full transition-all duration-500 shadow-sm`}
                            style={{ width: `${gate.percent}%` }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

function PermutationTable({ permutation }: { permutation?: number[] }) {
    if (!permutation || permutation.length === 0) {
        return (
            <div className="text-center text-slate-400 py-8 bg-slate-800/30 rounded-lg border border-slate-600/30">
                <Activity className="w-8 h-8 mx-auto mb-2 text-slate-500" />
                <div className="text-sm">No permutation data</div>
            </div>
        );
    }

    const isIdentity = permutation.every((val, idx) => val === idx);
    const width = Math.log2(permutation.length);

    return (
        <div className="space-y-4">
            <div
                className={`flex items-center gap-3 p-3 rounded-lg ${
                    isIdentity
                        ? "bg-green-500/10 border border-green-500/30"
                        : "bg-orange-500/10 border border-orange-500/30"
                }`}
            >
                {isIdentity ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                ) : (
                    <AlertTriangle className="w-5 h-5 text-orange-400" />
                )}
                <div>
                    <div
                        className={`font-semibold ${
                            isIdentity ? "text-green-300" : "text-orange-300"
                        }`}
                    >
                        {isIdentity
                            ? "Identity Circuit ✨"
                            : "Non-Identity Circuit"}
                    </div>
                    <div className="text-xs text-slate-400">
                        {isIdentity
                            ? "Implements the identity operation"
                            : "Performs a non-trivial permutation"}
                    </div>
                </div>
            </div>

            <div className="max-h-48 overflow-y-auto bg-slate-800/30 rounded-lg border border-slate-600/30">
                <div className="grid grid-cols-2 gap-1 p-3 text-xs font-mono">
                    <div className="font-bold text-slate-300 pb-2 border-b border-slate-600/30">
                        Input
                    </div>
                    <div className="font-bold text-slate-300 pb-2 border-b border-slate-600/30">
                        Output
                    </div>

                    {permutation
                        .slice(0, Math.min(16, permutation.length))
                        .map((output, input) => (
                            <React.Fragment key={input}>
                                <div className="text-slate-400 py-1">
                                    |{input.toString(2).padStart(width, "0")}⟩
                                </div>
                                <div
                                    className={`py-1 font-semibold ${
                                        input === output
                                            ? "text-green-400"
                                            : "text-orange-400"
                                    }`}
                                >
                                    |{output.toString(2).padStart(width, "0")}⟩
                                </div>
                            </React.Fragment>
                        ))}

                    {permutation.length > 16 && (
                        <div className="col-span-2 text-center text-slate-500 pt-3 border-t border-slate-600/30">
                            ... and {permutation.length - 16} more states
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function MetricsPanel({ circuit, metrics }: MetricsPanelProps) {
    return (
        <div className="space-y-6">
            {/* Total Gates */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-600/40">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="text-blue-400">#</span>
                        Total Gates
                    </h3>
                </div>
                <div className="text-3xl font-bold text-white">
                    {metrics.gateCount}
                </div>
                <div className="text-sm text-slate-400">Active gates</div>
            </div>

            {/* Circuit Depth */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-600/40">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="text-green-400">⚡</span>
                        Circuit Depth
                    </h3>
                </div>
                <div className="text-3xl font-bold text-white">
                    {metrics.depth}
                </div>
                <div className="text-sm text-slate-400">Sequential layers</div>
            </div>

            {/* Identity Status */}
            <div
                className={`rounded-xl p-4 border ${
                    metrics.isIdentity
                        ? "bg-green-500/20 border-green-500/40"
                        : "bg-yellow-500/20 border-yellow-500/40"
                }`}
            >
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        {metrics.isIdentity ? "✨" : "⚠️"}
                        {metrics.isIdentity
                            ? "Identity Circuit"
                            : "Non-Identity Circuit"}
                    </h3>
                </div>
                <div className="text-sm text-slate-300">
                    {metrics.isIdentity
                        ? "This circuit performs the identity operation"
                        : "This circuit performs a non-trivial permutation"}
                </div>
                {!metrics.isIdentity && (
                    <div className="mt-2">
                        <div className="text-xs text-slate-400">
                            Hamming Distance:
                        </div>
                        <div className="text-2xl font-bold text-yellow-300">
                            {metrics.hamming_distance}
                        </div>
                    </div>
                )}
            </div>

            {/* Gate Composition */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-600/40">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <span className="text-purple-400">⚡</span>
                    Gate Composition
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-red-300">X (NOT)</span>
                        <div className="flex items-center gap-2">
                            <span className="text-white font-bold">
                                {metrics.gateComposition[0]}
                            </span>
                            <span className="text-xs text-slate-400">
                                (
                                {metrics.gateCount > 0
                                    ? Math.round(
                                          (metrics.gateComposition[0] /
                                              metrics.gateCount) *
                                              100
                                      )
                                    : 0}
                                %)
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-blue-300">CX (CNOT)</span>
                        <div className="flex items-center gap-2">
                            <span className="text-white font-bold">
                                {metrics.gateComposition[1]}
                            </span>
                            <span className="text-xs text-slate-400">
                                (
                                {metrics.gateCount > 0
                                    ? Math.round(
                                          (metrics.gateComposition[1] /
                                              metrics.gateCount) *
                                              100
                                      )
                                    : 0}
                                %)
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-purple-300">CCX (Toffoli)</span>
                        <div className="flex items-center gap-2">
                            <span className="text-white font-bold">
                                {metrics.gateComposition[2]}
                            </span>
                            <span className="text-xs text-slate-400">
                                (
                                {metrics.gateCount > 0
                                    ? Math.round(
                                          (metrics.gateComposition[2] /
                                              metrics.gateCount) *
                                              100
                                      )
                                    : 0}
                                %)
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* State Mapping */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-600/40">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <span className="text-cyan-400">⚡</span>
                    State Mapping
                </h3>
                <div className="text-sm text-slate-400 mb-3">
                    {metrics.isIdentity
                        ? "Identity Circuit"
                        : "Non-Identity Circuit"}
                </div>

                {/* Headers */}
                <div className="grid grid-cols-2 gap-4 text-xs font-mono mb-2">
                    <div className="text-slate-400 font-bold">Input</div>
                    <div className="text-slate-400 font-bold">Output</div>
                </div>

                {/* Single scrollable container for both columns */}
                <div className="max-h-32 overflow-y-auto">
                    <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                        <div className="space-y-1">
                            {Array.from(
                                {
                                    length: Math.min(
                                        8,
                                        Math.pow(2, circuit.width)
                                    ),
                                },
                                (_, i) => (
                                    <div key={i} className="text-blue-300">
                                        |
                                        {i
                                            .toString(2)
                                            .padStart(circuit.width, "0")}
                                        ⟩
                                    </div>
                                )
                            )}
                            {Math.pow(2, circuit.width) > 8 && (
                                <div className="text-slate-500">...</div>
                            )}
                        </div>
                        <div className="space-y-1">
                            {metrics.permutation &&
                                metrics.permutation
                                    .slice(0, 8)
                                    .map((val, i) => (
                                        <div
                                            key={i}
                                            className={
                                                val === i
                                                    ? "text-green-300"
                                                    : "text-orange-300"
                                            }
                                        >
                                            |
                                            {val
                                                .toString(2)
                                                .padStart(circuit.width, "0")}
                                            ⟩
                                        </div>
                                    ))}
                            {metrics.permutation &&
                                metrics.permutation.length > 8 && (
                                    <div className="text-slate-500">...</div>
                                )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
