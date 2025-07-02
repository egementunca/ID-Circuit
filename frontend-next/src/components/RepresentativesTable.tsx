"use client";

import React, { useState } from "react";
import { Eye, RefreshCw, Play } from "lucide-react";
import { CircuitRecord, GateComposition } from "@/types/api";

interface RepresentativesTableProps {
    representatives: CircuitRecord[];
    composition: GateComposition | null;
    onSelect: (circuit: CircuitRecord) => void;
    onRefresh: () => void;
    onRefreshStats: () => void;
}

export default function RepresentativesTable({
    representatives,
    composition,
    onSelect,
    onRefresh,
    onRefreshStats,
}: RepresentativesTableProps) {
    const [selectedId, setSelectedId] = useState<number | null>(null);

    const handleRowClick = (circuit: CircuitRecord) => {
        setSelectedId(circuit.id);
        onSelect(circuit);
    };

    if (representatives.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-600 mb-4">
                    No representative circuits found for this composition.
                </div>
                <button
                    onClick={onRefresh}
                    className="btn-primary flex items-center gap-2 mx-auto"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h2 className="text-xl font-semibold text-gray-800">
                        Representative Circuits
                        {composition && (
                            <span className="text-gray-600 text-base ml-2">
                                [{composition.gate_composition.join(", ")}]
                            </span>
                        )}
                    </h2>
                    <div className="text-sm text-gray-600 mt-1">
                        {representatives.length} representatives found
                    </div>
                </div>
                <button
                    onClick={onRefresh}
                    className="btn-secondary btn-small flex items-center gap-2"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            <div className="flex-1 overflow-auto">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Circuit ID</th>
                            <th>Width</th>
                            <th>Gate Count</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {representatives.map((circuit) => (
                            <tr
                                key={circuit.id}
                                className={
                                    selectedId === circuit.id ? "selected" : ""
                                }
                                onClick={() => handleRowClick(circuit)}
                            >
                                <td>Circuit {circuit.id}</td>
                                <td>{circuit.width}</td>
                                <td>
                                    {circuit.gate_count}
                                    <span className="text-gray-500 text-xs ml-1">
                                        ({circuit.gates?.length || 0} gates)
                                    </span>
                                </td>
                                <td>
                                    <span className="status-badge success">
                                        ✅ Representative
                                    </span>
                                </td>
                                <td>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onSelect(circuit);
                                        }}
                                        className="btn-primary btn-small flex items-center gap-1"
                                    >
                                        <Eye className="w-3 h-3" />
                                        View Details
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
