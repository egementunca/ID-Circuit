"use client";

import React, { useState } from "react";
import { Eye, RefreshCw } from "lucide-react";
import { GateComposition, DimGroupRecord } from "@/types/api";

interface GateCompositionsTableProps {
    compositions: GateComposition[];
    dimGroup: DimGroupRecord | null;
    onSelect: (composition: GateComposition) => void;
    onRefresh: () => void;
}

export default function GateCompositionsTable({
    compositions,
    dimGroup,
    onSelect,
    onRefresh,
}: GateCompositionsTableProps) {
    const [selectedComposition, setSelectedComposition] = useState<
        string | null
    >(null);

    const handleRowClick = (composition: GateComposition) => {
        setSelectedComposition(composition.gate_composition.join(","));
        onSelect(composition);
    };

    if (compositions.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-600 mb-4">
                    No gate compositions found for this dimension group.
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

    // Calculate totals
    const totalCompositions = compositions.length;
    const totalCircuits = compositions.reduce(
        (sum, comp) => sum + comp.total_count,
        0
    );

    return (
        <div className="h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h2 className="text-xl font-semibold text-gray-800">
                        Gate Compositions
                        {dimGroup && (
                            <span className="text-gray-600 text-base ml-2">
                                ({dimGroup.width} qubits, {dimGroup.gate_count}{" "}
                                gates)
                            </span>
                        )}
                    </h2>
                    <div className="text-sm text-gray-600 mt-1">
                        {totalCompositions} compositions, {totalCircuits} total
                        circuits
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
                            <th>Gate Composition</th>
                            <th>Circuit Count</th>
                            <th>Actions</th>
                        </tr>
                        <tr className="bg-gray-100 font-semibold">
                            <td>
                                <strong>Totals:</strong>
                            </td>
                            <td>
                                <strong>{totalCircuits}</strong>
                            </td>
                            <td>
                                <em>{totalCompositions} compositions</em>
                            </td>
                        </tr>
                    </thead>
                    <tbody>
                        {compositions.map((composition, index) => {
                            const [notCount, cnotCount, ccnotCount] =
                                composition.gate_composition;
                            const compositionKey =
                                composition.gate_composition.join(",");

                            return (
                                <tr
                                    key={index}
                                    className={
                                        selectedComposition === compositionKey
                                            ? "selected"
                                            : ""
                                    }
                                    onClick={() => handleRowClick(composition)}
                                >
                                    <td>
                                        <div className="flex gap-2">
                                            <span className="gate-composition-badge">
                                                NOT: {notCount}
                                            </span>
                                            <span className="gate-composition-badge">
                                                CNOT: {cnotCount}
                                            </span>
                                            <span className="gate-composition-badge">
                                                CCNOT: {ccnotCount}
                                            </span>
                                        </div>
                                    </td>
                                    <td>{composition.total_count} circuits</td>
                                    <td>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onSelect(composition);
                                            }}
                                            className="btn-primary btn-small flex items-center gap-1"
                                        >
                                            <Eye className="w-3 h-3" />
                                            View Representatives
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
