import { type Chat } from "@google/genai";

export interface AdvisorAffinity {
  nsa: number; // National Security Adviser
  cds: number; // Chief of the Defence Staff
  gchq: number; // Director of GCHQ
}

export type UnitReadiness = 'High' | 'Medium' | 'Low' | 'Deployed' | 'Damaged';
export type UnitType = 'Naval' | 'Air' | 'Ground' | 'Cyber/Intel';

export interface MilitaryUnit {
  id: string; // Unique ID for tracking
  name: string;
  type: UnitType;
  quantity: number;
  location: string;
  readiness: UnitReadiness;
}

export interface Stats {
  militaryResources: MilitaryUnit[];
  advisorAffinity: AdvisorAffinity;
  threatLevel: number;
  domesticStability: number;
  natoBacking: number;
  currentTurn: number;
}

export type UrgencyLevel = 'low' | 'medium' | 'high';

export interface AdvisorDialogue {
  advisor: string;
  dialogue: string;
  urgency: UrgencyLevel;
}

export interface StorySegment {
  id: string;
  narratorIntro: string;
  story: string;
  imageUrl: string;
  imagePrompt: string;
  choices: string[];
  advisorDialogue: AdvisorDialogue[];
}

export interface GeminiResponse {
  narratorIntro: string;
  story: string;
  choices: string[];
  updatedStats: Stats;
  imagePrompt: string;
  advisorDialogue: AdvisorDialogue[];
}

export interface GameState {
  stats: Stats;
  storyHistory: StorySegment[];
  isLoading: boolean;
  error: string | null;
  chatSession: Chat | null;
}