"use client";

import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Users, Flag, Activity, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

// Interfaces matching API
export interface VibeData {
    vibes: string[];
    dominant: string;
    intensity: number;
}

export interface AdvisorData {
    role: string;
    name: string;
    trust: number;
    relationship: string;
    status: string;
    notes?: string;
}

export interface FlagData {
    key: string;
    label: string;
    severity: string;
    turn_activated?: number;
}

export interface StatusData {
    vibes: VibeData | null;
    advisors: AdvisorData[];
    active_flags: FlagData[];
    inactive_flags: FlagData[];
}

interface StatusPanelProps {
    isOpen: boolean;
    onClose: () => void;
    data: StatusData;
    loading: boolean;
}

// Simple Progress Bar Component
function ProgressBar({ value, className, colorClass = "bg-blue-500" }: { value: number, className?: string, colorClass?: string }) {
    return (
        <div className={`h-2 w-full bg-slate-800 rounded-full overflow-hidden ${className}`}>
            <div className={`h-full ${colorClass} transition-all duration-500`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
        </div>
    );
}

export function StatusPanel({ isOpen, onClose, data, loading }: StatusPanelProps) {
    const getTrustColor = (trust: number) => {
        if (trust >= 70) return "bg-emerald-500";
        if (trust >= 40) return "bg-amber-500";
        return "bg-red-500";
    };

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case 'critical': return "text-red-500 border-red-500";
            case 'elevated': return "text-amber-500 border-amber-500";
            default: return "text-blue-500 border-blue-500";
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[800px] max-h-[80vh] bg-slate-950 border-slate-800 text-slate-100 flex flex-col">
                <DialogHeader>
                    <DialogTitle className="text-xl font-mono flex items-center gap-2">
                        <Activity className="h-5 w-5 text-blue-400" />
                        SITUATION STATUS
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Current diagnostic assessment of strategic, political, and domestic indicators.
                    </DialogDescription>
                </DialogHeader>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <span className="animate-pulse text-slate-500 font-mono">Analyzing State...</span>
                    </div>
                ) : (
                    <Tabs defaultValue="vibes" className="flex-1 flex flex-col min-h-0">
                        <TabsList className="grid w-full grid-cols-3 bg-slate-900">
                            <TabsTrigger value="vibes" className="data-[state=active]:bg-slate-800">Vibes & Metrics</TabsTrigger>
                            <TabsTrigger value="advisors" className="data-[state=active]:bg-slate-800">Advisor Trust</TabsTrigger>
                            <TabsTrigger value="flags" className="data-[state=active]:bg-slate-800">World Flags</TabsTrigger>
                        </TabsList>

                        <div className="flex-1 min-h-0 mt-4">
                            <ScrollArea className="h-[50vh]">
                                <TabsContent value="vibes" className="space-y-4">
                                    {data.vibes && (
                                        <div className="space-y-6">
                                            <Card className="bg-slate-900/50 border-slate-800">
                                                <CardHeader>
                                                    <CardTitle className="text-sm uppercase text-slate-400">Dominant Atmosphere</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-3xl font-bold text-blue-100 mb-2">{data.vibes.dominant}</div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-slate-500">INTENSITY</span>
                                                        <ProgressBar value={data.vibes.intensity * 10} colorClass="bg-purple-500" className="flex-1" />
                                                        <span className="text-xs text-slate-300">{data.vibes.intensity}/10</span>
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            <div className="space-y-2">
                                                <h3 className="text-sm font-mono text-slate-400">INDICATORS</h3>
                                                {data.vibes.vibes.map((vibe, i) => (
                                                    <div key={i} className="p-3 bg-slate-900/30 border border-slate-800 rounded-md flex justify-between items-center">
                                                        <span className="font-mono text-sm">{vibe}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </TabsContent>

                                <TabsContent value="advisors" className="space-y-4">
                                    <div className="grid grid-cols-1 gap-4">
                                        {data.advisors.map((advisor) => (
                                            <div key={advisor.role} className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div>
                                                        <h4 className="font-bold text-slate-200">{advisor.role}</h4>
                                                        <div className="text-sm text-slate-400">{advisor.name}</div>
                                                    </div>
                                                    <Badge variant="outline" className={
                                                        advisor.relationship.toLowerCase().includes('allied') ? 'border-emerald-500 text-emerald-500' :
                                                        advisor.relationship.toLowerCase().includes('neutral') ? 'border-amber-500 text-amber-500' :
                                                        'border-red-500 text-red-500'
                                                    }>
                                                        {advisor.relationship.toUpperCase()}
                                                    </Badge>
                                                </div>
                                                
                                                <div className="space-y-1 mt-3">
                                                    <div className="flex justify-between text-xs">
                                                        <span className="text-slate-500">TRUST</span>
                                                        <span className="text-slate-300">{advisor.trust}/100</span>
                                                    </div>
                                                    <ProgressBar value={advisor.trust} colorClass={getTrustColor(advisor.trust)} />
                                                </div>

                                                {advisor.notes && (
                                                    <div className="mt-3 text-xs text-slate-500 italic">
                                                        "{advisor.notes}"
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </TabsContent>

                                <TabsContent value="flags" className="space-y-6">
                                    <div>
                                        <h3 className="text-sm font-mono text-slate-400 mb-3 flex items-center gap-2">
                                            <AlertTriangle className="h-4 w-4" />
                                            ACTIVE CRISIS INDICATORS
                                        </h3>
                                        <div className="space-y-2">
                                            {data.active_flags.length > 0 ? data.active_flags.map((flag) => (
                                                <div key={flag.key} className="p-3 bg-red-950/20 border border-red-900/50 rounded-md flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <Flag className="h-4 w-4 text-red-500" />
                                                        <span className="font-medium text-red-200">{flag.label}</span>
                                                    </div>
                                                    {flag.turn_activated && (
                                                        <Badge variant="secondary" className="bg-slate-900 text-slate-400">
                                                            Turn {flag.turn_activated}
                                                        </Badge>
                                                    )}
                                                </div>
                                            )) : (
                                                <div className="text-sm text-slate-600 italic p-4 text-center">No active crisis flags.</div>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="text-sm font-mono text-slate-400 mb-3">INACTIVE THREATS</h3>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                            {data.inactive_flags.map((flag) => (
                                                <div key={flag.key} className="p-2 bg-slate-900/30 border border-slate-800 rounded text-sm text-slate-600 flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-slate-700" />
                                                    {flag.label}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </TabsContent>
                            </ScrollArea>
                        </div>
                    </Tabs>
                )}
            </DialogContent>
        </Dialog>
    );
}

