"use client";

import React from 'react';
import { Users } from 'lucide-react';

export function AdvisorAvatar({ role, status, size = "md" }: { role: string, status?: string, size?: "sm" | "md" | "lg" }) {
    const getHueRotate = (r: string) => {
        const lower = r ? r.toLowerCase() : "";
        if (lower.includes("defense") || lower.includes("defence")) return "brightness-75 sepia hue-rotate-[-50deg] saturate-200"; 
        if (lower.includes("foreign")) return "brightness-90 sepia hue-rotate-[180deg] saturate-200"; 
        if (lower.includes("intel")) return "brightness-75 sepia hue-rotate-[220deg] saturate-150"; 
        if (lower.includes("treasury")) return "brightness-90 sepia hue-rotate-[60deg] saturate-150"; 
        if (lower.includes("home")) return "brightness-90 sepia hue-rotate-[0deg] saturate-100"; 
        return "grayscale brightness-75";
    };

    const isOnline = status === 'online';
    
    const sizeClasses = {
        sm: "h-10 w-10",
        md: "h-14 w-14",
        lg: "h-20 w-20"
    };

    return (
         <div className={`relative ${sizeClasses[size]} border-4 border-slate-700 bg-black overflow-hidden rounded-none shrink-0 shadow-[0_0_15px_rgba(0,0,0,0.8)]`}>
            <img 
                src="/avatars/anchor/anchor_neutral_01.png" 
                alt={role}
                className={`h-full w-full object-cover object-top ${getHueRotate(role)}`}
                style={{ imageRendering: 'pixelated' }}
            />
            {status && (
                <div className={`absolute bottom-1 right-1 h-3 w-3 rounded-none border-2 border-black ${isOnline ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-red-600'}`} />
            )}
         </div>
    );
}

