import React, { useState, useEffect, useCallback, useRef } from 'react';
import { type GameState, type GeminiResponse } from './types';
import { INITIAL_STATS, INITIAL_USER_PROMPT } from './constants';
import { createChatSession, getNextStorySegment, generateStoryImage, generateNarrationAudio } from './services/geminiService';
import Sidebar from './components/Sidebar';
import StoryDisplay from './components/StoryDisplay';
import ChoiceInput from './components/ChoiceInput';
import IntroScene from './components/IntroScene';

const BACKGROUND_MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/10/14/audio_39e1420738.mp3?filename=war-zone-122952.mp3";

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>({
    stats: INITIAL_STATS,
    storyHistory: [],
    isLoading: false, // Start as false, loading will be triggered by starting the game
    error: null,
    chatSession: null,
  });

  const [gameStarted, setGameStarted] = useState(false);
  const [narration, setNarration] = useState<{ text: string; audioB64: string } | null>(null);
  const backgroundMusicRef = useRef<HTMLAudioElement>(null);
  const [audioContext] = useState(() => new (window.AudioContext || window['webkitAudioContext'])({ sampleRate: 24000 }));


  const processTurn = useCallback(async (response: GeminiResponse) => {
    // Generate image and audio in parallel for speed
    const [imageUrl, narrationAudioB64] = await Promise.all([
      generateStoryImage(response.imagePrompt),
      generateNarrationAudio(response.narratorIntro)
    ]);

    setNarration({ text: response.narratorIntro, audioB64: narrationAudioB64 });

    setGameState(prevState => ({
      ...prevState,
      stats: response.updatedStats,
      storyHistory: [
        ...prevState.storyHistory,
        {
          id: `turn-${response.updatedStats.currentTurn}`,
          narratorIntro: response.narratorIntro,
          story: response.story,
          imageUrl,
          imagePrompt: response.imagePrompt,
          choices: response.choices,
          advisorDialogue: response.advisorDialogue,
        },
      ],
      isLoading: false,
      error: null,
    }));
  }, []);

  const startGame = useCallback(async () => {
    setNarration(null);
    setGameState(prevState => ({ ...prevState, isLoading: true, error: null, storyHistory: [], stats: INITIAL_STATS }));
    try {
      const chat = createChatSession();
      setGameState(prevState => ({ ...prevState, chatSession: chat }));
      const response = await getNextStorySegment(chat, INITIAL_USER_PROMPT);
      await processTurn(response);
    } catch (e) {
      const error = e instanceof Error ? e.message : "An unknown error occurred during startup.";
      setGameState(prevState => ({ ...prevState, isLoading: false, error }));
    }
  }, [processTurn]);

  const handleStartGame = async () => {
    setGameStarted(true);
    // User interaction has occurred, so we can now safely start audio.
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }
    if (backgroundMusicRef.current) {
        backgroundMusicRef.current.volume = 0.05;
        backgroundMusicRef.current.play().catch(e => console.error("Background music failed to play:", e));
    }
    await startGame();
  };

  const handleChoice = async (choice: string) => {
    if (!gameState.chatSession) {
      setGameState(prevState => ({ ...prevState, error: "Chat session not initialized." }));
      return;
    }
    setGameState(prevState => ({ ...prevState, isLoading: true, error: null }));
    setNarration(null); // Clear previous narration if any

    try {
      const response = await getNextStorySegment(gameState.chatSession, choice);
      await processTurn(response);
    } catch (e) {
      const error = e instanceof Error ? e.message : "An unknown error occurred.";
      setGameState(prevState => ({ ...prevState, isLoading: false, error }));
    }
  };
  
  const handleNarrationComplete = () => {
    setNarration(null);
  };

  if (!gameStarted) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 bg-dots-pattern">
        <div className="text-center p-8 bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-2xl border border-gray-700 max-w-2xl mx-4">
          <h1 className="text-4xl md:text-5xl font-bold text-red-500 tracking-wider uppercase">War Game</h1>
          <p className="text-gray-300 mt-4">
            You are the Prime Minister. A global crisis is unfolding. Your decisions will shape the future. The nation is watching.
          </p>
          <button
            onClick={handleStartGame}
            className="mt-8 px-8 py-4 bg-red-700 hover:bg-red-600 text-white font-bold text-lg rounded-lg transition-transform transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
          >
            Begin Simulation
          </button>
          <p className="text-xs text-gray-500 mt-8">Based on the Sky News 'War Game' podcast. For the best experience, use headphones.</p>
        </div>
        <style>{`.bg-dots-pattern { background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0); background-size: 20px 20px; }`}</style>
      </div>
    );
  }

  const latestSegment = gameState.storyHistory.length > 0 ? gameState.storyHistory[gameState.storyHistory.length - 1] : null;
  const showMainContent = !narration && ! (gameState.isLoading && gameState.storyHistory.length === 0);

  return (
    <div className="h-screen w-screen flex flex-col md:flex-row bg-gray-900 font-sans">
      <Sidebar stats={gameState.stats} />
      <main className="flex-1 flex flex-col bg-dots-pattern relative">
        {narration && (
          <IntroScene 
            text={narration.text}
            audioB64={narration.audioB64}
            onComplete={handleNarrationComplete}
            audioContext={audioContext}
          />
        )}

        {gameState.isLoading && gameState.storyHistory.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-center p-4">
            <div>
              <h2 className="text-2xl font-bold text-red-500 animate-pulse">Establishing Secure Connection...</h2>
              <p className="text-gray-400 mt-2">Initializing crisis simulation. Stand by.</p>
            </div>
          </div>
        )}

        {showMainContent && (
          <>
            <StoryDisplay storyHistory={gameState.storyHistory} />

            {gameState.error && (
              <div className="m-4 p-4 bg-red-900/50 border border-red-700 text-red-300 rounded-lg">
                  <p className="font-bold">A critical error occurred:</p>
                  <p>{gameState.error}</p>
                  <button onClick={startGame} className="mt-2 px-4 py-2 bg-red-700 hover:bg-red-600 rounded">
                    Restart Simulation
                  </button>
                </div>
            )}

            {latestSegment && !gameState.isLoading && (
              <ChoiceInput
                choices={latestSegment.choices}
                onChoice={handleChoice}
                isLoading={gameState.isLoading}
              />
            )}
            
            {gameState.isLoading && gameState.storyHistory.length > 0 && (
              <div className="p-6 border-t border-gray-700 bg-gray-900/50">
                <div className="flex items-center justify-center space-x-3">
                  <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-red-400 font-semibold">Analyzing outcomes and receiving intel...</span>
                </div>
              </div>
            )}
          </>
        )}
      </main>
      <audio ref={backgroundMusicRef} src={BACKGROUND_MUSIC_URL} loop controls={false} />
      <style>{`
        .bg-dots-pattern {
          background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0);
          background-size: 20px 20px;
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-fade-in {
          animation: fade-in 1s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default App;
