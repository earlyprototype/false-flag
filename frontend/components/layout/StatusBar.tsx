"use client";

import React from 'react';
import { Terminal, AlertTriangle, Shield, Users, Activity } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { AdvisorAvatar } from "@/components/shared/AdvisorAvatar";

// Types
export interface GameMetrics {
  escalation_risk: number;
  domestic_stability: number;
  alliance_cohesion: number;
  casualties_mil: number;
  casualties_civ: number;
}

export interface Advisor {
    role: string;
    status: string;
}

interface StatusBarProps {
    sessionId: string | null;
    metrics: GameMetrics | null;
    advisors: Advisor[];
}

function MetricRow({ icon, label, value, color }: any) {
  return (
    <div className="flex items-center justify-between text-2xl font-vt323">
      <div className="flex items-center gap-3 text-slate-300">
        {icon}
        <span className="uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="h-4 w-32 bg-black border-2 border-slate-600 overflow-hidden">
            <div className={`h-full ${color.replace('text-', 'bg-')} transition-all duration-500`} style={{ width: `${value}%` }} />
        </div>
        <span className={`font-bold w-12 text-right ${color} text-glow`}>{value}</span>
      </div>
    </div>
  );
}

function AdvisorStatus({ role, status }: any) {
  const isOnline = status === 'online';
  return (
    <div className="flex items-center gap-4 p-3 hover:bg-slate-700/50 transition-colors border-b-2 border-slate-700/50 last:border-0">
      <AdvisorAvatar role={role} status={status} size="lg" />
      <div className="flex-1 min-w-0">
          <div className="text-xl font-vt323 text-cyan-300 truncate uppercase tracking-wider text-glow">{role}</div>
          <div className={`text-lg font-vt323 ${isOnline ? 'text-green-400 text-glow' : 'text-red-500'}`}>
             {isOnline ? '● SECURE LINK' : '○ OFFLINE'}
          </div>
      </div>
    </div>
  );
}

export function StatusBar({ sessionId, metrics, advisors }: StatusBarProps) {
    return (
      <div className="w-[350px] flex flex-col gap-4">
        
        {/* HEADER CARD */}
        <Card className="scumm-panel border-none bg-slate-800">
            <CardHeader className="pb-3 pt-4">
                <CardTitle className="text-5xl font-vt323 text-red-500 flex items-center gap-4 tracking-widest text-glow-strong">
                    <Terminal className="h-10 w-10" />
                    FALSE FLAG
                </CardTitle>
                <CardDescription className="font-vt323 text-xl text-cyan-500 mt-2">
                    TERMINAL: {sessionId?.slice(0,8) || "OFFLINE"}
                </CardDescription>
            </CardHeader>
        </Card>

        {/* METRICS CARD */}
        <Card className="flex-1 scumm-panel border-none bg-slate-800">
            <CardHeader className="pb-3 pt-4 border-b-4 border-black">
                <CardTitle className="text-2xl font-vt323 text-cyan-400 tracking-[0.3em] uppercase text-glow">Strategic Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
                {/* DEFCON Status */}
                <div className="bg-black border-4 border-slate-600 p-6 text-center relative shadow-inner">
                    <div className="text-lg text-cyan-600 mb-2 font-vt323 tracking-[0.3em]">DEFCON LEVEL</div>
                     {metrics ? (
                        <div className={`text-8xl font-vt323 tracking-tighter relative z-10 text-glow-strong ${metrics.escalation_risk > 75 ? 'text-red-500 animate-pulse' : metrics.escalation_risk > 50 ? 'text-orange-400' : 'text-yellow-400'}`}>
                            {metrics.escalation_risk > 75 ? '2' : metrics.escalation_risk > 50 ? '3' : '4'}
                        </div>
                    ) : (
                        <Skeleton className="h-20 w-full bg-slate-700" />
                    )}
                </div>

                {metrics && (
                    <div className="space-y-4">
                        <MetricRow icon={<AlertTriangle size={20} />} label="RISK" value={metrics.escalation_risk} color="text-red-400" />
                        <MetricRow icon={<Shield size={20} />} label="STABILITY" value={metrics.domestic_stability} color="text-cyan-400" />
                        <MetricRow icon={<Users size={20} />} label="COHESION" value={metrics.alliance_cohesion} color="text-green-400" />
                        <Separator className="bg-slate-600 h-[2px] my-3" />
                        <MetricRow icon={<Activity size={20} />} label="CASUALTIES" value={metrics.casualties_mil + metrics.casualties_civ} color="text-slate-300" />
                    </div>
                )}
            </CardContent>
        </Card>

        {/* ADVISORS CARD */}
        <Card className="h-[400px] scumm-panel border-none bg-slate-800 flex flex-col">
             <CardHeader className="pb-3 pt-4 shrink-0 border-b-4 border-black">
                <CardTitle className="text-2xl font-vt323 text-cyan-400 tracking-[0.3em] uppercase text-glow">Secure Channels</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto pr-2 pt-3">
                <div className="space-y-2">
                    {advisors.length > 0 ? (
                        advisors.map((adv, idx) => (
                            <AdvisorStatus key={idx} role={adv.role} status={adv.status} />
                        ))
                    ) : (
                        <div className="text-2xl text-cyan-700 text-center py-8 animate-pulse font-vt323">SEARCHING...</div>
                    )}
                </div>
            </CardContent>
        </Card>
      </div>
    );
}
