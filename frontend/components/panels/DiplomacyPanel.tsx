"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Send, Phone, Globe } from 'lucide-react';
import { Badge } from "@/components/ui/badge";

export interface DiplomaticContact {
    country_code: string;
    title: string;
    access_level: string;
    disposition?: string;
    notes?: string;
}

export interface DiplomaticMessage {
    sender: string;
    text: string;
}

export interface ActiveCallState {
    country_code: string;
    title: string;
    transcript: string[]; // Raw strings from API
    active: boolean;
    outcome?: any;
}

interface DiplomacyPanelProps {
    isOpen: boolean;
    onClose: () => void;
    contacts: DiplomaticContact[];
    activeCall: ActiveCallState | null;
    onStartCall: (country_code: string) => void;
    onReply: (message: string) => void;
    loading: boolean;
}

export function DiplomacyPanel({ 
    isOpen, 
    onClose, 
    contacts, 
    activeCall, 
    onStartCall, 
    onReply, 
    loading 
}: DiplomacyPanelProps) {
    const [input, setInput] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);
    const viewportRef = useRef<HTMLDivElement>(null);

    // Parse raw transcript into messages
    const messages = activeCall?.transcript.map(line => {
        // Handle "Title: Message" format
        const parts = line.split(': ');
        if (parts.length >= 2 && !line.startsWith('===') && !line.includes('Outcome:')) {
            return { sender: parts[0], text: parts.slice(1).join(': ') };
        }
        // Handle System/Outcome lines
        return { sender: "System", text: line };
    }) || [];

    // Auto-scroll
    useEffect(() => {
        if (viewportRef.current) {
            viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
        }
    }, [messages, loading]);

    const handleSend = () => {
        if (!input.trim()) return;
        onReply(input);
        setInput("");
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[900px] h-[80vh] bg-slate-950 border-slate-800 text-slate-100 flex flex-col p-0 gap-0 overflow-hidden">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                    <div>
                        <DialogTitle className="text-lg font-mono flex items-center gap-2">
                            <Globe className="h-5 w-5 text-blue-400" />
                            DIPLOMATIC CHANNELS
                        </DialogTitle>
                        <DialogDescription className="text-slate-400 text-xs">
                            {activeCall ? `SECURE LINE: ${activeCall.title} (${activeCall.country_code})` : "Select a channel to establish connection."}
                        </DialogDescription>
                    </div>
                    {activeCall && (
                        <Badge variant={activeCall.active ? "default" : "destructive"} className="font-mono">
                            {activeCall.active ? "CONNECTED" : "TERMINATED"}
                        </Badge>
                    )}
                </div>

                <div className="flex-1 flex min-h-0">
                    {/* Sidebar: Contacts */}
                    <div className={`w-1/3 max-w-[250px] border-r border-slate-800 bg-slate-900/20 flex flex-col ${activeCall ? 'hidden sm:flex' : 'flex'}`}>
                        <div className="p-3 border-b border-slate-800">
                            <h3 className="text-xs font-bold text-slate-500 uppercase">Available Lines</h3>
                        </div>
                        <ScrollArea className="flex-1">
                            <div className="p-2 space-y-1">
                                {contacts.map((contact) => (
                                    <button
                                        key={contact.country_code}
                                        onClick={() => !loading && onStartCall(contact.country_code)}
                                        disabled={loading || (activeCall?.active ?? false)}
                                        className={`w-full text-left p-3 rounded-md transition-colors flex justify-between items-center group ${
                                            activeCall?.country_code === contact.country_code
                                            ? "bg-blue-900/30 border border-blue-800 text-blue-100"
                                            : "hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
                                        }`}
                                    >
                                        <div className="min-w-0">
                                            <div className="font-bold text-sm truncate">{contact.country_code}</div>
                                            <div className="text-xs opacity-60 truncate">{contact.title}</div>
                                        </div>
                                        <Phone className={`h-4 w-4 shrink-0 ml-2 ${activeCall?.active && activeCall.country_code === contact.country_code ? 'text-green-500 animate-pulse' : 'opacity-50 group-hover:opacity-100'}`} />
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>
                    </div>

                    {/* Main Content: Chat */}
                    <div className="flex-1 flex flex-col bg-slate-950 relative min-w-0">
                        {activeCall ? (
                            <>
                                <div className="flex-1 overflow-y-auto p-4" ref={viewportRef}>
                                    <div className="space-y-4">
                                        {messages.map((msg, i) => {
                                            const isMe = msg.sender === "Prime Minister";
                                            const isSystem = msg.sender === "System";
                                            
                                            if (isSystem) {
                                                // Don't render empty system lines
                                                if (!msg.text.trim()) return null;
                                                return (
                                                    <div key={i} className="flex justify-center my-4">
                                                        <span className="text-[10px] font-mono text-slate-500 bg-slate-900/50 px-2 py-1 rounded border border-slate-800/50 whitespace-pre-wrap text-center max-w-full">
                                                            {msg.text}
                                                        </span>
                                                    </div>
                                                );
                                            }

                                            return (
                                                <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                                                    <div className={`max-w-[85%] rounded-lg p-3 ${
                                                        isMe 
                                                        ? 'bg-blue-900/20 border border-blue-800/50 text-blue-100' 
                                                        : 'bg-slate-800/50 border border-slate-700 text-slate-200'
                                                    }`}>
                                                        <div className="text-[10px] font-bold opacity-50 mb-1 uppercase">{msg.sender}</div>
                                                        <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {loading && (
                                            <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2">
                                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 flex items-center gap-2">
                                                    <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                                                    <span className="text-xs text-slate-400 italic">Secure transmission active...</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex gap-2">
                                    <Input 
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                        placeholder={activeCall.active ? "Send message..." : "Connection terminated."}
                                        disabled={!activeCall.active || loading}
                                        className="bg-slate-950 border-slate-700 font-mono"
                                        autoFocus
                                    />
                                    <Button 
                                        onClick={handleSend} 
                                        disabled={!activeCall.active || loading}
                                        size="icon"
                                        className="bg-blue-600 hover:bg-blue-500"
                                    >
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-slate-600 gap-4">
                                <div className="h-20 w-20 rounded-full bg-slate-900 flex items-center justify-center">
                                    <Globe className="h-10 w-10 opacity-20" />
                                </div>
                                <p>Select a secure channel to begin.</p>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

