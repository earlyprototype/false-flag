import { GoogleGenAI, Chat, Modality } from "@google/genai";
import { ART_STYLE_PROMPT, RESPONSE_SCHEMA, SYSTEM_INSTRUCTION } from "../constants";
import { type GeminiResponse } from "../types";

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY environment variable not set");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

export function createChatSession(): Chat {
  return ai.chats.create({
    model: 'gemini-2.5-flash',
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      responseMimeType: "application/json",
      responseSchema: RESPONSE_SCHEMA,
    },
  });
}

export async function getNextStorySegment(
  chat: Chat,
  message: string
): Promise<GeminiResponse> {
  try {
    const response = await chat.sendMessage({ message });
    const jsonText = response.text.trim();
    // Gemini can sometimes wrap the JSON in ```json ... ```, so we strip it.
    const cleanJsonText = jsonText.replace(/^```json\s*|```$/g, '');
    const parsedResponse: GeminiResponse = JSON.parse(cleanJsonText);
    return parsedResponse;
  } catch (error) {
    console.error("Error parsing Gemini response:", error);
    throw new Error("Failed to get a valid story segment from the AI. The response was not valid JSON.");
  }
}

export async function generateStoryImage(prompt: string): Promise<string> {
  const fullPrompt = `${prompt}, ${ART_STYLE_PROMPT}`;
  try {
    const response = await ai.models.generateImages({
      model: 'imagen-4.0-generate-001',
      prompt: fullPrompt,
      config: {
        numberOfImages: 1,
        outputMimeType: 'image/jpeg',
        aspectRatio: '16:9',
      },
    });

    if (response.generatedImages && response.generatedImages.length > 0) {
      const base64ImageBytes: string = response.generatedImages[0].image.imageBytes;
      return `data:image/jpeg;base64,${base64ImageBytes}`;
    }
    throw new Error("No image was generated.");
  } catch (error) {
    console.error("Error generating image:", error);
    // Return a placeholder image on failure
    return `https://picsum.photos/1280/720?random=${Math.random()}`;
  }
}

export async function generateNarrationAudio(text: string): Promise<string> {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-preview-tts",
      contents: [{ parts: [{ text: `Narrate in a serious, grim tone: ${text}` }] }],
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: 'Charon' }, // A deep, serious voice
            },
        },
      },
    });
    
    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (base64Audio) {
      return base64Audio;
    }
    throw new Error("No audio data was generated.");
  } catch(error) {
    console.error("Error generating narration audio:", error);
    return ""; // Return empty string on failure
  }
}