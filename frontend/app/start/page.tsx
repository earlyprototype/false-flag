"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Play, Save, Terminal, Clock } from 'lucide-react';

const API_URL = "http://localhost:8000";

export default function StartScreen() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [saves, setSaves] = useState<any[]>([]);
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [selectedScenario, setSelectedScenario] = useState<any>(null);
    
    useEffect(() => {
        // Fetch Saves
        fetch(`${API_URL}/game/saves`)
            .then(r => r.json())
            .then(data => setSaves(data.saves))
            .catch(e => console.error("Failed to load saves", e));

        // Fetch Scenarios
        fetch(`${API_URL}/scenarios`)
            .then(r => r.json())
            .then(data => {
                setScenarios(data.scenarios);
                if (data.scenarios.length > 0) {
                    setSelectedScenario(data.scenarios[0]);
                }
            })
            .catch(e => console.error("Failed to load scenarios", e));
    }, []);

    const handleNewGame = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/game/new`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    scenario_id: selectedScenario?.id || "war_game_2025"
                })
            });
            const data = await res.json();
            localStorage.setItem("currentSessionId", data.session_id);
            router.push("/");
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleLoadGame = async (savePath: string) => {
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/game/load`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ save_path: savePath })
            });
            const data = await res.json();
            localStorage.setItem("currentSessionId", data.session_id);
            router.push("/");
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-4 font-mono">
            <Card className="w-full max-w-2xl bg-slate-900 border-slate-800 shadow-2xl">
                <CardHeader className="border-b border-slate-800 text-center pb-8 pt-8">
                    <div className="flex justify-center mb-4">
                        <Terminal className="h-12 w-12 text-blue-500" />
                    </div>
                    <CardTitle className="text-3xl font-bold tracking-widest text-white">FALSE FLAG</CardTitle>
                    <CardDescription className="text-slate-400">Crisis Simulation System v1.0</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                    <Tabs defaultValue="new" className="w-full">
                        <TabsList className="grid w-full grid-cols-2 bg-slate-950 mb-6">
                            <TabsTrigger value="new">NEW SIMULATION</TabsTrigger>
                            <TabsTrigger value="load">LOAD SCENARIO</TabsTrigger>
                        </TabsList>
                        
                        <TabsContent value="new" className="space-y-4">
                            <ScrollArea className="h-[300px] rounded border border-slate-800 bg-slate-950/50 p-2">
                                {scenarios.map((scenario) => (
                                    <button
                                        key={scenario.id}
                                        onClick={() => setSelectedScenario(scenario)}
                                        className={`w-full text-left p-3 rounded mb-2 transition-colors border ${
                                            selectedScenario?.id === scenario.id 
                                            ? "bg-blue-900/30 border-blue-800 text-blue-100" 
                                            : "bg-transparent border-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                                        }`}
                                    >
                                        <div className="font-bold">{scenario.name}</div>
                                        <div className="text-xs opacity-60">{scenario.description}</div>
                                    </button>
                                ))}
                            </ScrollArea>

                            {selectedScenario && (
                                <div className="p-4 border border-slate-800 rounded bg-slate-950/50 text-sm text-slate-400">
                                    <span className="font-bold text-white">Selected: {selectedScenario.name}</span>
                                    <p className="mt-2">{selectedScenario.description}</p>
                                    <div className="flex gap-2 mt-3 flex-wrap">
                                        {selectedScenario.variants && selectedScenario.variants.map((v: string) => (
                                            <span key={v} className="bg-slate-800 px-2 py-1 rounded text-xs uppercase">{v}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <Button className="w-full h-12 text-lg font-bold bg-blue-600 hover:bg-blue-500" onClick={handleNewGame} disabled={loading || !selectedScenario}>
                                {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Play className="mr-2 h-5 w-5" />}
                                INITIATE PROTOCOL
                            </Button>
                        </TabsContent>
                        
                        <TabsContent value="load">
                            <ScrollArea className="h-[450px] rounded border border-slate-800 bg-slate-950/50 p-2">
                                {saves.length > 0 ? (
                                    <div className="space-y-2">
                                        {saves.map((save) => (
                                            <button
                                                key={save.path}
                                                onClick={() => handleLoadGame(save.path)}
                                                disabled={loading}
                                                className="w-full text-left p-3 rounded hover:bg-slate-800 transition-colors border border-transparent hover:border-slate-700 group"
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div className="font-bold text-slate-300 group-hover:text-white">{save.name}</div>
                                                    <div className="text-xs text-slate-500 flex items-center">
                                                        <Clock className="h-3 w-3 mr-1" />
                                                        {new Date(save.timestamp).toLocaleString()}
                                                    </div>
                                                </div>
                                                <div className="text-xs text-slate-500 mt-1">
                                                    Turn {save.turn} • {save.scenario}
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                        <Save className="h-8 w-8 mb-2 opacity-20" />
                                        <p>No archives found.</p>
                                    </div>
                                )}
                            </ScrollArea>
                        </TabsContent>
                    </Tabs>
                </CardContent>
                <CardFooter className="border-t border-slate-800 bg-slate-950/30 justify-center py-4">
                    <p className="text-xs text-slate-600 font-mono">SECURE TERMINAL // TOP SECRET EYES ONLY</p>
                </CardFooter>
            </Card>
        </main>
    );
}
