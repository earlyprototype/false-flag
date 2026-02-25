"use client";

import React, { useRef, useEffect } from 'react';
import { Loader2, AlertTriangle, Users, Radio, Shield } from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { AdvisorAvatar } from "@/components/shared/AdvisorAvatar";

// Types
export interface TranscriptItem {
  type: 'system' | 'inject' | 'advisor' | 'player' | 'narrator' | 'error';
  content: string;
  role?: string;
  title?: string;
}

interface SceneViewportProps {
    turn: number;
    phase: string;
    loading: boolean;
    initialized: boolean;
    transcript: TranscriptItem[];
    children?: React.ReactNode;
}

function FeedItem({ item }: { item: TranscriptItem }) {
  if (item.type === 'system') {
    return (
      <div className="flex justify-center animate-in fade-in duration-300">
        <Badge variant="outline" className="bg-black text-cyan-400 border-cyan-700 border-2 font-vt323 text-2xl tracking-[0.2em] rounded-none px-6 py-2 text-glow">
          {item.content}
        </Badge>
      </div>
    );
  }

  if (item.type === 'inject') {
    return (
      <Alert className="scumm-panel border-l-[8px] border-l-yellow-500 bg-yellow-950/30 animate-in fade-in slide-in-from-bottom-4 duration-500 rounded-none">
        <AlertTriangle className="h-6 w-6 text-yellow-400" />
        <AlertTitle className="text-yellow-300 font-bold tracking-widest uppercase mb-3 text-2xl font-vt323 text-glow">
          {item.title || "INTELLIGENCE UPDATE"}
        </AlertTitle>
        <AlertDescription className="text-yellow-100 leading-relaxed whitespace-pre-wrap text-2xl font-vt323">
          {item.content}
        </AlertDescription>
      </Alert>
    );
  }

  if (item.type === 'advisor') {
    return (
      <div className="flex gap-4 max-w-5xl mr-auto animate-in fade-in slide-in-from-left-4 duration-300 w-full group">
        <div className="flex flex-col items-center gap-2">
            <AdvisorAvatar role={item.role || "Advisor"} size="lg" status="online" />
        </div>
        <Card className="scumm-panel max-w-[85%] relative overflow-visible group-hover:brightness-110 transition-all bg-slate-800">
             {/* Speech bubble triangle */}
             <div className="absolute top-6 -left-4 w-0 h-0 border-t-[12px] border-t-transparent border-r-[16px] border-r-slate-600 border-b-[12px] border-b-transparent" />
             
            <CardHeader className="p-4 pb-2 bg-slate-900/50 border-b-2 border-black">
                <CardTitle className="text-xl text-cyan-500 uppercase tracking-wide flex items-center justify-between font-vt323 text-glow">
                    {item.role}
                    <Radio className="h-4 w-4 text-green-500" />
                </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-3">
                <div className="text-green-200 whitespace-pre-wrap text-2xl leading-relaxed font-vt323">{item.content}</div>
            </CardContent>
        </Card>
      </div>
    );
  }

  if (item.type === 'player') {
    return (
      <div className="flex gap-4 max-w-5xl ml-auto justify-end animate-in fade-in slide-in-from-right-4 duration-300 w-full">
        <Card className="scumm-panel bg-blue-900/40 border-blue-600 max-w-[85%]">
            <CardHeader className="p-4 pb-2 bg-blue-950/50 border-b-2 border-blue-950">
                 <CardTitle className="text-xl text-blue-300 uppercase tracking-wide text-right font-vt323 text-glow">Prime Minister</CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-3">
                <div className="text-blue-100 font-bold whitespace-pre-wrap text-2xl text-right font-vt323">{item.content}</div>
            </CardContent>
        </Card>
        <div className="w-16 h-16 rounded-none bg-blue-900/50 flex items-center justify-center border-4 border-blue-700 shrink-0">
             <Shield className="h-8 w-8 text-blue-300" />
        </div>
      </div>
    );
  }
  
  if (item.type === 'narrator') {
      return (
          <div className="max-w-4xl mx-auto text-center text-cyan-500 my-6 text-2xl animate-in fade-in duration-1000 font-vt323 italic text-glow">
              {item.content}
          </div>
      )
  }
  
  if (item.type === 'error') {
      return (
          <Alert variant="destructive" className="scumm-panel bg-red-950/30 border-red-700 max-w-2xl mx-auto">
              <AlertTriangle className="h-6 w-6" />
              <AlertTitle className="font-vt323 text-2xl text-red-300">SYSTEM ERROR</AlertTitle>
              <AlertDescription className="font-vt323 text-xl text-red-200">{item.content}</AlertDescription>
          </Alert>
      )
  }

  return null;
}

export function SceneViewport({ turn, phase, loading, initialized, transcript, children }: SceneViewportProps) {
    const feedRef = useRef<HTMLDivElement>(null);

    // Auto-scroll
    useEffect(() => {
        if (feedRef.current) {
            feedRef.current.scrollTop = feedRef.current.scrollHeight;
        }
    }, [transcript]);

    const getPhaseColor = (p: string) => {
      if (p === 'briefing') return 'text-cyan-400 text-glow';
      if (p === 'discussion') return 'text-yellow-400 text-glow';
      if (p === 'decision') return 'text-red-500 text-glow-strong animate-pulse';
      return 'text-slate-500';
    };

    return (
      <Card className="flex-1 flex flex-col scumm-panel relative min-h-0 bg-slate-900">
        <CardHeader className="border-b-4 border-black py-4 bg-slate-800 shrink-0">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-8">
                    <Badge variant="outline" className="bg-black text-cyan-400 border-cyan-700 border-3 text-2xl font-vt323 rounded-none px-4 py-1 text-glow">TURN {turn}</Badge>
                    <div className="text-2xl font-vt323 uppercase tracking-wider">
                        PHASE: <span className={`font-bold ${getPhaseColor(phase)}`}>{phase}</span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {loading && <Loader2 className="animate-spin text-green-400" size={24} />}
                    <Badge variant={initialized ? "default" : "destructive"} className="text-lg font-vt323 rounded-none px-3 py-1 bg-green-900 text-green-300 border-2 border-green-600">
                        {initialized ? "● LIVE" : "○ OFFLINE"}
                    </Badge>
                </div>
            </div>
        </CardHeader>

        {/* SCROLLING TRANSCRIPT */}
        <div ref={feedRef} className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth bg-black/40">
            {transcript.length === 0 && initialized && (
                <div className="flex items-center justify-center h-full text-cyan-700 animate-pulse font-vt323 text-3xl uppercase tracking-widest">
                    Awaiting transmission...
                </div>
            )}
            
            {transcript.map((item, idx) => (
                <FeedItem key={idx} item={item} />
            ))}
            
            {loading && (
                <div className="flex justify-center py-6">
                    <span className="text-2xl text-green-400 animate-pulse flex items-center gap-3 font-vt323 uppercase tracking-wider text-glow">
                        <Loader2 className="h-6 w-6 animate-spin" /> Processing...
                    </span>
                </div>
            )}
        </div>
        
        {children}
      </Card>
    );
}
