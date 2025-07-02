"use client";

import React, { useState, useEffect } from "react";
import { ChevronRight, Database, Layers, Grid, Eye } from "lucide-react";
import { DimGroupRecord, GateComposition, CircuitRecord } from "@/types/api";
import {
    getDimensionGroups,
    getDimensionGroupCompositions,
    getDimensionGroupCircuits,
} from "@/lib/api";
import DimensionGroupsTable from "./DimensionGroupsTable";
import GateCompositionsTable from "./GateCompositionsTable";
import RepresentativesTable from "./RepresentativesTable";
import CircuitDetails from "./CircuitDetails";

interface MainContentProps {
    onRefreshStats: () => void;
}

type ViewType =
    | "dimension_groups"
    | "gate_compositions"
    | "representatives"
    | "circuit_details";

export default function MainContent({ onRefreshStats }: MainContentProps) {
    const [currentView, setCurrentView] =
        useState<ViewType>("dimension_groups");
    const [selectedDimGroup, setSelectedDimGroup] =
        useState<DimGroupRecord | null>(null);
    const [selectedComposition, setSelectedComposition] =
        useState<GateComposition | null>(null);
    const [selectedCircuit, setSelectedCircuit] =
        useState<CircuitRecord | null>(null);

    const [dimGroups, setDimGroups] = useState<DimGroupRecord[]>([]);
    const [gateCompositions, setGateCompositions] = useState<GateComposition[]>(
        []
    );
    const [representatives, setRepresentatives] = useState<CircuitRecord[]>([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load dimension groups on mount
    useEffect(() => {
        loadDimensionGroups();
    }, []);

    const loadDimensionGroups = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getDimensionGroups();
            setDimGroups(data);
        } catch (err) {
            console.error("Failed to load dimension groups:", err);
            setError("Failed to load dimension groups");
        } finally {
            setLoading(false);
        }
    };

    const loadGateCompositions = async (dimGroupId: number) => {
        try {
            setLoading(true);
            setError(null);
            const data = await getDimensionGroupCompositions(dimGroupId);
            setGateCompositions(data);
        } catch (err) {
            console.error("Failed to load gate compositions:", err);
            setError("Failed to load gate compositions");
        } finally {
            setLoading(false);
        }
    };

    const loadRepresentatives = async (
        dimGroupId: number,
        composition?: GateComposition
    ) => {
        try {
            setLoading(true);
            setError(null);

            if (composition) {
                // Filter circuits by specific composition
                setRepresentatives(composition.circuits);
            } else {
                // Load all representatives in dimension group
                const data = await getDimensionGroupCircuits(dimGroupId, true);
                setRepresentatives(data);
            }
        } catch (err) {
            console.error("Failed to load representatives:", err);
            setError("Failed to load representatives");
        } finally {
            setLoading(false);
        }
    };

    // Navigation handlers
    const handleDimGroupSelect = async (dimGroup: DimGroupRecord) => {
        setSelectedDimGroup(dimGroup);
        setCurrentView("gate_compositions");
        await loadGateCompositions(dimGroup.id);
    };

    const handleCompositionSelect = async (composition: GateComposition) => {
        setSelectedComposition(composition);
        setCurrentView("representatives");
        await loadRepresentatives(selectedDimGroup?.id || 0, composition);
    };

    const handleCircuitSelect = (circuit: CircuitRecord) => {
        setSelectedCircuit(circuit);
        setCurrentView("circuit_details");
    };

    const handleBackToDimGroups = () => {
        setCurrentView("dimension_groups");
        setSelectedDimGroup(null);
        setSelectedComposition(null);
        setSelectedCircuit(null);
        loadDimensionGroups();
    };

    const handleBackToCompositions = () => {
        setCurrentView("gate_compositions");
        setSelectedComposition(null);
        setSelectedCircuit(null);
        if (selectedDimGroup) {
            loadGateCompositions(selectedDimGroup.id);
        }
    };

    const handleBackToRepresentatives = () => {
        setCurrentView("representatives");
        setSelectedCircuit(null);
        if (selectedDimGroup && selectedComposition) {
            loadRepresentatives(selectedDimGroup.id, selectedComposition);
        }
    };

    const renderBreadcrumb = () => {
        const breadcrumbClass = "breadcrumb";

        return (
            <div className={breadcrumbClass}>
                <button
                    onClick={handleBackToDimGroups}
                    className="text-blue-600 hover:text-blue-800 transition-colors duration-150"
                >
                    Dimension Groups
                </button>

                {selectedDimGroup && (
                    <>
                        <ChevronRight className="inline w-4 h-4 mx-1" />
                        {currentView === "gate_compositions" ? (
                            <span>
                                Gate Compositions ({selectedDimGroup.width},{" "}
                                {selectedDimGroup.gate_count})
                            </span>
                        ) : (
                            <button
                                onClick={handleBackToCompositions}
                                className="text-blue-600 hover:text-blue-800 transition-colors duration-150"
                            >
                                Gate Compositions ({selectedDimGroup.width},{" "}
                                {selectedDimGroup.gate_count})
                            </button>
                        )}
                    </>
                )}

                {selectedComposition && (
                    <>
                        <ChevronRight className="inline w-4 h-4 mx-1" />
                        {currentView === "representatives" ? (
                            <span>
                                Representatives [
                                {selectedComposition.gate_composition.join(
                                    ", "
                                )}
                                ]
                            </span>
                        ) : (
                            <button
                                onClick={handleBackToRepresentatives}
                                className="text-blue-600 hover:text-blue-800 transition-colors duration-150"
                            >
                                Representatives [
                                {selectedComposition.gate_composition.join(
                                    ", "
                                )}
                                ]
                            </button>
                        )}
                    </>
                )}

                {selectedCircuit && (
                    <>
                        <ChevronRight className="inline w-4 h-4 mx-1" />
                        <span>Circuit {selectedCircuit.id} Details</span>
                    </>
                )}
            </div>
        );
    };

    const renderContent = () => {
        if (loading) {
            return (
                <div className="flex items-center justify-center h-64">
                    <div className="text-gray-600">Loading...</div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex items-center justify-center h-64">
                    <div className="text-red-600">{error}</div>
                </div>
            );
        }

        switch (currentView) {
            case "dimension_groups":
                return (
                    <DimensionGroupsTable
                        dimGroups={dimGroups}
                        onSelect={handleDimGroupSelect}
                        onRefresh={loadDimensionGroups}
                    />
                );

            case "gate_compositions":
                return (
                    <GateCompositionsTable
                        compositions={gateCompositions}
                        dimGroup={selectedDimGroup}
                        onSelect={handleCompositionSelect}
                        onRefresh={() =>
                            selectedDimGroup &&
                            loadGateCompositions(selectedDimGroup.id)
                        }
                    />
                );

            case "representatives":
                return (
                    <RepresentativesTable
                        representatives={representatives}
                        composition={selectedComposition}
                        onSelect={handleCircuitSelect}
                        onRefresh={() =>
                            selectedDimGroup &&
                            loadRepresentatives(
                                selectedDimGroup.id,
                                selectedComposition || undefined
                            )
                        }
                        onRefreshStats={onRefreshStats}
                    />
                );

            case "circuit_details":
                return (
                    <CircuitDetails
                        circuit={selectedCircuit}
                        onBack={handleBackToRepresentatives}
                    />
                );

            default:
                return null;
        }
    };

    return (
        <div className="glass-panel p-5 flex flex-col h-full">
            {/* Breadcrumb Navigation */}
            {renderBreadcrumb()}

            {/* Content Area */}
            <div className="flex-1 overflow-hidden">{renderContent()}</div>
        </div>
    );
}
