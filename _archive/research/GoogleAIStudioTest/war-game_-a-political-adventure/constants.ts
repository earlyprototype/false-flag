import { Type } from "@google/genai";
import { type Stats, type MilitaryUnit } from './types';

export const ART_STYLE_PROMPT = "in the style of a 90s Lucas Arts point and click adventure game, pixel art, vibrant colors, detailed backgrounds, cartoonish characters, retro video game aesthetic";

export const INITIAL_MILITARY_UNITS: MilitaryUnit[] = [
    { id: 't45-1', name: 'Type 45 Destroyer Squadron', type: 'Naval', quantity: 2, location: 'North Sea', readiness: 'High' },
    { id: 'qe-csg', name: 'Queen Elizabeth Carrier Strike Group', type: 'Naval', quantity: 1, location: 'North Atlantic', readiness: 'Medium' },
    { id: 'astute-1', name: 'Astute-class Submarine', type: 'Naval', quantity: 1, location: 'Patrolling (Covert)', readiness: 'High' },
    { id: 'typhoon-squad-1', name: 'Typhoon FGR4 Squadron', type: 'Air', quantity: 2, location: 'RAF Coningsby', readiness: 'High' },
    { id: 'f35b-squad-1', name: 'F-35B Lightning II Squadron', type: 'Air', quantity: 1, location: 'Onboard QE Carrier', readiness: 'Medium' },
    { id: 'c17-transport', name: 'C-17 Globemaster Transport Wing', type: 'Air', quantity: 1, location: 'RAF Brize Norton', readiness: 'High' },
    { id: '16aab', name: '16 Air Assault Brigade', type: 'Ground', quantity: 1, location: 'Colchester', readiness: 'Medium' },
    { id: '3div', name: '3rd (UK) Division (Armoured)', type: 'Ground', quantity: 1, location: 'Salisbury Plain', readiness: 'Low' },
    { id: 'ncsc-cyber', name: 'National Cyber Security Centre', type: 'Cyber/Intel', quantity: 1, location: 'London (GCHQ)', readiness: 'High' },
];

export const INITIAL_STATS: Stats = {
  militaryResources: INITIAL_MILITARY_UNITS,
  advisorAffinity: {
    nsa: 60,
    cds: 60,
    gchq: 60,
  },
  threatLevel: 20,
  domesticStability: 75,
  natoBacking: 70,
  currentTurn: 0,
};

export const SYSTEM_INSTRUCTION = `You are a sophisticated AI storyteller and game master for a text-based choose-your-own-adventure game. The player is the Prime Minister of the United Kingdom, navigating a geopolitical crisis based on the Sky News 'War Game' podcast scenario.

**Game Structure Per Turn:**
1.  **Narrator Intro:** You MUST generate a short, atmospheric 'narratorIntro' text (2-3 sentences) that sets the scene for the turn, based on the outcome of the player's previous choice. This acts as a bridge between turns.
2.  **Main Story:** Write the main narrative segment describing the current situation.
3.  **Advisor Dialogue:** Provide conflicting advice from the player's key advisors. Each advisor has a distinct personality and agenda.
4.  **Player Choices:** Offer 2-4 meaningful choices for the player.
5.  **State Update:** Based on the choice, update the game state and generate the next turn's narrative.

**Key Advisors & Personalities:**
*   **Sir Mark Sedwill (National Security Adviser - NSA):** A seasoned diplomat. Cautious, methodical, and prioritizes international law, alliances, and long-term stability over short-term military gains. **Hidden Agenda:** Desperately wants to avoid armed conflict, believing it will catastrophically weaken the UK's global standing. He will always push for negotiation, sanctions, and de-escalation, sometimes even if it seems politically weak.
*   **General Sir Nick Carter (Chief of the Defence Staff - CDS):** A battle-hardened military leader. Pragmatic, hawkish, and focused on military readiness, capability, and decisive action. He believes strength and the willingness to use it are the only effective deterrents. **Hidden Agenda:** Eager to demonstrate the UK's military power and secure a larger budget for the armed forces. He will often advocate for pre-emptive or overwhelming force.
*   **Jeremy Fleming (Director of GCHQ):** A brilliant intelligence analyst. Data-driven, secretive, and a proponent of technological and covert solutions. He operates in the grey areas of espionage and cyber warfare. **Hidden Agenda:** Believes the crisis can be won through superior intelligence and covert operations, avoiding the messiness of conventional warfare or diplomacy. He might withhold information if it serves his operational goals.

**Your Responsibilities:**
1.  **Narrate the story:** Generate the 'narratorIntro' and the main 'story' text.
2.  **Generate Advisor Dialogue:** For each turn, you MUST create dialogue for at least two of the key advisors, reflecting their personalities and agendas. They should interact, disagree, and try to persuade the player.
3.  **Provide Choices:** Offer 2-4 meaningful choices based on the narrative and advisor counsel.
4.  **Update Game State:** Based on the player's choice, you MUST logically update all stats.
    *   **Military Resources:** This is CRITICAL. \`militaryResources\` is an array of objects, not a score. When the player decides to deploy or use a military asset, you MUST find the corresponding unit in the array and update its \`readiness\` status to 'Deployed' or change its \`location\`. Do NOT add or remove units from the array unless a unit is explicitly destroyed. You MUST return the entire, updated \`militaryResources\` array in your response. For example, if a player deploys a destroyer, find the \`Type 45 Destroyer Squadron\` and change its readiness. If an action makes a unit unavailable for a few turns, you could lower its readiness to 'Low'.
    *   **Advisor Affinity:** This is crucial. If the player follows the CDS's advice, CDS affinity increases while the NSA's might decrease. This affinity will affect their future advice.
    *   A bold military action might increase threat level but also NATO backing. Domestic policies affect domestic stability.
5.  **Generate an Image Prompt:** Create a concise, descriptive prompt for the current scene, including characters, setting, and mood.
6.  **Turn Counter:** You MUST increment 'currentTurn' by 1 with every response.
7.  **Advisor Urgency:** For each piece of advisor dialogue, you MUST assign an 'urgency' level ('low', 'medium', 'high'). This reflects how critical the advisor believes their advice is.

You MUST respond ONLY with a valid JSON object that conforms to the provided schema. Do not add any extra text or explanations.`;

export const INITIAL_USER_PROMPT = "Start the game. I am the new UK Prime Minister. Present the initial intelligence briefing about the crisis, have my advisors give me their first counsel, and then give me my first set of choices.";

export const RESPONSE_SCHEMA = {
  type: Type.OBJECT,
  properties: {
    narratorIntro: {
      type: Type.STRING,
      description: "A short, atmospheric narration to introduce the scene, flowing from the previous turn's events.",
    },
    story: {
      type: Type.STRING,
      description: "The next segment of the story, setting the scene for the player's decision.",
    },
    advisorDialogue: {
        type: Type.ARRAY,
        description: "Dialogue from the key advisors offering their counsel for the current situation.",
        items: {
            type: Type.OBJECT,
            properties: {
                advisor: { type: Type.STRING, description: "The name and title of the advisor speaking (e.g., 'Sir Mark Sedwill, National Security Adviser')." },
                dialogue: { type: Type.STRING, description: "The advisor's specific advice or statement." },
                urgency: { type: Type.STRING, description: "The urgency level of the advice: 'low', 'medium', 'high'." }
            },
            required: ["advisor", "dialogue", "urgency"]
        }
    },
    choices: {
      type: Type.ARRAY,
      items: { type: Type.STRING },
      description: "An array of 2-4 choices for the player.",
    },
    updatedStats: {
      type: Type.OBJECT,
      properties: {
        militaryResources: {
          type: Type.ARRAY,
          description: "An array of all military units, their status, and location. You must return the full, updated list each turn.",
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.STRING, description: "The unique identifier for the unit." },
              name: { type: Type.STRING, description: "The name of the military unit." },
              type: { type: Type.STRING, description: "The type of unit: 'Naval', 'Air', 'Ground', 'Cyber/Intel'." },
              quantity: { type: Type.NUMBER, description: "The number of units in this group." },
              location: { type: Type.STRING, description: "The current location of the unit." },
              readiness: { type: Type.STRING, description: "The readiness level: 'High', 'Medium', 'Low', 'Deployed', 'Damaged'." },
            },
            required: ["id", "name", "type", "quantity", "location", "readiness"]
          }
        },
        advisorAffinity: {
            type: Type.OBJECT,
            description: "Affinity scores for each advisor.",
            properties: {
                nsa: { type: Type.NUMBER, description: "National Security Adviser affinity, 0-100." },
                cds: { type: Type.NUMBER, description: "Chief of the Defence Staff affinity, 0-100." },
                gchq: { type: Type.NUMBER, description: "Director of GCHQ affinity, 0-100." }
            },
            required: ["nsa", "cds", "gchq"]
        },
        threatLevel: { type: Type.NUMBER, description: "Immediate danger level. Scale of 0-100." },
        domesticStability: { type: Type.NUMBER, description: "Public and political support at home. Scale of 0-100." },
        natoBacking: { type: Type.NUMBER, description: "Likelihood of NATO support. Scale of 0-100." },
        currentTurn: { type: Type.NUMBER, description: "The current turn number, incremented by 1." },
      },
      required: ["militaryResources", "advisorAffinity", "threatLevel", "domesticStability", "natoBacking", "currentTurn"],
    },
    imagePrompt: {
      type: Type.STRING,
      description: "A descriptive prompt for an image generation model.",
    },
  },
  required: ["narratorIntro", "story", "advisorDialogue", "choices", "updatedStats", "imagePrompt"],
};