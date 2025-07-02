"use client";

import React, { useState, useCallback, useMemo, useRef } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { RotateCcw, Shuffle, Plus, Minus, ZoomIn, ZoomOut } from "lucide-react";
import GateToolbox from "./GateToolbox";
import CircuitCanvas from "./CircuitCanvas";
import MetricsPanel from "./MetricsPanel";
import { PlaygroundCircuit, PlaygroundGate, LiveMetrics } from "@/types/api";

const INITIAL_WIDTH = 3;
const INITIAL_LENGTH = 12;
const MIN_WIDTH = 2;
const MAX_WIDTH = 12;
const MIN_LENGTH = 8;

export default function CircuitPlayground() {
    const [circuit, setCircuit] = useState<PlaygroundCircuit>({
        width: INITIAL_WIDTH,
        length: INITIAL_LENGTH,
        gates: [],
    });

    const [selectedTool, setSelectedTool] = useState<"X" | "CX" | "CCX" | null>(
        null
    );
    const [isGenerating, setIsGenerating] = useState(false);
    const [zoom, setZoom] = useState(1);
    const canvasRef = useRef<HTMLDivElement>(null);

    // Calculate live metrics - Match the actual LiveMetrics interface
    const metrics = useMemo((): LiveMetrics => {
        const gateCount = circuit.gates.length;
        const depth =
            circuit.gates.length > 0
                ? Math.max(...circuit.gates.map((g) => g.step)) + 1
                : 0;

        // Calculate permutation
        const permutation = calculateCircuitPermutation(circuit);
        const isIdentity = permutation.every((val, idx) => val === idx);

        // Calculate Hamming distance for identity circuits
        const hammingDistance = permutation.reduce(
            (dist, val, idx) => dist + (val !== idx ? 1 : 0),
            0
        );

        // Gate composition as tuple [X, CX, CCX]
        const xCount = circuit.gates.filter((g) => g.type === "X").length;
        const cxCount = circuit.gates.filter((g) => g.type === "CX").length;
        const ccxCount = circuit.gates.filter((g) => g.type === "CCX").length;

        return {
            gateCount: gateCount,
            gateComposition: [xCount, cxCount, ccxCount] as [
                number,
                number,
                number
            ],
            depth: depth,
            isIdentity: isIdentity,
            permutation: permutation,
            qubitConnectivity: 1.0, // Always 100% since we use all qubits
            hamming_distance: hammingDistance,
        };
    }, [circuit]);

    // Smart gate placement logic - FIXED to match interface
    const findBestPlacement = useCallback(
        (
            gateType: "X" | "CX" | "CCX",
            targetQubit: number
        ): {
            target: number;
            controls: number[];
        } => {
            switch (gateType) {
                case "X":
                    return { target: targetQubit, controls: [] };

                case "CX":
                    // Place control one line above target, unless target is 0
                    const cxControl =
                        targetQubit > 0 ? targetQubit - 1 : targetQubit + 1;
                    return {
                        target: targetQubit,
                        controls: [Math.min(cxControl, circuit.width - 1)],
                    };

                case "CCX":
                    // Find two nearest available qubits for controls
                    const availableQubits = Array.from(
                        { length: circuit.width },
                        (_, i) => i
                    ).filter((q) => q !== targetQubit);

                    // Prefer qubits closest to target
                    availableQubits.sort(
                        (a, b) =>
                            Math.abs(a - targetQubit) -
                            Math.abs(b - targetQubit)
                    );

                    const controls = availableQubits.slice(0, 2);
                    return { target: targetQubit, controls: controls.sort() };

                default:
                    return { target: targetQubit, controls: [] };
            }
        },
        [circuit.width]
    );

    const handleGateDrop = useCallback(
        (gateType: "X" | "CX" | "CCX", step: number, targetQubit: number) => {
            // Check if step is beyond current length and extend if needed
            const newLength = Math.max(circuit.length, step + 1);

            // Check if step has a gate and push if needed (only for new gates)
            const existingGate = circuit.gates.find((g) => g.step === step);
            if (existingGate) {
                // Push all gates at this step and after to the right
                const updatedGates = circuit.gates.map((g) =>
                    g.step >= step ? { ...g, step: g.step + 1 } : g
                );

                const finalLength = Math.max(
                    newLength + 1,
                    Math.max(...updatedGates.map((g) => g.step)) + 1
                );

                const placement = findBestPlacement(gateType, targetQubit);
                const newGate: PlaygroundGate = {
                    id: `gate-${Date.now()}-${Math.random()}`,
                    type: gateType,
                    step,
                    target: placement.target,
                    controls: placement.controls,
                };

                setCircuit((prev) => ({
                    ...prev,
                    gates: [...updatedGates, newGate],
                    length: finalLength,
                }));
            } else {
                // Empty step - just place the gate
                const placement = findBestPlacement(gateType, targetQubit);
                const newGate: PlaygroundGate = {
                    id: `gate-${Date.now()}-${Math.random()}`,
                    type: gateType,
                    step,
                    target: placement.target,
                    controls: placement.controls,
                };

                setCircuit((prev) => ({
                    ...prev,
                    gates: [...prev.gates, newGate],
                    length: newLength,
                }));
            }

            // Auto-extend if all steps are now occupied
            setTimeout(() => {
                setCircuit((current) => {
                    const occupiedSteps = new Set(
                        current.gates.map((g) => g.step)
                    );
                    const allStepsOccupied =
                        occupiedSteps.size === current.length;

                    if (allStepsOccupied) {
                        return { ...current, length: current.length + 2 }; // Add 2 extra steps
                    }
                    return current;
                });
            }, 100);
        },
        [circuit.gates, circuit.length, findBestPlacement]
    );

    const handleGateMove = useCallback(
        (gateId: string, newStep: number, newTarget?: number) => {
            const gate = circuit.gates.find((g) => g.id === gateId);
            if (!gate) return;

            const oldStep = gate.step;
            const updatedTarget =
                newTarget !== undefined ? newTarget : gate.target;

            // Extend circuit if needed
            const newLength = Math.max(circuit.length, newStep + 1);

            // Validate gate can fit at new position with preserved controls
            const validateGateFit = (
                gateType: "X" | "CX" | "CCX",
                target: number,
                controls: number[]
            ): boolean => {
                if (gateType === "X")
                    return target >= 0 && target < circuit.width;

                // Check if all controls and target are within circuit bounds
                const allQubits = [target, ...controls];
                return (
                    allQubits.every((q) => q >= 0 && q < circuit.width) &&
                    controls.every((c) => c !== target) &&
                    controls.length === new Set(controls).size
                ); // No duplicate controls
            };

            // Calculate control offset preservation
            const preserveControlOffsets = (
                gateType: "X" | "CX" | "CCX",
                newTarget: number,
                oldControls: number[],
                oldTarget: number
            ): { controls: number[]; valid: boolean } => {
                if (gateType === "X") return { controls: [], valid: true };

                // Calculate relative offsets from old target
                const offsets = oldControls.map(
                    (control) => control - oldTarget
                );

                // Apply offsets to new target
                const newControls = offsets.map((offset) => newTarget + offset);

                // Check if the preserved gate fits
                const valid = validateGateFit(gateType, newTarget, newControls);

                if (valid) {
                    return { controls: newControls.sort(), valid: true };
                } else {
                    // If preserved shape doesn't fit, reject the move
                    return { controls: oldControls, valid: false };
                }
            };

            // Check if target step has a gate (excluding the gate being moved)
            const existingGate = circuit.gates.find(
                (g) => g.step === newStep && g.id !== gateId
            );

            // Try to preserve control offsets
            const preservationResult = preserveControlOffsets(
                gate.type,
                updatedTarget,
                gate.controls,
                gate.target
            );

            // If gate doesn't fit with preserved shape, don't allow the move
            if (!preservationResult.valid) {
                console.log(
                    "Gate doesn't fit at target position with current control configuration"
                );
                return;
            }

            if (existingGate) {
                // Reordering logic: insert at new position and shift others
                const otherGates = circuit.gates.filter((g) => g.id !== gateId);

                let updatedGates: PlaygroundGate[];
                if (newStep > oldStep) {
                    // Moving right: shift gates between oldStep and newStep to the left
                    updatedGates = otherGates.map((g) => {
                        if (g.step > oldStep && g.step <= newStep) {
                            return { ...g, step: g.step - 1 };
                        }
                        return g;
                    });
                } else {
                    // Moving left: shift gates between newStep and oldStep to the right
                    updatedGates = otherGates.map((g) => {
                        if (g.step >= newStep && g.step < oldStep) {
                            return { ...g, step: g.step + 1 };
                        }
                        return g;
                    });
                }

                const movedGate = {
                    ...gate,
                    step: newStep,
                    target: updatedTarget,
                    controls: preservationResult.controls,
                };

                const finalLength = Math.max(
                    newLength,
                    Math.max(...updatedGates.map((g) => g.step), newStep) + 1
                );

                setCircuit((prev) => ({
                    ...prev,
                    gates: [...updatedGates, movedGate],
                    length: finalLength,
                }));
            } else {
                // Empty position - just move the gate
                setCircuit((prev) => ({
                    ...prev,
                    gates: prev.gates.map((g) =>
                        g.id === gateId
                            ? {
                                  ...g,
                                  step: newStep,
                                  target: updatedTarget,
                                  controls: preservationResult.controls,
                              }
                            : g
                    ),
                    length: newLength,
                }));
            }
        },
        [circuit.gates, circuit.width, circuit.length]
    );

    const handleGateRemove = useCallback((gateId: string) => {
        setCircuit((prev) => ({
            ...prev,
            gates: prev.gates.filter((g) => g.id !== gateId),
        }));
    }, []);

    const handleControlEdit = useCallback(
        (gateId: string, newControls: number[]) => {
            setCircuit((prev) => ({
                ...prev,
                gates: prev.gates.map((gate) =>
                    gate.id === gateId
                        ? { ...gate, controls: newControls }
                        : gate
                ),
            }));
        },
        []
    );

    const handleWidthChange = useCallback(
        (delta: number) => {
            const newWidth = Math.max(
                MIN_WIDTH,
                Math.min(MAX_WIDTH, circuit.width + delta)
            );
            setCircuit((prev) => ({
                ...prev,
                width: newWidth,
                // Remove gates that would be invalid with new width
                gates: prev.gates.filter(
                    (gate) =>
                        gate.target < newWidth &&
                        gate.controls.every((c) => c < newWidth)
                ),
            }));
        },
        [circuit.width]
    );

    const handleLengthChange = useCallback(
        (delta: number) => {
            const newLength = Math.max(MIN_LENGTH, circuit.length + delta);
            setCircuit((prev) => ({
                ...prev,
                length: newLength,
                // Remove gates beyond new length
                gates: prev.gates.filter((gate) => gate.step < newLength),
            }));
        },
        [circuit.length]
    );

    const handleClear = useCallback(() => {
        setCircuit((prev) => ({
            ...prev,
            gates: [],
        }));
    }, []);

    // Build gate pool similar to backend approach
    const buildGatePool = useCallback((width: number) => {
        const gates: {
            type: "X" | "CX" | "CCX";
            target: number;
            controls: number[];
        }[] = [];

        // X gates on each qubit
        for (let i = 0; i < width; i++) {
            gates.push({ type: "X", target: i, controls: [] });
        }

        // CX gates (all possible control/target combinations)
        for (let control = 0; control < width; control++) {
            for (let target = 0; target < width; target++) {
                if (control !== target) {
                    gates.push({ type: "CX", target, controls: [control] });
                }
            }
        }

        // CCX gates (Toffoli) for 3+ qubits - normalized with sorted controls
        if (width >= 3) {
            for (let control1 = 0; control1 < width; control1++) {
                for (
                    let control2 = control1 + 1;
                    control2 < width;
                    control2++
                ) {
                    for (let target = 0; target < width; target++) {
                        if (target !== control1 && target !== control2) {
                            gates.push({
                                type: "CCX",
                                target,
                                controls: [control1, control2],
                            });
                        }
                    }
                }
            }
        }

        return gates;
    }, []);

    const handleRandomGenerate = useCallback(
        async (customLength?: number) => {
            setIsGenerating(true);

            try {
                const gatePool = buildGatePool(circuit.width);

                // Clear existing gates first
                setCircuit((prev) => ({ ...prev, gates: [] }));

                // Generate random number of gates (4-12 gates for good visual results)
                const minGates = 4;
                const maxGates = Math.min(12, circuit.width * 3);
                const numGates =
                    Math.floor(Math.random() * (maxGates - minGates + 1)) +
                    minGates;

                const randomGates: PlaygroundGate[] = [];

                // Place gates sequentially from step 0 onwards (no gaps!)
                for (let i = 0; i < numGates; i++) {
                    // Pick random gate from pool
                    const gateTemplate =
                        gatePool[Math.floor(Math.random() * gatePool.length)];

                    randomGates.push({
                        id: `random-${Date.now()}-${i}`,
                        type: gateTemplate.type,
                        step: i, // Sequential placement - no gaps!
                        target: gateTemplate.target,
                        controls: [...gateTemplate.controls],
                    });
                }

                // Calculate final length: either custom length or just enough for the gates + some buffer
                const gateLength = numGates;
                const finalLength = customLength
                    ? Math.max(customLength, gateLength)
                    : Math.max(circuit.length, gateLength + 2); // Add 2 buffer steps

                setCircuit((prev) => ({
                    ...prev,
                    gates: randomGates,
                    length: finalLength,
                }));
            } finally {
                setIsGenerating(false);
            }
        },
        [circuit.width, circuit.length, buildGatePool]
    );

    const handleCompressCircuit = useCallback(() => {
        if (circuit.gates.length === 0) return;

        // Sort gates by step
        const sortedGates = [...circuit.gates].sort((a, b) => a.step - b.step);

        // Reassign steps sequentially starting from 0
        const compressedGates = sortedGates.map((gate, index) => ({
            ...gate,
            step: index,
        }));

        // Calculate new circuit length (gates + small buffer)
        const newLength = Math.max(compressedGates.length + 2, circuit.length);

        setCircuit((prev) => ({
            ...prev,
            gates: compressedGates,
            length: newLength,
        }));
    }, [circuit.gates, circuit.length]);

    const handleAddStep = useCallback(() => {
        setCircuit((prev) => ({ ...prev, length: prev.length + 1 }));
    }, []);

    const handleAddLine = useCallback(() => {
        setCircuit((prev) => ({ ...prev, width: prev.width + 1 }));
    }, []);

    const handleDeleteLine = useCallback(() => {
        if (circuit.width <= MIN_WIDTH) return; // Don't allow deleting below minimum

        const lineToDelete = circuit.width - 1; // Delete the last line

        setCircuit((prev) => {
            // Remove gates that have target or controls on the deleted line
            const filteredGates = prev.gates.filter((gate) => {
                // Remove if target is on deleted line
                if (gate.target === lineToDelete) return false;

                // Remove if any control is on deleted line
                if (gate.controls.includes(lineToDelete)) return false;

                return true;
            });

            // Adjust remaining gates: shift targets and controls down if they're above deleted line
            const adjustedGates = filteredGates.map((gate) => ({
                ...gate,
                target:
                    gate.target > lineToDelete ? gate.target - 1 : gate.target,
                controls: gate.controls
                    .filter((control) => control !== lineToDelete) // Safety filter (shouldn't be needed)
                    .map((control) =>
                        control > lineToDelete ? control - 1 : control
                    ),
            }));

            return {
                ...prev,
                width: prev.width - 1,
                gates: adjustedGates,
            };
        });
    }, [circuit.width]);

    return (
        <DndProvider backend={HTML5Backend}>
            <div className="h-full w-full flex bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-hidden">
                {/* Left Sidebar - Gate Toolbox */}
                <div className="w-96 border-r border-slate-700/50 bg-slate-800/60 backdrop-blur-sm overflow-y-auto">
                    <div className="p-6">
                        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">
                                    ⚡
                                </span>
                            </div>
                            Gate Toolbox
                        </h2>
                        <p className="text-slate-400 text-sm mb-6">
                            Select gates and build your quantum circuit
                        </p>
                        <GateToolbox
                            selectedTool={selectedTool}
                            onToolSelect={setSelectedTool}
                            onAddLine={handleAddLine}
                            onDeleteLine={handleDeleteLine}
                            onAddStep={handleAddStep}
                            onRandomGenerate={handleRandomGenerate}
                            isGenerating={isGenerating}
                            circuitLength={circuit.length}
                            circuitWidth={circuit.width}
                        />
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                    {/* Header */}
                    <div className="bg-slate-800/50 border-b border-slate-700/50 p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold text-white flex items-center gap-4">
                                    Circuit Designer
                                    <div className="flex items-center gap-2 text-base">
                                        <span className="bg-slate-700/60 px-3 py-1.5 rounded-lg border border-slate-600/50 text-slate-300">
                                            Gates: {circuit.gates.length}
                                        </span>
                                        <span className="bg-slate-700/60 px-3 py-1.5 rounded-lg border border-slate-600/50 text-slate-300">
                                            Depth:{" "}
                                            {Math.max(
                                                ...circuit.gates.map(
                                                    (g) => g.step
                                                ),
                                                -1
                                            ) + 1}
                                        </span>
                                    </div>
                                </h1>
                            </div>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={handleCompressCircuit}
                                    disabled={circuit.gates.length === 0}
                                    className="px-6 py-3 bg-orange-600/80 hover:bg-orange-500/80 disabled:bg-orange-600/40 disabled:cursor-not-allowed text-white rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-orange-500/25 backdrop-blur-sm border border-orange-500/30"
                                >
                                    🗜️ Compress
                                </button>
                                <button
                                    onClick={handleClear}
                                    className="px-6 py-3 bg-red-600/80 hover:bg-red-500/80 text-white rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-red-500/25 backdrop-blur-sm border border-red-500/30"
                                >
                                    🗑️ Clear
                                </button>
                                <div className="flex items-center gap-2 bg-slate-700/60 px-4 py-2 rounded-xl border border-slate-600/50">
                                    <span className="text-slate-300 text-sm font-medium">
                                        Zoom:
                                    </span>
                                    <button
                                        onClick={() =>
                                            setZoom(Math.max(0.25, zoom - 0.25))
                                        }
                                        className="px-2 py-1 bg-slate-600 hover:bg-slate-500 rounded text-white text-sm"
                                    >
                                        −
                                    </button>
                                    <span className="text-white font-mono text-sm min-w-12 text-center">
                                        {Math.round(zoom * 100)}%
                                    </span>
                                    <button
                                        onClick={() =>
                                            setZoom(Math.min(2, zoom + 0.25))
                                        }
                                        className="px-2 py-1 bg-slate-600 hover:bg-slate-500 rounded text-white text-sm"
                                    >
                                        +
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Circuit Canvas */}
                    <div className="flex-1 bg-gradient-to-br from-slate-900/95 to-slate-800/95 min-w-0 overflow-hidden">
                        <CircuitCanvas
                            circuit={circuit}
                            onGateDrop={handleGateDrop}
                            onGateMove={handleGateMove}
                            onGateRemove={handleGateRemove}
                            onControlEdit={handleControlEdit}
                            selectedTool={selectedTool}
                            zoom={zoom}
                        />
                    </div>
                </div>

                {/* Right Sidebar - Live Metrics */}
                <div className="w-96 border-l border-slate-700/50 bg-slate-800/60 backdrop-blur-sm overflow-y-auto">
                    <div className="p-6">
                        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">
                                    📊
                                </span>
                            </div>
                            Live Metrics
                        </h2>
                        <MetricsPanel circuit={circuit} metrics={metrics} />
                    </div>
                </div>
            </div>
        </DndProvider>
    );
}

function calculateCircuitPermutation(circuit: PlaygroundCircuit): number[] {
    const width = circuit.width;
    const numStates = 1 << width;

    let permutation = Array.from({ length: numStates }, (_, i) => i);

    // Sort gates by step
    const sortedGates = [...circuit.gates].sort((a, b) => a.step - b.step);

    for (const gate of sortedGates) {
        const newPermutation = [...permutation];

        for (let state = 0; state < numStates; state++) {
            let newState = permutation[state];

            switch (gate.type) {
                case "X":
                    newState ^= 1 << gate.target;
                    break;
                case "CX":
                    if (newState & (1 << gate.controls[0])) {
                        newState ^= 1 << gate.target;
                    }
                    break;
                case "CCX":
                    if (gate.controls.every((c) => newState & (1 << c))) {
                        newState ^= 1 << gate.target;
                    }
                    break;
            }

            newPermutation[state] = newState;
        }

        permutation = newPermutation;
    }

    return permutation;
}
