"use client";

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Settings, Zap, Sparkles, Monitor, Moon, Sun } from 'lucide-react';

interface SettingsPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

// Theme definitions
const THEMES = [
    { id: 'defcon', name: 'DEFCON', desc: 'Cold War Blues', class: 'theme-defcon' },
    { id: 'standard', name: 'Standard', desc: 'Modern Interface', class: 'theme-standard' },
    { id: 'retro', name: 'Retro', desc: 'Phosphor Green', class: 'theme-retro' },
    { id: 'slate', name: 'Slate', desc: 'High Contrast', class: 'theme-slate' },
];

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
    const [llmMode, setLlmMode] = useState<'flash' | 'pro'>('pro');
    const [currentTheme, setCurrentTheme] = useState('defcon');
    const [loading, setLoading] = useState(false);

    // Load initial state
    useEffect(() => {
        if (isOpen) {
            // Load LLM Config
            fetch('http://localhost:8000/settings/llm')
                .then(r => r.json())
                .then(data => {
                    // Heuristic to determine mode from context summary
                    const summary = data.contexts || {};
                    const allFlash = Object.values(summary).every(m => (m as string).includes('flash'));
                    setLlmMode(allFlash ? 'flash' : 'pro');
                })
                .catch(console.error);
                
            // Load Theme (from localStorage or html class)
            const savedTheme = localStorage.getItem('theme') || 'defcon';
            setCurrentTheme(savedTheme);
        }
    }, [isOpen]);

    const handleLlmChange = async (mode: 'flash' | 'pro') => {
        setLoading(true);
        try {
            await fetch('http://localhost:8000/settings/llm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contexts: { mode } })
            });
            setLlmMode(mode);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleThemeChange = (themeId: string) => {
        setCurrentTheme(themeId);
        localStorage.setItem('theme', themeId);
        
        // Apply theme class to document root
        document.documentElement.className = `theme-${themeId}`; 
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[600px] bg-slate-950 border-slate-800 text-slate-100">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 font-mono">
                        <Settings className="h-5 w-5" /> SYSTEM CONFIGURATION
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Adjust simulation parameters and interface options.
                    </DialogDescription>
                </DialogHeader>

                <Tabs defaultValue="gameplay" className="w-full mt-4">
                    <TabsList className="grid w-full grid-cols-2 bg-slate-900">
                        <TabsTrigger value="gameplay">INTELLIGENCE</TabsTrigger>
                        <TabsTrigger value="display">DISPLAY</TabsTrigger>
                    </TabsList>

                    <TabsContent value="gameplay" className="space-y-6 py-4">
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-900/50">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 font-bold text-blue-400">
                                        <Zap className="h-4 w-4" /> PERFORMANCE MODE
                                    </div>
                                    <p className="text-xs text-slate-400 max-w-[250px]">
                                        Use "Flash" models for faster responses and lower latency. 
                                        Recommended for quick gameplay.
                                    </p>
                                </div>
                                <Button 
                                    variant={llmMode === 'flash' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => handleLlmChange('flash')}
                                    disabled={loading}
                                    className={llmMode === 'flash' ? 'bg-blue-600 hover:bg-blue-500' : ''}
                                >
                                    ACTIVATE
                                </Button>
                            </div>

                            <div className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-900/50">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 font-bold text-purple-400">
                                        <Sparkles className="h-4 w-4" /> QUALITY MODE
                                    </div>
                                    <p className="text-xs text-slate-400 max-w-[250px]">
                                        Use "Pro" models for maximum narrative depth and strategic nuance. 
                                        Higher latency.
                                    </p>
                                </div>
                                <Button 
                                    variant={llmMode === 'pro' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => handleLlmChange('pro')}
                                    disabled={loading}
                                    className={llmMode === 'pro' ? 'bg-purple-600 hover:bg-purple-500' : ''}
                                >
                                    ACTIVATE
                                </Button>
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="display" className="space-y-6 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            {THEMES.map((theme) => (
                                <button
                                    key={theme.id}
                                    onClick={() => handleThemeChange(theme.id)}
                                    className={`p-4 rounded-lg border text-left transition-all ${
                                        currentTheme === theme.id 
                                        ? "border-blue-500 bg-blue-900/20 ring-1 ring-blue-500" 
                                        : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
                                    }`}
                                >
                                    <div className="font-bold text-sm mb-1">{theme.name}</div>
                                    <div className="text-xs text-slate-500">{theme.desc}</div>
                                    
                                    {/* Preview Swatch */}
                                    <div className={`mt-3 h-2 w-full rounded-full opacity-50 ${
                                        theme.id === 'retro' ? 'bg-green-500' :
                                        theme.id === 'slate' ? 'bg-white' :
                                        theme.id === 'defcon' ? 'bg-amber-500' :
                                        'bg-blue-500'
                                    }`} />
                                </button>
                            ))}
                        </div>
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}

