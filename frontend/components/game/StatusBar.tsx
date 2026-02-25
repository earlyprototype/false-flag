"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, Shield, Users, Activity, Terminal } from 'lucide-react';

interface StatusBarProps {
    sessionId: string | null;
    metrics: {
        escalation_risk: number;
        domestic_stability: number;
        alliance_cohesion: number;
        casualties_mil: number;
        casualties_civ: number;
    } | null;
    advisors: {
        role: string;
        status: string;
    }[];
}

export function StatusBar({ sessionId, metrics, advisors }: StatusBarProps) {
    return (
        <div className="w-1/3 max-w-sm flex flex-col gap-4 h-full">
            {/* HEADER CARD */}
            <Card className="border-red-900/50 bg-black/40 shrink-0">
                <CardHeader className="pb-2">
                    <CardTitle className="text-2xl font-black tracking-tighter text-red-600 flex items-center gap-2">
                        <Terminal className="h-6 w-6" />
                        FALSE FLAG
                    </CardTitle>
                    <CardDescription className="font-mono text-xs">
                        SITUATION ROOM TERMINAL <br/>
                        ID: {sessionId?.slice(0,8) || "OFFLINE"}
                    </CardDescription>
                </CardHeader>
            </Card>

            {/* METRICS CARD */}
            <Card className="flex-1 border-slate-800 bg-slate-950/50 min-h-0 overflow-hidden flex flex-col">
                <CardHeader className="pb-2 shrink-0">
                    <CardTitle className="text-sm font-bold text-muted-foreground tracking-widest uppercase">Strategic Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6 overflow-y-auto">
                    {/* DEFCON Status */}
                    <div className="bg-black/50 p-4 rounded border border-slate-800 text-center shrink-0">
                        <div className="text-xs text-muted-foreground mb-2">ESCALATION STATUS</div>
                         {metrics ? (
                            <div className={`text-5xl font-black tracking-tighter ${metrics.escalation_risk > 75 ? 'text-red-600 animate-pulse' : metrics.escalation_risk > 50 ? 'text-orange-500' : 'text-yellow-500'}`}>
                                {metrics.escalation_risk > 75 ? 'DEFCON 2' : metrics.escalation_risk > 50 ? 'DEFCON 3' : 'DEFCON 4'}
                            </div>
                        ) : (
                            <Skeleton className="h-12 w-full bg-slate-800" />
                        )}
                    </div>

                    {metrics && (
                        <div className="space-y-4">
                            <MetricRow icon={<AlertTriangle size={16} />} label="Risk" value={metrics.escalation_risk} color="text-red-500" />
                            <MetricRow icon={<Shield size={16} />} label="Stability" value={metrics.domestic_stability} color="text-blue-400" />
                            <MetricRow icon={<Users size={16} />} label="Cohesion" value={metrics.alliance_cohesion} color="text-green-400" />
                            <Separator className="bg-slate-800" />
                            <MetricRow icon={<Activity size={16} />} label="Casualties" value={metrics.casualties_mil + metrics.casualties_civ} color="text-slate-400" />
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* ADVISORS CARD */}
            <Card className="h-1/3 border-slate-800 bg-slate-950/50 min-h-0 flex flex-col shrink-0">
                 <CardHeader className="pb-2 shrink-0">
                    <CardTitle className="text-sm font-bold text-muted-foreground tracking-widest uppercase">Secure Channels</CardTitle>
                </CardHeader>
                <CardContent className="overflow-y-auto">
                    <div className="space-y-2">
                        {advisors.length > 0 ? (
                            advisors.map((adv, idx) => (
                                <AdvisorStatus key={idx} role={adv.role} status={adv.status} />
                            ))
                        ) : (
                            <div className="text-xs text-muted-foreground text-center py-4">Connecting secure channels...</div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function MetricRow({ icon, label, value, color }: any) {
  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="h-2 w-24 bg-slate-800 rounded-full overflow-hidden">
            <div className={`h-full ${color.replace('text-', 'bg-')}`} style={{ width: `${value}%` }} />
        </div>
        <span className={`font-bold w-8 text-right ${color}`}>{value}</span>
      </div>
    </div>
  );
}

function AdvisorStatus({ role, status }: any) {
  const isOnline = status === 'active' || status === 'online'; // Adjusted status check
  return (
    <div className="flex items-center justify-between p-2 rounded hover:bg-slate-900/50 transition-colors">
      <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isOnline ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-slate-600'}`} />
          <span className="text-sm font-medium text-slate-300">{role}</span>
      </div>
      <span className="text-[10px] text-muted-foreground font-mono">
        {isOnline ? 'CONNECTED' : 'OFFLINE'}
      </span>
    </div>
  );
}

