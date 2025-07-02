"use client";

import React, { useState, useEffect, useRef } from "react";
import { ArrowLeft, Activity } from "lucide-react";
import { CircuitRecord, CircuitVisualization } from "@/types/api";
import { getCircuitVisualization } from "@/lib/api";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface CircuitDetailsProps {
    circuit: CircuitRecord | null;
    onBack: () => void;
}

export default function CircuitDetails({
    circuit,
    onBack,
}: CircuitDetailsProps) {
    const [visualization, setVisualization] =
        useState<CircuitVisualization | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (circuit) {
            loadVisualization();
        }
    }, [circuit]);

    const loadVisualization = async () => {
        if (!circuit) return;

        try {
            setLoading(true);
            setError(null);
            const data = await getCircuitVisualization(circuit.id);
            setVisualization(data);
        } catch (err) {
            console.error("Failed to load circuit visualization:", err);
            setError("Failed to load circuit visualization");
        } finally {
            setLoading(false);
        }
    };

    if (!circuit) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-600">No circuit selected</div>
            </div>
        );
    }

    const generateHammingChartData = () => {
        if (!circuit.complexity_walk || circuit.complexity_walk.length === 0) {
            console.log(
                "No complexity walk data available for circuit:",
                circuit.id
            );
            return null;
        }

        // Add initial point at 0 for the identity state
        const walkData = [0, ...circuit.complexity_walk];
        const gateLabels = walkData.map((_, index) =>
            index === 0 ? "Identity" : `Gate ${index}`
        );

        console.log("Generating chart with data:", walkData);

        return {
            labels: gateLabels,
            datasets: [
                {
                    label: "Hamming Distance from Identity",
                    data: walkData,
                    borderColor: "rgb(102, 126, 234)",
                    backgroundColor: "rgba(102, 126, 234, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointBackgroundColor: "rgb(102, 126, 234)",
                    pointBorderColor: "rgb(74, 85, 104)",
                    pointBorderWidth: 1,
                    pointRadius: 4,
                },
            ],
        };
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: "Hamming Distance",
                },
                grid: {
                    color: "#e2e8f0",
                },
            },
            x: {
                title: {
                    display: true,
                    text: "Gate Step",
                },
                grid: {
                    color: "#e2e8f0",
                },
            },
        },
        plugins: {
            title: {
                display: true,
                text: "Circuit Complexity Evolution",
                font: {
                    size: 14,
                    weight: "bold" as const,
                },
            },
            legend: {
                display: false,
            },
        },
        interaction: {
            intersect: false,
            mode: "index" as const,
        },
    };

    const generateGateDescriptions = () => {
        if (!circuit.gates) return [];

        return circuit.gates.map((gate, index) => {
            if (gate[0] === "X") {
                return `Gate ${index + 1}: X (NOT) on qubit ${gate[1]}`;
            } else if (gate[0] === "CX") {
                return `Gate ${index + 1}: CX (CNOT) from qubit ${
                    gate[1]
                } to qubit ${gate[2]}`;
            } else if (gate[0] === "CCX") {
                return `Gate ${index + 1}: CCX (Toffoli) with controls ${
                    gate[1]
                }, ${gate[2]} and target ${gate[3]}`;
            } else {
                return `Gate ${index + 1}: ${gate}`;
            }
        });
    };

    const generateTruthTable = () => {
        if (!circuit.permutation) return [];

        const width = circuit.width;
        const table = [];

        for (let i = 0; i < Math.pow(2, width); i++) {
            const inputBinary = i
                .toString(2)
                .padStart(width, "0")
                .split("")
                .map(Number);
            const outputIndex = circuit.permutation[i];
            const outputBinary = outputIndex
                .toString(2)
                .padStart(width, "0")
                .split("")
                .map(Number);
            table.push([i, ...inputBinary, outputIndex, ...outputBinary]);
        }

        return table;
    };

    const chartData = generateHammingChartData();
    const gateDescriptions = generateGateDescriptions();
    const truthTable = generateTruthTable();

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={onBack}
                    className="btn-secondary btn-small flex items-center gap-2"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>
                <div>
                    <h2 className="text-xl font-semibold text-gray-800">
                        Circuit {circuit.id} Details
                    </h2>
                    <div className="text-sm text-gray-600">
                        {circuit.width} qubits, {circuit.gate_count} gates
                    </div>
                </div>
            </div>

            {loading && (
                <div className="flex items-center justify-center h-32">
                    <div className="text-gray-600">
                        Loading circuit details...
                    </div>
                </div>
            )}

            {error && (
                <div className="flex items-center justify-center h-32">
                    <div className="text-red-600">{error}</div>
                </div>
            )}

            {!loading && !error && (
                <div className="flex-1 overflow-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Circuit Diagram */}
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                🔗 Circuit Diagram
                            </h4>
                            <div className="circuit-diagram">
                                {visualization?.ascii_diagram ||
                                    "Loading diagram..."}
                            </div>
                        </div>

                        {/* Hamming Distance Chart */}
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                <Activity className="w-5 h-5" />
                                Hamming Distance Plot
                            </h4>
                            <div className="h-64">
                                {chartData ? (
                                    <Line
                                        data={chartData}
                                        options={chartOptions}
                                    />
                                ) : (
                                    <div className="flex items-center justify-center h-full text-gray-600">
                                        No complexity walk data available
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Gate Sequence */}
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h4 className="text-lg font-semibold text-gray-800 mb-3">
                                🚪 Gate Sequence
                            </h4>
                            <div className="max-h-48 overflow-y-auto space-y-1">
                                {gateDescriptions.map((desc, index) => (
                                    <div
                                        key={index}
                                        className="text-sm text-gray-700 py-1 border-b border-gray-200 last:border-b-0"
                                    >
                                        {desc}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Truth Table */}
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <h4 className="text-lg font-semibold text-gray-800 mb-3">
                                📋 Truth Table
                            </h4>
                            <div className="max-h-48 overflow-auto">
                                <table className="w-full text-xs border-collapse">
                                    <thead>
                                        <tr>
                                            <th className="p-1 bg-blue-100 border">
                                                In#
                                            </th>
                                            {Array.from(
                                                { length: circuit.width },
                                                (_, i) => (
                                                    <th
                                                        key={i}
                                                        className="p-1 bg-blue-100 border"
                                                    >
                                                        In{i}
                                                    </th>
                                                )
                                            )}
                                            <th className="p-1 bg-gray-400 border text-white">
                                                →
                                            </th>
                                            <th className="p-1 bg-green-100 border">
                                                Out#
                                            </th>
                                            {Array.from(
                                                { length: circuit.width },
                                                (_, i) => (
                                                    <th
                                                        key={i}
                                                        className="p-1 bg-green-100 border"
                                                    >
                                                        Out{i}
                                                    </th>
                                                )
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {truthTable.map((row, index) => (
                                            <tr
                                                key={index}
                                                className={
                                                    index % 2 === 0
                                                        ? "bg-white"
                                                        : "bg-gray-50"
                                                }
                                            >
                                                {row.map((cell, cellIndex) => (
                                                    <td
                                                        key={cellIndex}
                                                        className="p-1 border text-center"
                                                    >
                                                        {cellIndex ===
                                                        circuit.width + 1
                                                            ? "→"
                                                            : cell}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Circuit Info */}
                    <div className="mt-6 bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-lg font-semibold text-gray-800 mb-3">
                            Circuit Information
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <span className="font-medium text-gray-600">
                                    Circuit ID:
                                </span>
                                <div className="text-gray-800">
                                    {circuit.id}
                                </div>
                            </div>
                            <div>
                                <span className="font-medium text-gray-600">
                                    Width:
                                </span>
                                <div className="text-gray-800">
                                    {circuit.width} qubits
                                </div>
                            </div>
                            <div>
                                <span className="font-medium text-gray-600">
                                    Gate Count:
                                </span>
                                <div className="text-gray-800">
                                    {circuit.gate_count}
                                </div>
                            </div>
                            <div>
                                <span className="font-medium text-gray-600">
                                    Status:
                                </span>
                                <div className="text-gray-800">
                                    <span className="status-badge success">
                                        Representative
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
