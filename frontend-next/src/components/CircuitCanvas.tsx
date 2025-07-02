"use client";

import React, { useCallback, useState, useMemo } from "react";
import { useDrop, useDrag } from "react-dnd";
import {
    Square,
    ArrowRight,
    Zap,
    X,
    Edit3,
    Move,
    Plus,
    Minus,
} from "lucide-react";
import { PlaygroundCircuit, PlaygroundGate, DragItem } from "@/types/api";

// Imports should now work with react-dnd v16 built-in types

interface CircuitCanvasProps {
    circuit: PlaygroundCircuit;
    onGateDrop: (
        gateType: "X" | "CX" | "CCX",
        step: number,
        targetQubit: number
    ) => void;
    onGateMove: (gateId: string, newStep: number, newTarget?: number) => void;
    onGateRemove: (gateId: string) => void;
    onControlEdit: (gateId: string, newControls: number[]) => void;
    selectedTool: "X" | "CX" | "CCX" | null;
    zoom: number;
}

interface DropZoneProps {
    step: number;
    qubit: number;
    hasGate: boolean;
    onDrop: (item: DragItem, step: number, qubit: number) => void;
    onCellClick: () => void;
    selectedTool: "X" | "CX" | "CCX" | null;
    children?: React.ReactNode;
    canAcceptDrop: (item: DragItem) => boolean;
    circuit: PlaygroundCircuit;
}

function DropZone({
    step,
    qubit,
    hasGate,
    onDrop,
    onCellClick,
    selectedTool,
    children,
    canAcceptDrop,
    circuit,
}: DropZoneProps) {
    const [{ isOver, canDrop, draggedItem }, drop] = useDrop(
        () => ({
            accept: "gate",
            drop: (item: DragItem) => {
                onDrop(item, step, qubit);
            },
            canDrop: (item: DragItem) => canAcceptDrop(item),
            collect: (monitor: any) => ({
                isOver: monitor.isOver(),
                canDrop: monitor.canDrop(),
                draggedItem: monitor.getItem(),
            }),
        }),
        [step, qubit, hasGate, canAcceptDrop]
    );

    const [isHovered, setIsHovered] = useState(false);
    const canPlace = selectedTool && !hasGate;

    // Calculate dynamic height - FIXED to not exceed viewport
    const viewportHeight =
        typeof window !== "undefined" ? window.innerHeight : 900;
    const availableHeight = viewportHeight - 400; // More conservative space for header/footer
    const baseHeight = Math.max(
        60,
        Math.min(120, availableHeight / circuit.width)
    );
    const cellHeight = Math.max(50, baseHeight);

    return (
        <div
            ref={drop}
            onClick={onCellClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`
                relative w-28 border transition-all duration-200 cursor-pointer
                ${
                    isOver && canDrop
                        ? "border-green-400 bg-green-500/10"
                        : isOver && !canDrop
                        ? "border-red-400 bg-red-500/10"
                        : canPlace && isHovered
                        ? "border-slate-400 bg-slate-400/10"
                        : canPlace
                        ? "border-slate-600/40 border-dashed"
                        : "border-transparent"
                }
            `}
            style={{ height: cellHeight + "px" }}
        >
            {/* Simplified Quantum Wire - Thinner */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div
                    className="w-full bg-slate-300 relative"
                    style={{ height: "2px" }}
                >
                    <div className="absolute inset-0 bg-blue-400/20 animate-pulse" />
                </div>
            </div>

            {children}

            {/* Simple Placement Preview */}
            {selectedTool && canPlace && isHovered && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-800/40 rounded border border-slate-400">
                    <div className="text-white font-bold text-lg">
                        {selectedTool === "X"
                            ? "X"
                            : selectedTool === "CX"
                            ? "⊕"
                            : "⊕"}
                    </div>
                </div>
            )}

            {/* Clean Drop Indicator */}
            {isOver && draggedItem && (
                <div
                    className={`absolute inset-0 flex items-center justify-center border ${
                        canDrop
                            ? "border-green-400 bg-green-500/20 text-green-300"
                            : "border-red-400 bg-red-500/20 text-red-300"
                    }`}
                >
                    <div className="text-xs font-bold">
                        {canDrop ? "✓" : "✗"}
                    </div>
                </div>
            )}
        </div>
    );
}

interface DraggableControlDotProps {
    gate: PlaygroundGate;
    controlQubit: number;
    relativePos: number;
    cellHeight: number;
    onControlMove: (fromQubit: number, toQubit: number) => void;
    onControlRemove: (controlQubit: number) => void;
    onDragStateChange: (isDragging: boolean) => void;
}

function DraggableControlDot({
    gate,
    controlQubit,
    relativePos,
    cellHeight,
    onControlMove,
    onControlRemove,
    onDragStateChange,
}: DraggableControlDotProps) {
    const [{ isDragging }, drag] = useDrag(
        () => ({
            type: "control",
            item: {
                type: "CONTROL_WIRE",
                gateId: gate.id,
                sourceQubit: controlQubit,
                sourceStep: gate.step,
            },
            collect: (monitor: any) => ({
                isDragging: monitor.isDragging(),
            }),
        }),
        [gate, controlQubit]
    );

    // Notify parent of drag state changes
    React.useEffect(() => {
        onDragStateChange(isDragging);
    }, [isDragging, onDragStateChange]);

    return (
        <div
            ref={drag}
            className={`absolute left-1/2 w-8 h-8 bg-white rounded-full border-4 border-slate-800 transform -translate-x-1/2 -translate-y-1/2 cursor-grab active:cursor-grabbing hover:bg-slate-100 shadow-xl transition-all z-40 ${
                isDragging
                    ? "opacity-70 scale-150 z-50 ring-4 ring-blue-400"
                    : "hover:scale-110"
            }`}
            style={{
                top: relativePos + cellHeight / 2 + "px",
            }}
            onDoubleClick={(e) => {
                e.stopPropagation();
                if (gate.controls.length > 1 || gate.type === "CX") {
                    onControlRemove(controlQubit);
                }
            }}
            title="Drag to move control, double-click to remove"
        />
    );
}

interface ControlDropZoneProps {
    qubit: number;
    gate: PlaygroundGate;
    cellHeight: number;
    onControlMove: (gateId: string, fromQubit: number, toQubit: number) => void;
}

function ControlDropZone({
    qubit,
    gate,
    cellHeight,
    onControlMove,
}: ControlDropZoneProps) {
    const [{ isOver, canDrop }, drop] = useDrop(
        () => ({
            accept: "control",
            drop: (item: any) => {
                if (item.gateId === gate.id && item.sourceQubit !== qubit) {
                    onControlMove(gate.id, item.sourceQubit, qubit);
                }
            },
            canDrop: (item: any) => {
                return (
                    item.gateId === gate.id &&
                    qubit !== gate.target &&
                    !gate.controls.includes(qubit) &&
                    item.sourceQubit !== qubit
                );
            },
            collect: (monitor: any) => ({
                isOver: monitor.isOver(),
                canDrop: monitor.canDrop(),
            }),
        }),
        [qubit, gate, onControlMove]
    );

    // Don't show drop zone on target or existing controls, but allow all other qubits
    if (qubit === gate.target || gate.controls.includes(qubit)) {
        return null;
    }

    // Calculate relative position from the gate's target position
    const relativeTop = (qubit - gate.target) * cellHeight + cellHeight / 2;

    return (
        <div
            ref={drop}
            className={`absolute left-1/2 w-12 h-12 transform -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-dashed transition-all z-30 ${
                isOver && canDrop
                    ? "border-green-400 bg-green-500/50 scale-125 shadow-lg ring-4 ring-green-300/60"
                    : isOver
                    ? "border-red-400 bg-red-500/50 scale-110 ring-4 ring-red-300/60"
                    : "border-blue-400/60 bg-blue-500/20 hover:border-blue-400 hover:bg-blue-500/30 hover:scale-110"
            }`}
            style={{
                top: relativeTop + "px",
            }}
        >
            {isOver && (
                <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-white drop-shadow-lg">
                    {canDrop ? "✓" : "✗"}
                </div>
            )}
        </div>
    );
}

interface DraggableGateProps {
    gate: PlaygroundGate;
    onRemove: () => void;
    onControlEdit: (newControls: number[]) => void;
    circuitWidth: number;
    cellHeight: number;
    isDraggedControlGate: boolean;
    onControlDragChange: (gateId: string | null) => void;
}

function DraggableGate({
    gate,
    onRemove,
    onControlEdit,
    circuitWidth,
    cellHeight,
    isDraggedControlGate,
    onControlDragChange,
}: DraggableGateProps) {
    const [{ isDragging }, drag, dragPreview] = useDrag(
        () => ({
            type: "gate",
            item: {
                type: "EXISTING_GATE",
                gateId: gate.id,
                gateType: gate.type,
                originalStep: gate.step,
                originalTarget: gate.target,
                originalControls: gate.controls,
            },
            collect: (monitor: any) => ({
                isDragging: monitor.isDragging(),
            }),
        }),
        [gate]
    );

    const [isHovered, setIsHovered] = useState(false);

    // Only show drop zones for THIS gate when its control is being dragged
    const isControlDragging = isDraggedControlGate;

    const getGateSymbol = () => {
        switch (gate.type) {
            case "X":
                return "X";
            case "CX":
                return "⊕";
            case "CCX":
                return "⊕";
            default:
                return gate.type;
        }
    };

    const getGateColor = () => {
        switch (gate.type) {
            case "X":
                return "text-red-400 border-red-400 bg-red-500/10";
            case "CX":
                return "text-blue-400 border-blue-400 bg-blue-500/10";
            case "CCX":
                return "text-purple-400 border-purple-400 bg-purple-500/10";
            default:
                return "text-slate-400 border-slate-400 bg-slate-500/10";
        }
    };

    const handleControlMove = useCallback(
        (fromQubit: number, toQubit: number) => {
            const newControls = gate.controls.map((c) =>
                c === fromQubit ? toQubit : c
            );
            onControlEdit(newControls);
        },
        [gate.controls, onControlEdit]
    );

    const handleControlDragStateChange = useCallback(
        (isDragging: boolean) => {
            onControlDragChange(isDragging ? gate.id : null);
        },
        [gate.id, onControlDragChange]
    );

    const handleControlRemove = useCallback(
        (controlQubit: number) => {
            const newControls = gate.controls.filter((c) => c !== controlQubit);
            onControlEdit(newControls);
        },
        [gate.controls, onControlEdit]
    );

    const handleControlAdd = useCallback(
        (gateId: string, fromQubit: number, toQubit: number) => {
            if (gateId === gate.id) {
                handleControlMove(fromQubit, toQubit);
            }
        },
        [gate.id, handleControlMove]
    );

    const wireSpacing = cellHeight;

    return (
        <div
            className={`absolute inset-0 ${isDragging ? "opacity-50" : ""}`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Clean Control Wires */}
            {gate.type !== "X" && (
                <div className="absolute inset-0 pointer-events-none">
                    {/* Draw vertical wire from each control to target */}
                    {gate.controls.map((controlQubit, index) => {
                        const relativePos =
                            (controlQubit - gate.target) * wireSpacing;
                        const minY = Math.min(0, relativePos);
                        const maxY = Math.max(0, relativePos);
                        const height = Math.abs(relativePos);

                        return (
                            <div
                                key={`control-wire-${index}`}
                                className="absolute left-1/2 w-px bg-slate-400"
                                style={{
                                    top: minY + cellHeight / 2 + "px",
                                    height: height + "px",
                                    transform: "translateX(-50%)",
                                }}
                            />
                        );
                    })}
                </div>
            )}

            {/* Draggable Control Dots */}
            {gate.type !== "X" &&
                gate.controls.map((controlQubit, index) => {
                    const relativePos =
                        (controlQubit - gate.target) * wireSpacing;
                    return (
                        <DraggableControlDot
                            key={`control-dot-${index}`}
                            gate={gate}
                            controlQubit={controlQubit}
                            relativePos={relativePos}
                            cellHeight={cellHeight}
                            onControlMove={handleControlMove}
                            onControlRemove={handleControlRemove}
                            onDragStateChange={handleControlDragStateChange}
                        />
                    );
                })}

            {/* Control Drop Zones for all qubits - Show ONLY when dragging any control */}
            {gate.type !== "X" &&
                isControlDragging &&
                Array.from({ length: circuitWidth }, (_, qubit) => {
                    return (
                        <ControlDropZone
                            key={`drop-zone-${qubit}`}
                            qubit={qubit}
                            gate={gate}
                            cellHeight={cellHeight}
                            onControlMove={handleControlAdd}
                        />
                    );
                })}

            {/* Clean Main Gate Symbol */}
            <div
                ref={drag}
                className={`
                    absolute inset-1 rounded border-2 transition-all duration-200 cursor-move
                    flex items-center justify-center font-bold text-2xl
                    ${getGateColor()}
                    ${
                        isDragging
                            ? "scale-110 rotate-3 z-50"
                            : isHovered
                            ? "scale-105"
                            : ""
                    }
                `}
            >
                {getGateSymbol()}
            </div>

            {/* Clean Remove Button */}
            {isHovered && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove();
                    }}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center text-white text-xs"
                >
                    ×
                </button>
            )}

            <div ref={dragPreview} style={{ opacity: isDragging ? 0 : 1 }} />
        </div>
    );
}

interface MinimapProps {
    circuit: PlaygroundCircuit;
    viewportStart: number;
    viewportWidth: number;
    onScrollTo: (step: number) => void;
}

function SmoothViewportMinimap({
    circuit,
    viewportStart,
    viewportWidth,
    onScrollTo,
}: MinimapProps) {
    const minimapWidth = 400;
    const stepWidth = minimapWidth / circuit.length;

    return (
        <div className="bg-slate-800/80 rounded-xl border border-slate-600/50 p-4 shadow-lg">
            <div className="text-sm text-slate-300 mb-3 font-medium">
                Circuit Overview
            </div>
            <div
                className="relative bg-slate-900/90 rounded-lg h-12 border border-slate-600/40 overflow-hidden cursor-pointer shadow-inner"
                style={{ width: minimapWidth }}
                onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    const clickedStep = Math.floor(
                        (clickX / minimapWidth) * circuit.length
                    );
                    onScrollTo(clickedStep);
                }}
            >
                {/* Gate indicators */}
                {circuit.gates.map((gate) => (
                    <div
                        key={gate.id}
                        className={`absolute top-1 w-1.5 h-10 rounded-full shadow-sm ${
                            gate.type === "X"
                                ? "bg-red-400"
                                : gate.type === "CX"
                                ? "bg-blue-400"
                                : "bg-purple-400"
                        }`}
                        style={{ left: gate.step * stepWidth }}
                        title={`${gate.type} at step ${gate.step}`}
                    />
                ))}

                {/* Viewport indicator */}
                <div
                    className="absolute top-0 h-full bg-blue-400/30 border-2 border-blue-400/60 rounded backdrop-blur-sm transition-all duration-200"
                    style={{
                        left: viewportStart * stepWidth,
                        width: viewportWidth * stepWidth,
                    }}
                />

                {/* Step markers every 4 steps */}
                {Array.from(
                    { length: Math.floor(circuit.length / 4) },
                    (_, i) => i * 4
                ).map((step) => (
                    <div
                        key={step}
                        className="absolute top-0 w-px h-full bg-slate-600/30"
                        style={{ left: step * stepWidth }}
                    />
                ))}
            </div>
            <div className="text-xs text-slate-400 mt-2">
                Click anywhere to scroll to that position
            </div>
        </div>
    );
}

export default function CircuitCanvas({
    circuit,
    onGateDrop,
    onGateMove,
    onGateRemove,
    onControlEdit,
    selectedTool,
    zoom,
}: CircuitCanvasProps) {
    const [scrollContainer, setScrollContainer] =
        useState<HTMLDivElement | null>(null);
    const [viewportStart, setViewportStart] = useState(0);
    const viewportWidth = 8; // Show 8 steps at a time
    const [draggedControlGateId, setDraggedControlGateId] = useState<
        string | null
    >(null);

    // Drop validation and gate pushing logic
    const canAcceptDrop = useCallback(
        (item: DragItem, step: number, qubit: number) => {
            return true;
        },
        []
    );

    const handleDrop = useCallback(
        (item: DragItem, step: number, qubit: number) => {
            const extendedStep = Math.max(step, 0);

            if (item.type === "NEW_GATE" && item.gateType) {
                onGateDrop(item.gateType, extendedStep, qubit);
            } else if (item.type === "EXISTING_GATE" && item.gateId) {
                onGateMove(item.gateId, extendedStep, qubit);
            }
        },
        [onGateDrop, onGateMove]
    );

    const handleCellClick = useCallback(
        (step: number, qubit: number) => {
            if (!selectedTool) return;
            onGateDrop(selectedTool, step, qubit);
        },
        [selectedTool, onGateDrop]
    );

    // Create enhanced grid data structure
    const gridData = useMemo(() => {
        const grid: (PlaygroundGate | null)[][] = Array(circuit.width)
            .fill(null)
            .map(() => Array(circuit.length).fill(null));

        circuit.gates.forEach((gate) => {
            if (gate.step < circuit.length && gate.target < circuit.width) {
                grid[gate.target][gate.step] = gate;
            }
        });

        return grid;
    }, [circuit.gates, circuit.width, circuit.length]);

    // Calculate viewport based on scroll position
    const updateViewportFromScroll = useCallback(() => {
        if (scrollContainer) {
            const stepWidth = 112;
            const scrollLeft = scrollContainer.scrollLeft;
            const newViewportStart = Math.floor(scrollLeft / stepWidth);
            setViewportStart(newViewportStart);
        }
    }, [scrollContainer]);

    // Listen to scroll events
    React.useEffect(() => {
        if (scrollContainer) {
            scrollContainer.addEventListener(
                "scroll",
                updateViewportFromScroll
            );
            return () =>
                scrollContainer.removeEventListener(
                    "scroll",
                    updateViewportFromScroll
                );
        }
    }, [scrollContainer, updateViewportFromScroll]);

    // Show viewport steps but render all for smooth scrolling
    const visibleSteps = Array.from({ length: circuit.length }, (_, i) => i);

    // Calculate dynamic height
    const viewportHeight =
        typeof window !== "undefined" ? window.innerHeight : 900;
    const availableHeight = viewportHeight - 400;
    const baseHeight = Math.max(
        60,
        Math.min(120, availableHeight / circuit.width)
    );
    const cellHeight = Math.max(50, baseHeight);

    // Scroll to specific step
    const handleScrollTo = useCallback(
        (step: number) => {
            if (scrollContainer) {
                const stepWidth = 112;
                const targetScrollLeft = step * stepWidth;
                scrollContainer.scrollTo({
                    left: targetScrollLeft,
                    behavior: "smooth",
                });
            }
        },
        [scrollContainer]
    );

    return (
        <div className="flex flex-col h-full w-full min-w-0">
            {/* Main Circuit Area with Smooth Horizontal Scrolling */}
            <div
                ref={setScrollContainer}
                className="flex-1 overflow-x-auto overflow-y-hidden"
                style={{
                    padding: "60px 40px 40px 180px",
                    maxWidth: "100%",
                    width: "100%",
                    boxSizing: "border-box",
                    minWidth: 0, // Allow shrinking
                    height: "100%",
                    position: "relative",
                }}
            >
                <div
                    className="relative"
                    style={{
                        transform: `scale(${zoom})`,
                        transformOrigin: "top left",
                        width: `${circuit.length * 112}px`,
                        minWidth: `${circuit.length * 112}px`,
                        height: "fit-content",
                        flexShrink: 0,
                        display: "block",
                    }}
                >
                    {/* Clean Qubit Labels */}
                    <div
                        className="absolute top-0 flex flex-col gap-0"
                        style={{ left: "-160px" }}
                    >
                        {Array.from({ length: circuit.width }, (_, qubit) => (
                            <div
                                key={qubit}
                                className="flex items-center justify-end pr-4 text-slate-300 font-mono text-sm"
                                style={{ height: cellHeight + "px" }}
                            >
                                <div className="bg-slate-800 px-2 py-1 rounded border border-slate-600">
                                    |q{qubit}⟩
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Clean Step Labels - Fixed Alignment */}
                    <div
                        className="absolute left-0 flex gap-0"
                        style={{ top: "-40px" }}
                    >
                        {visibleSteps.map((step) => (
                            <div
                                key={step}
                                className="flex items-center justify-center"
                                style={{ width: "112px" }}
                            >
                                <div className="text-sm text-slate-400 font-mono bg-slate-800 py-1 px-2 rounded border border-slate-600">
                                    t{step}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Main Circuit Grid - Full Width for Smooth Scrolling */}
                    <div
                        className="grid gap-0"
                        style={{
                            gridTemplateColumns: `repeat(${circuit.length}, 112px)`,
                        }}
                    >
                        {Array.from({ length: circuit.width }, (_, qubit) =>
                            visibleSteps.map((step) => {
                                const gate = gridData[qubit][step];
                                const isTargetQubit = gate?.target === qubit;

                                return (
                                    <DropZone
                                        key={`${step}-${qubit}`}
                                        step={step}
                                        qubit={qubit}
                                        hasGate={!!gate}
                                        onDrop={handleDrop}
                                        onCellClick={() =>
                                            handleCellClick(step, qubit)
                                        }
                                        selectedTool={selectedTool}
                                        canAcceptDrop={(item) =>
                                            canAcceptDrop(item, step, qubit)
                                        }
                                        circuit={circuit}
                                    >
                                        {isTargetQubit && gate && (
                                            <DraggableGate
                                                gate={gate}
                                                onRemove={() =>
                                                    onGateRemove(gate.id)
                                                }
                                                onControlEdit={(newControls) =>
                                                    onControlEdit(
                                                        gate.id,
                                                        newControls
                                                    )
                                                }
                                                circuitWidth={circuit.width}
                                                cellHeight={cellHeight}
                                                isDraggedControlGate={
                                                    draggedControlGateId ===
                                                    gate.id
                                                }
                                                onControlDragChange={
                                                    setDraggedControlGateId
                                                }
                                            />
                                        )}
                                    </DropZone>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>

            {/* Enhanced Navigation with Smooth Minimap - No Buttons */}
            {circuit.length > viewportWidth && (
                <div className="border-t border-slate-700/50 p-4 bg-slate-800/40 backdrop-blur-sm">
                    <div className="flex items-center justify-between">
                        <div className="text-sm text-slate-400 flex items-center gap-2">
                            <span>← Scroll horizontally to navigate →</span>
                            <span className="font-mono text-xs">
                                Showing steps {viewportStart}-
                                {Math.min(
                                    viewportStart + viewportWidth - 1,
                                    circuit.length - 1
                                )}{" "}
                                of {circuit.length}
                            </span>
                        </div>

                        <SmoothViewportMinimap
                            circuit={circuit}
                            viewportStart={viewportStart}
                            viewportWidth={viewportWidth}
                            onScrollTo={handleScrollTo}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
