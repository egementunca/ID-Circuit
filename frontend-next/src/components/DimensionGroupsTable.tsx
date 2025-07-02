"use client";

import React, { useState } from "react";
import { Eye, RefreshCw } from "lucide-react";
import { DimGroupRecord } from "@/types/api";

interface DimensionGroupsTableProps {
    dimGroups: DimGroupRecord[];
    onSelect: (dimGroup: DimGroupRecord) => void;
    onRefresh: () => void;
}

export default function DimensionGroupsTable({
    dimGroups,
    onSelect,
    onRefresh,
}: DimensionGroupsTableProps) {
    const [selectedId, setSelectedId] = useState<number | null>(null);

    const handleRowClick = (dimGroup: DimGroupRecord) => {
        setSelectedId(dimGroup.id);
        onSelect(dimGroup);
    };

    if (dimGroups.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-600 mb-4">
                    No dimension groups found. Generate some seeds!
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
                <h2 className="text-xl font-semibold text-gray-800">
                    Dimension Groups
                </h2>
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
                            <th>ID</th>
                            <th>Width</th>
                            <th>Gate Count</th>
                            <th>Total Circuits</th>
                            <th>Representatives</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {dimGroups.map((dimGroup) => (
                            <tr
                                key={dimGroup.id}
                                className={
                                    selectedId === dimGroup.id ? "selected" : ""
                                }
                                onClick={() => handleRowClick(dimGroup)}
                            >
                                <td>{dimGroup.id}</td>
                                <td>{dimGroup.width}</td>
                                <td>{dimGroup.gate_count}</td>
                                <td>{dimGroup.circuit_count}</td>
                                <td>{dimGroup.representative_count}</td>
                                <td>
                                    <span
                                        className={`status-badge ${
                                            dimGroup.is_processed
                                                ? "success"
                                                : "pending"
                                        }`}
                                    >
                                        {dimGroup.is_processed
                                            ? "✅ Processed"
                                            : "⏳ Pending"}
                                    </span>
                                </td>
                                <td>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onSelect(dimGroup);
                                        }}
                                        className="btn-primary btn-small flex items-center gap-1"
                                    >
                                        <Eye className="w-3 h-3" />
                                        View Gate Compositions
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
