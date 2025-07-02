"use client";

import React, { useState } from "react";
import Header from "@/components/Header";
import CircuitPlayground from "@/components/CircuitPlayground";

export default function PlaygroundPage() {
    return (
        <div className="min-h-screen bg-circuit-gradient overflow-hidden">
            <div className="p-5 w-full max-w-none h-screen box-border">
                {/* Header */}
                <Header />

                {/* Playground Content */}
                <div className="mt-5 h-[calc(100vh-140px)] overflow-hidden">
                    <CircuitPlayground />
                </div>
            </div>
        </div>
    );
}
