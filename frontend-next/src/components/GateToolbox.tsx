"use client";

import React from "react";
import { useDrag } from "react-dnd";
import { Square, ArrowRight, Zap, Plus } from "lucide-react";

// Test comment to verify imports are working

interface GateToolboxProps {
    selectedTool: "X" | "CX" | "CCX" | null;
    onToolSelect: (tool: "X" | "CX" | "CCX" | null) => void;
    onAddLine?: () => void;
    onDeleteLine?: () => void;
    onAddStep: () => void;
    onRandomGenerate?: (customLength?: number) => Promise<void>;
    isGenerating?: boolean;
    circuitLength?: number;
    circuitWidth?: number;
}

interface DraggableGateProps {
    type: "X" | "CX" | "CCX";
    icon: React.ReactNode;
    name: string;
    description: string;
    color: string;
    borderColor: string;
    isSelected: boolean;
    onSelect: () => void;
}

function DraggableGate({
    type,
    icon,
    name,
    description,
    color,
    borderColor,
    isSelected,
    onSelect,
}: DraggableGateProps) {
    const [{ isDragging }, drag] = useDrag(
        () => ({
            type: "gate",
            item: { type: "NEW_GATE", gateType: type },
            collect: (monitor: any) => ({
                isDragging: !!monitor.isDragging(),
            }),
        }),
        [type]
    );

    return (
        <div
            ref={drag}
            onClick={onSelect}
            className={`
                relative cursor-grab active:cursor-grabbing p-4 rounded-xl border-2 transition-all duration-300
                ${
                    isSelected
                        ? `${color} ${borderColor} shadow-lg scale-105`
                        : `bg-slate-800/60 border-slate-600/50 hover:${color} hover:${borderColor} hover:scale-102`
                }
                ${isDragging ? "opacity-30" : ""}
            `}
        >
            <div className="flex items-center gap-3 mb-3">
                <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
                <div>
                    <h3 className="font-bold text-white text-lg">{name}</h3>
                    <p className="text-xs text-slate-400">{type} Gate</p>
                </div>
            </div>
            <p className="text-sm text-slate-300">{description}</p>

            {isSelected && (
                <div className="absolute top-2 right-2 bg-white/20 text-white text-xs px-2 py-1 rounded-full">
                    Selected
                </div>
            )}

            {/* Simple drag preview */}
            {isDragging && (
                <div
                    className={`absolute inset-0 ${color} rounded-xl border-2 ${borderColor} flex items-center justify-center`}
                >
                    <div className="text-white font-bold text-2xl">
                        {type === "X" ? "X" : "⊕"}
                    </div>
                </div>
            )}
        </div>
    );
}

export default function GateToolbox({
    selectedTool,
    onToolSelect,
    onAddLine,
    onDeleteLine,
    onAddStep,
    onRandomGenerate,
    isGenerating,
    circuitLength,
    circuitWidth,
}: GateToolboxProps) {
    const gates = [
        {
            type: "X" as const,
            icon: <Square className="w-6 h-6 text-red-300" />,
            name: "NOT Gate",
            description: "Flips the state of a single qubit (Pauli-X gate)",
            color: "bg-red-500/30",
            borderColor: "border-red-500/70",
        },
        {
            type: "CX" as const,
            icon: <ArrowRight className="w-6 h-6 text-blue-300" />,
            name: "CNOT Gate",
            description: "Controlled-NOT with one control and one target qubit",
            color: "bg-blue-500/30",
            borderColor: "border-blue-500/70",
        },
        {
            type: "CCX" as const,
            icon: <Zap className="w-6 h-6 text-purple-300" />,
            name: "Toffoli Gate",
            description: "Controlled-controlled-NOT (CCNOT) with two controls",
            color: "bg-purple-500/30",
            borderColor: "border-purple-500/70",
        },
    ];

    return (
        <div className="space-y-4">
            {/* Gate Cards */}
            {gates.map((gate) => (
                <DraggableGate
                    key={gate.type}
                    type={gate.type}
                    icon={gate.icon}
                    name={gate.name}
                    description={gate.description}
                    color={gate.color}
                    borderColor={gate.borderColor}
                    isSelected={selectedTool === gate.type}
                    onSelect={() =>
                        onToolSelect(
                            selectedTool === gate.type ? null : gate.type
                        )
                    }
                />
            ))}

            {/* Add/Delete Line Buttons */}
            <div className="flex gap-2">
                {onAddLine && (
                    <button
                        onClick={onAddLine}
                        className="flex-1 p-3 rounded-xl border-2 border-dashed border-slate-500 hover:border-slate-400 text-slate-400 hover:text-slate-300 transition-all duration-200 flex items-center justify-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        <span className="font-medium text-sm">Add Line</span>
                    </button>
                )}

                {onDeleteLine && (
                    <button
                        onClick={onDeleteLine}
                        disabled={!circuitWidth || circuitWidth <= 2}
                        className="flex-1 p-3 rounded-xl border-2 border-dashed border-red-500 hover:border-red-400 disabled:border-slate-600 disabled:text-slate-500 text-red-400 hover:text-red-300 transition-all duration-200 flex items-center justify-center gap-2"
                    >
                        <span className="w-4 h-4 text-center">−</span>
                        <span className="font-medium text-sm">Delete Line</span>
                    </button>
                )}
            </div>

            {/* Random Circuit Generation */}
            {onRandomGenerate && (
                <div className="bg-slate-700/40 p-4 rounded-xl border border-slate-600/50 space-y-3">
                    <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                        🎲 Random Circuit
                    </h3>

                    <div className="flex gap-2">
                        <button
                            onClick={() => onRandomGenerate()}
                            disabled={isGenerating}
                            className="flex-1 px-3 py-2 bg-purple-600/80 hover:bg-purple-500/80 disabled:bg-purple-600/50 text-white rounded-lg transition-all duration-200 font-medium text-sm"
                        >
                            {isGenerating ? "Generating..." : "Current"}
                        </button>
                        <button
                            onClick={() =>
                                onRandomGenerate(
                                    Math.max(circuitLength || 12, 16)
                                )
                            }
                            disabled={isGenerating}
                            className="flex-1 px-3 py-2 bg-blue-600/80 hover:bg-blue-500/80 disabled:bg-blue-600/50 text-white rounded-lg transition-all duration-200 font-medium text-sm"
                        >
                            Extended
                        </button>
                    </div>

                    <div className="text-xs text-slate-400">
                        Current: {circuitLength || 12} steps
                    </div>
                </div>
            )}

            {/* Add Step Button */}
            <button
                onClick={onAddStep}
                className="w-full mt-4 p-4 bg-slate-700/60 hover:bg-slate-600/60 rounded-xl border-2 border-dashed border-slate-500/60 hover:border-slate-400/60 transition-all duration-200 text-slate-300 hover:text-white"
            >
                <div className="flex items-center justify-center gap-2">
                    <span className="text-2xl">+</span>
                    <span className="font-medium">Add Step</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                    Extend circuit length
                </div>
            </button>
        </div>
    );
}
