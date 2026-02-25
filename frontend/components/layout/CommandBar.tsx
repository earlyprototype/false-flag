"use client";

import React from 'react';
import { Database, Activity, Shield, Globe, Users, Send, Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CardFooter } from "@/components/ui/card";

interface CommandBarProps {
    phase: string;
    loading: boolean;
    initialized: boolean;
    input: string;
    setInput: (s: string) => void;
    onSend: () => void;
    
    // Actions triggers
    onOpenResources: () => void;
    onOpenStatus: () => void;
    onOpenIntel: () => void;
    onOpenDiplomacy: () => void;
    onAdvise: () => void;
}

export function CommandBar({ 
    phase, 
    loading, 
    initialized, 
    input, 
    setInput, 
    onSend,
    onOpenResources,
    onOpenStatus,
    onOpenIntel,
    onOpenDiplomacy,
    onAdvise
}: CommandBarProps) {
    
    return (
        <>
            {/* ACTION BUTTONS ROW */}
            <div className="px-6 pt-4 pb-2 bg-slate-900/80 border-t-4 border-black flex gap-3 shrink-0 overflow-x-auto">
                <Button variant="ghost" size="lg" className="scumm-btn text-cyan-400 hover:text-cyan-300" onClick={onOpenResources}>
                    <Database className="mr-2 h-5 w-5" /> RESOURCES
                </Button>

                <Button variant="ghost" size="lg" className="scumm-btn text-red-400 hover:text-red-300" onClick={onOpenStatus}>
                    <Activity className="mr-2 h-5 w-5" /> STATUS
                </Button>

                <Button variant="ghost" size="lg" className="scumm-btn text-purple-400 hover:text-purple-300" onClick={onOpenIntel}>
                    <Shield className="mr-2 h-5 w-5" /> INTEL
                </Button>

                <Button variant="ghost" size="lg" className="scumm-btn text-green-400 hover:text-green-300" onClick={onOpenDiplomacy}>
                    <Globe className="mr-2 h-5 w-5" /> DIPLOMACY
                </Button>

                <Button variant="ghost" size="lg" className="scumm-btn text-yellow-400 hover:text-yellow-300" onClick={onAdvise} disabled={loading || phase !== "discussion"}>
                    <Users className="mr-2 h-5 w-5" /> ADVISE
                </Button>
            </div>

            {/* INPUT AREA */}
            <CardFooter className="p-6 pt-4 border-none bg-transparent shrink-0">
                <div className="flex w-full gap-4">
                    <Input 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && onSend()}
                        placeholder={phase === "discussion" ? "TYPE COMMAND..." : phase === "briefing" ? "TYPE 'READY'..." : "ENTER DECISION..."}
                        disabled={loading || !initialized}
                        className="scumm-input flex-1"
                        autoFocus
                    />
                    <Button 
                        onClick={onSend} 
                        disabled={loading || !initialized}
                        className={`scumm-btn h-auto w-40 ${phase === "decision" ? 'text-red-400 border-red-600 text-glow-strong animate-pulse' : 'text-green-400 border-green-700 text-glow'}`}
                    >
                        {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : (
                            <>
                                <span className="text-2xl">EXECUTE</span>
                                <Send className="ml-3 h-6 w-6" />
                            </>
                        )}
                    </Button>
                </div>
            </CardFooter>
        </>
    );
}
