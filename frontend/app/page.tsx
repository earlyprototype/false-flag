"use client";

import React, { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';
import { Button } from "@/components/ui/button";

import { StatusBar, GameMetrics, Advisor } from "@/components/layout/StatusBar";
import { SceneViewport, TranscriptItem } from "@/components/layout/SceneViewport";
import { CommandBar } from "@/components/layout/CommandBar";
import { ResourcePanel, ResourceData } from "@/components/panels/ResourcePanel";
import { DecisionReviewDialog, InterpretationData } from "@/components/panels/DecisionReviewDialog";
import { StatusPanel, StatusData } from "@/components/panels/StatusPanel";
import { IntelligencePanel, IntelActor, IntelDetail } from "@/components/panels/IntelligencePanel";
import { DiplomacyPanel, ActiveCallState, DiplomaticContact as Contact } from "@/components/panels/DiplomacyPanel";
import { SettingsPanel } from "@/components/panels/SettingsPanel";

const API_URL = "http://localhost:8000";

export default function Dashboard() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<GameMetrics | null>(null);
  const [advisors, setAdvisors] = useState<Advisor[]>([]);
  const [turn, setTurn] = useState(1);
  const [phase, setPhase] = useState("LOADING");
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);
  
  // Resources & Diplomacy State
  const [isResourcesOpen, setIsResourcesOpen] = useState(false);
  const [resources, setResources] = useState<ResourceData | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  
  // Decision Review State
  const [interpretation, setInterpretation] = useState<InterpretationData | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [pendingDecisionText, setPendingDecisionText] = useState<string>("");
  
  // Phase 2 State
  const [isStatusOpen, setIsStatusOpen] = useState(false);
  const [statusData, setStatusData] = useState<StatusData>({ vibes: null, advisors: [], active_flags: [], inactive_flags: [] });
  const [statusLoading, setStatusLoading] = useState(false);

  const [isIntelOpen, setIsIntelOpen] = useState(false);
  const [intelActors, setIntelActors] = useState<IntelActor[]>([]);
  const [selectedIntelDetail, setSelectedIntelDetail] = useState<IntelDetail | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);

  const [isDiplomacyOpen, setIsDiplomacyOpen] = useState(false);
  const [activeDiplomacySession, setActiveDiplomacySession] = useState<ActiveCallState | null>(null);
  const [diplomacyLoading, setDiplomacyLoading] = useState(false);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Phase 2 Handlers
  const handleOpenStatus = async () => {
      setIsStatusOpen(true);
      setStatusLoading(true);
      try {
          if (!sessionId) return;
          const [vibesRes, advisorsRes, flagsRes] = await Promise.all([
              fetch(`${API_URL}/game/${sessionId}/state/vibes`),
              fetch(`${API_URL}/game/${sessionId}/state/advisors`),
              fetch(`${API_URL}/game/${sessionId}/state/flags`)
          ]);
          
          const vibes = await vibesRes.json();
          const advisors = await advisorsRes.json();
          const flags = await flagsRes.json();
          
          setStatusData({
              vibes: vibes,
              advisors: advisors.advisors,
              active_flags: flags.active_flags,
              inactive_flags: flags.inactive_flags
          });
      } catch (e) {
          console.error("Failed to fetch status data", e);
      } finally {
          setStatusLoading(false);
      }
  };

  const handleOpenIntel = async () => {
      setIsIntelOpen(true);
      try {
          if (!sessionId) return;
          const res = await fetch(`${API_URL}/game/${sessionId}/intel`);
          const data = await res.json();
          setIntelActors(data.available_actors);
      } catch (e) {
          console.error("Failed to fetch intel list", e);
      }
  };

  const handleSelectActor = async (code: string) => {
      setIntelLoading(true);
      try {
          if (!sessionId) return;
          const res = await fetch(`${API_URL}/game/${sessionId}/intel/${code}`);
          const data = await res.json();
          setSelectedIntelDetail(data);
      } catch (e) {
          console.error("Failed to fetch intel detail", e);
      } finally {
          setIntelLoading(false);
      }
  };

  const handleOpenDiplomacy = () => {
      setIsDiplomacyOpen(true);
      fetchContacts();
  };

  const handleStartCall = async (country_code: string) => {
      setDiplomacyLoading(true);
      try {
          if (!sessionId) return;
          const res = await fetch(`${API_URL}/game/action/call`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: sessionId, country_name: country_code })
          });
          const data = await res.json();
          setActiveDiplomacySession({
              country_code: country_code,
              title: data.title || "Unknown",
              transcript: data.transcript,
              active: data.active,
              outcome: data.outcome
          });
      } catch (e) {
          console.error("Start call failed", e);
      } finally {
          setDiplomacyLoading(false);
      }
  };

  const handleReplyCall = async (message: string) => {
      setDiplomacyLoading(true);
      try {
          if (!sessionId) return;
          const res = await fetch(`${API_URL}/game/action/diplomacy/reply`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: sessionId, message: message })
          });
          const data = await res.json();
          
          setActiveDiplomacySession(prev => prev ? {
              ...prev,
              transcript: data.transcript,
              active: data.active,
              outcome: data.outcome
          } : null);
      } catch (e) {
          console.error("Reply failed", e);
      } finally {
          setDiplomacyLoading(false);
      }
  };

  // 1. Initialize Game on Mount
  useEffect(() => {
    if (initialized) return;
    
    async function initGame() {
      try {
        let data;
        const storedSessionId = localStorage.getItem("currentSessionId");
        
        if (storedSessionId) {
            const res = await fetch(`${API_URL}/game/${storedSessionId}`);
            if (res.ok) {
                data = await res.json();
                // Resume
                setTranscript([
                    { type: 'system', content: 'SESSION RESTORED' },
                    { type: 'system', content: `TURN ${data.turn} | PHASE: ${data.phase.toUpperCase()}` },
                ]);
            } else {
                // Invalid/Expired
                console.log("Session expired, creating new.");
                localStorage.removeItem("currentSessionId");
            }
        }
        
        if (!data) {
        const res = await fetch(`${API_URL}/game/new`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_id: "war_game_2025" })
        });
        
        if (!res.ok) throw new Error("Failed to start game");
        
            data = await res.json();
            localStorage.setItem("currentSessionId", data.session_id);
            
            // Add initial welcome message
            setTranscript([
              { type: 'system', content: 'SECURE CHANNEL ESTABLISHED' },
              { type: 'system', content: `TURN ${data.turn} | PHASE: ${data.phase.toUpperCase()}` },
            ]);
        }
        
        setSessionId(data.session_id);
        setMetrics(data.metrics);
        setAdvisors(data.advisors || []);
        setTurn(data.turn);
        setPhase(data.phase); 
        
        setInitialized(true);
      } catch (err) {
        console.error(err);
        setTranscript([{ type: 'error', content: 'CONNECTION FAILED: Backend API unavailable.' }]);
      }
    }
    
    initGame();
  }, [initialized]);

  // 2. Connect to SSE Stream
  useEffect(() => {
    if (!sessionId) return;

    console.log("Connecting to stream...");
    const eventSource = new EventSource(`${API_URL}/stream/${sessionId}`);

    eventSource.onopen = () => {
      console.log("Stream connected");
    };

    eventSource.onerror = (err) => {
      console.error("Stream error", err);
      eventSource.close();
    };

    // Handle "transcript" events
    eventSource.addEventListener("transcript", (event) => {
      try {
        const data = JSON.parse(event.data);
        setTranscript(prev => [...prev, data]);
      } catch (e) {
        console.error("Failed to parse transcript event", e);
      }
    });

    // Handle "state_update" events
    eventSource.addEventListener("state_update", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.phase) setPhase(data.phase);
        if (data.turn) setTurn(data.turn);
        if (data.metrics) setMetrics(data.metrics);
      } catch (e) {
        console.error("Failed to parse state update", e);
      }
    });
    
    // Handle "system" events
    eventSource.addEventListener("system", (event) => {
        try {
            const data = JSON.parse(event.data);
            setTranscript(prev => [...prev, { type: 'system', content: data.content }]);
        } catch (e) {}
    });

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  // --- ACTIONS ---

  const fetchResources = async () => {
      if (!sessionId) return;
      const res = await fetch(`${API_URL}/game/${sessionId}/resources`);
      const data = await res.json();
      setResources(data);
  };

  const handleOpenResources = () => {
      setIsResourcesOpen(true);
      fetchResources();
  };

  const fetchContacts = async () => {
      if (!sessionId) return;
      const res = await fetch(`${API_URL}/game/${sessionId}/diplomacy/contacts`);
      const data = await res.json();
      setContacts(data);
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId || loading) return;
    
    const userAction = input;
    setInput('');
    setLoading(true);
    
    // Optimistic update
    setTranscript(prev => [...prev, { type: 'player', content: userAction }]);

    try {
      // --- BRANCH LOGIC BASED ON PHASE ---
      if (phase === "briefing") {
        if (userAction.toLowerCase().includes("ready") || userAction.toLowerCase().includes("ok")) {
           await fetch(`${API_URL}/game/${sessionId}/briefing/ack`, { method: "POST" });
        } else {
           setTranscript(prev => [...prev, { type: 'system', content: `Briefing Phase: Type 'ready' to enter discussion.` }]);
        }
      } 
      else if (phase === "discussion") {
        // Handle /advise command
        if (userAction.toLowerCase() === "/advise" || userAction.toLowerCase().startsWith("/advise")) {
            await fetch(`${API_URL}/game/discussion`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, question: "I need advice from all advisors on the current situation." })
            });
        }
        // Handle /decide command
        else if (userAction.toLowerCase().startsWith("/decide") || userAction.toLowerCase() === "decide") {
            const actionText = userAction.replace("/decide", "").trim();
            if (!actionText) {
                 setTranscript(prev => [...prev, { type: 'system', content: `Type '/decide [action]' to commit.` }]);
            } else {
                await executeDecision(actionText);
            }
        }
        // Regular discussion question
        else {
            await fetch(`${API_URL}/game/discussion`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, question: userAction })
            });
        }
      }
      else if (phase === "decision") {
        await executeDecision(userAction);
      }
      
    } catch (err) {
      console.error(err);
      setTranscript(prev => [...prev, { type: 'error', content: 'Command failed.' }]);
    } finally {
      setLoading(false);
    }
  };

  const executeDecision = async (actionText: string) => {
      setLoading(true);
      setPendingDecisionText(actionText);
      
      try {
          const res = await fetch(`${API_URL}/game/decision/interpret`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, action_text: actionText })
      });
          
          if (!res.ok) throw new Error("Failed to interpret decision");
          
          const data = await res.json();
          setInterpretation(data);
          setIsReviewOpen(true);
      } catch (err) {
          console.error(err);
          setTranscript(prev => [...prev, { type: 'error', content: 'Decision interpretation failed.' }]);
      } finally {
          setLoading(false);
      }
  }

  const handleCommitDecision = async (finalText: string, choice: string = "confirm") => {
      setLoading(true);
      setIsReviewOpen(false);
      
      try {
          await fetch(`${API_URL}/game/decision/commit`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ 
                  session_id: sessionId, 
                  action_text: finalText,
                  user_choice: choice
              })
          });
      } catch (err) {
          console.error(err);
          setTranscript(prev => [...prev, { type: 'error', content: 'Decision commit failed.' }]);
      } finally {
          setLoading(false);
          setInterpretation(null);
          setPendingDecisionText("");
      }
  }

  const handleApplyRecommendations = () => {
      if (!interpretation) return;
      
      // Construct modified text
      let modifiedText = pendingDecisionText;
      const recs = interpretation.critical_concerns.map(c => c.recommendation).join(" ");
      if (recs) {
          modifiedText += ` Also, ${recs}`;
      }
      
      handleCommitDecision(modifiedText, "apply_recommendations");
  };

  const handleModifyDecision = () => {
      setInput(pendingDecisionText); // Put text back in input
      setIsReviewOpen(false);
      setInterpretation(null);
  };

  const handleIgnoreAndProceed = () => {
      handleCommitDecision(pendingDecisionText, "override");
  };

  const handleReturnToDiscussion = () => {
      setIsReviewOpen(false);
      setInterpretation(null);
      setPhase("discussion");
      setTranscript(prev => [...prev, { type: 'system', content: "Returned to discussion phase." }]);
  };

  const handleAdvise = async () => {
      if (!sessionId || loading || phase !== "discussion") return;
      setLoading(true);
      setTranscript(prev => [...prev, { type: 'player', content: '/advise' }]);
      
      try {
          await fetch(`${API_URL}/game/discussion`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, question: "I need advice from all advisors on the current situation." })
          });
      } catch (err) {
          console.error(err);
          setTranscript(prev => [...prev, { type: 'error', content: 'ADVISE command failed.' }]);
      } finally {
          setLoading(false);
      }
  }

  return (
    <main className="flex h-screen bg-background text-foreground font-mono overflow-hidden p-4 gap-4 relative">
      {/* Settings Button */}
      <div className="absolute top-2 right-2 z-50">
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground" onClick={() => setIsSettingsOpen(true)}>
              <Settings className="h-5 w-5" />
          </Button>
      </div>
      
      {/* LEFT COLUMN: METRICS & ADVISORS */}
      <StatusBar 
          sessionId={sessionId} 
          metrics={metrics} 
          advisors={advisors} 
      />

      {/* CENTER COLUMN: MAIN FEED & COMMANDS */}
      <SceneViewport 
          turn={turn} 
          phase={phase} 
          loading={loading} 
          initialized={initialized} 
          transcript={transcript}
      >
          <CommandBar 
            phase={phase}
            loading={loading}
            initialized={initialized}
            input={input}
            setInput={setInput}
            onSend={handleSend}
            onOpenResources={handleOpenResources}
            onOpenStatus={handleOpenStatus}
            onOpenIntel={handleOpenIntel}
            onOpenDiplomacy={handleOpenDiplomacy}
            onAdvise={handleAdvise}
          />
      </SceneViewport>

      {/* HIDDEN/OVERLAY PANELS */}
      <ResourcePanel 
          isOpen={isResourcesOpen} 
          onClose={setIsResourcesOpen} 
          resources={resources} 
      />

      <StatusPanel 
          isOpen={isStatusOpen} 
          onClose={() => setIsStatusOpen(false)} 
          data={statusData}
          loading={statusLoading}
      />

      <IntelligencePanel 
          isOpen={isIntelOpen} 
          onClose={() => setIsIntelOpen(false)} 
          actors={intelActors}
          onSelectActor={handleSelectActor}
          selectedActorData={selectedIntelDetail}
          loadingDetail={intelLoading}
      />

      <DiplomacyPanel 
          isOpen={isDiplomacyOpen}
          onClose={() => setIsDiplomacyOpen(false)}
          contacts={contacts}
          activeCall={activeDiplomacySession}
          onStartCall={handleStartCall}
          onReply={handleReplyCall}
          loading={diplomacyLoading}
      />

      <DecisionReviewDialog 
          isOpen={isReviewOpen}
          onClose={() => { /* Prevent closing by clicking outside */ }}
          decisionText={pendingDecisionText}
          interpretation={interpretation}
          onApplyRecommendations={handleApplyRecommendations}
          onModify={handleModifyDecision}
          onIgnoreAndProceed={handleIgnoreAndProceed}
          onReturnToDiscussion={handleReturnToDiscussion}
          isProcessing={loading}
      />

      <SettingsPanel isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
    </main>
  );
}
