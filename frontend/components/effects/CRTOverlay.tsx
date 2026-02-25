"use client";

import React from 'react';

export function CRTOverlay() {
    return (
        <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden h-full w-full select-none">
            {/* Scanlines - High Contrast */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_4px,6px_100%] opacity-60" />
            
            {/* Vignette */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_50%,rgba(0,0,0,0.6)_100%)] z-20" />

            {/* Dithering / Noise */}
            <div className="absolute inset-0 z-[15] opacity-[0.05] mix-blend-overlay">
                <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                    <filter id="noise">
                        <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch"/>
                    </filter>
                    <rect width="100%" height="100%" filter="url(#noise)"/>
                </svg>
            </div>
        </div>
    );
}
