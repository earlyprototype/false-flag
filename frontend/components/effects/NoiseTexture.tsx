"use client";

import React from 'react';

export function NoiseTexture() {
    return (
        <div className="pointer-events-none fixed inset-0 z-[40] opacity-[0.03] mix-blend-overlay pointer-events-none">
            <svg width="100%" height="100%">
                <filter id="noiseFilter">
                    <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" />
                </filter>
                <rect width="100%" height="100%" filter="url(#noiseFilter)" />
            </svg>
        </div>
    );
}


