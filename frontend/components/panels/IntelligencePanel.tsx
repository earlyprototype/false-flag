"use client";

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Globe, Lock, ShieldAlert, ShieldCheck, Search, Loader2 } from 'lucide-react';

export interface IntelActor {
    code: string;
    name: string;
    category: string;
}

export interface IntelDetail {
    actor: string;
    code: string;
    assessment: { raw: string[] }; // Backend returns list of strings as "raw"
    confidence: string;
    last_updated: number;
}

interface IntelligencePanelProps {
    isOpen: boolean;
    onClose: () => void;
    actors: IntelActor[];
    onSelectActor: (code: string) => Promise<void>;
    selectedActorData: IntelDetail | null;
    loadingDetail: boolean;
}

export function IntelligencePanel({ isOpen, onClose, actors, onSelectActor, selectedActorData, loadingDetail }: IntelligencePanelProps) {
    const [selectedCode, setSelectedCode] = useState<string | null>(null);

    const handleSelect = (code: string) => {
        setSelectedCode(code);
        onSelectActor(code);
    };

    const getCategoryColor = (cat: string) => {
        switch (cat.toLowerCase()) {
            case 'adversary': return "text-red-400 border-red-900/50 bg-red-950/20";
            case 'ally': return "text-emerald-400 border-emerald-900/50 bg-emerald-950/20";
            default: return "text-blue-400 border-blue-900/50 bg-blue-950/20";
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[900px] h-[80vh] bg-slate-950 border-slate-800 text-slate-100 flex flex-col p-0 gap-0 overflow-hidden">
                <div className="p-6 border-b border-slate-800 bg-slate-900/50">
                    <DialogTitle className="text-xl font-mono flex items-center gap-2">
                        <Globe className="h-5 w-5 text-blue-400" />
                        INTELLIGENCE DOSSIERS
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Classified assessments of state actors and strategic threats.
                    </DialogDescription>
                </div>

                <div className="flex-1 flex min-h-0">
                    {/* Sidebar: Actor List */}
                    <div className="w-1/3 border-r border-slate-800 bg-slate-900/20 flex flex-col">
                        <div className="p-4 border-b border-slate-800">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Available Targets</h3>
                        </div>
                        <ScrollArea className="flex-1">
                            <div className="p-2 space-y-1">
                                {actors.map((actor) => (
                                    <button
                                        key={actor.code}
                                        onClick={() => handleSelect(actor.code)}
                                        className={`w-full text-left p-3 rounded-md transition-colors flex justify-between items-center group ${
                                            selectedCode === actor.code 
                                            ? "bg-blue-900/30 border border-blue-800 text-blue-100" 
                                            : "hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
                                        }`}
                                    >
                                        <div className="flex flex-col">
                                            <span className="font-medium">{actor.name}</span>
                                            <span className="text-[10px] opacity-60">{actor.code}</span>
                                        </div>
                                        <Badge variant="outline" className={`text-[10px] ${getCategoryColor(actor.category)}`}>
                                            {actor.category.toUpperCase()}
                                        </Badge>
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>
                    </div>

                    {/* Main Content: Detail View */}
                    <div className="flex-1 flex flex-col bg-slate-950 relative">
                        {loadingDetail ? (
                            <div className="flex-1 flex items-center justify-center flex-col gap-3">
                                <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                                <span className="text-sm text-slate-500 font-mono">Decrypting dossier...</span>
                            </div>
                        ) : selectedActorData ? (
                            <ScrollArea className="flex-1">
                                <div className="p-8 max-w-3xl mx-auto">
                                    <div className="flex justify-between items-start mb-8">
                                        <div>
                                            <h2 className="text-2xl font-bold text-white mb-1">{selectedActorData.actor}</h2>
                                            <div className="flex gap-2 text-sm text-slate-400 font-mono">
                                                <span>CODE: {selectedActorData.code}</span>
                                                <span>•</span>
                                                <span>CONFIDENCE: {selectedActorData.confidence.toUpperCase()}</span>
                                                <span>•</span>
                                                <span>UPDATED: TURN {selectedActorData.last_updated}</span>
                                            </div>
                                        </div>
                                        <Lock className="h-6 w-6 text-red-500 opacity-50" />
                                    </div>

                                    <div className="space-y-4 font-mono text-sm leading-relaxed text-slate-300 bg-black/20 p-6 rounded-lg border border-slate-800">
                                        {/* Render raw lines for now, parsing can be improved later */}
                                        {selectedActorData.assessment.raw.map((line, i) => {
                                            // Simple formatting for bold headers in the text
                                            if (line.includes('[bold]')) {
                                                return <div key={i} className="font-bold text-blue-200 mt-4 mb-2 border-b border-blue-900/30 pb-1" dangerouslySetInnerHTML={{ __html: line.replace(/\[bold\](.*?)\[\/bold\]/g, '$1').replace(/\[.*?\]/g, '') }} />
                                            }
                                            if (line.trim() === "") return <br key={i} />;
                                            // Handle bullet points
                                            if (line.trim().startsWith('•')) {
                                                return <div key={i} className="pl-4 text-slate-300" dangerouslySetInnerHTML={{ __html: line.replace(/\[.*?\]/g, '') }} />
                                            }
                                            return <div key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\[.*?\]/g, '') }} />;
                                        })}
                                    </div>
                                </div>
                            </ScrollArea>
                        ) : (
                            <div className="flex-1 flex items-center justify-center text-slate-600 flex-col gap-4">
                                <Search className="h-12 w-12 opacity-20" />
                                <p>Select an actor to view intelligence assessment.</p>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

