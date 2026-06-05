import React, { useState, useEffect } from 'react';

// --- Audio Decoding Utilities ---
// These helpers are used to process the raw audio data from the Gemini API.

function decode(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}
// --- End Audio Decoding Utilities ---


interface IntroSceneProps {
  text: string;
  audioB64: string;
  onComplete: () => void;
  audioContext: AudioContext;
}

const IntroScene: React.FC<IntroSceneProps> = ({ text, audioB64, onComplete, audioContext }) => {
  const [displayText, setDisplayText] = useState('');

  // Typewriter effect for the narration text
  useEffect(() => {
    setDisplayText('');
    if (text) {
      let i = 0;
      const intervalId = setInterval(() => {
        if (i < text.length) {
          setDisplayText(prev => prev + text.charAt(i));
          i++;
        } else {
          clearInterval(intervalId);
        }
      }, 40); // Adjust typing speed here
      return () => clearInterval(intervalId);
    }
  }, [text]);

  // Audio playback effect
  useEffect(() => {
    let source: AudioBufferSourceNode | null = null;
    
    const playAudio = async () => {
      if (!audioB64 || !audioContext || audioContext.state !== 'running') {
        // If there's no audio or context isn't ready, wait for text animation then complete.
        // This gives the user time to read.
        setTimeout(onComplete, Math.max(text.length * 50, 3000));
        return;
      }

      try {
        const decodedBytes = decode(audioB64);
        const audioBuffer = await decodeAudioData(decodedBytes, audioContext, 24000, 1);
        
        source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.onended = onComplete;
        source.start();
      } catch (error) {
        console.error("Failed to play narration audio:", error);
        onComplete(); // Move on even if audio fails
      }
    };

    playAudio();

    return () => {
      if (source) {
        // Stop and disconnect to clean up resources
        source.onended = null;
        try {
            source.stop();
        } catch (e) {
            // Can throw an error if already stopped, safe to ignore.
        }
        source.disconnect();
      }
    };
  }, [audioB64, onComplete, text.length, audioContext]);

  return (
    <div className="absolute inset-0 bg-black/80 z-10 flex items-center justify-center p-8 animate-fade-in">
      <p className="text-gray-300 text-xl md:text-2xl lg:text-3xl text-center max-w-4xl leading-relaxed italic">
        {displayText}
        <span className="animate-pulse">_</span>
      </p>
    </div>
  );
};

export default IntroScene;
