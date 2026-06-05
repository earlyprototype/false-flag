import React, { useRef, useEffect } from 'react';
import { type StorySegment, type UrgencyLevel } from '../types';

interface StoryDisplayProps {
  storyHistory: StorySegment[];
}

const StoryDisplay: React.FC<StoryDisplayProps> = ({ storyHistory }) => {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [storyHistory]);

  if (storyHistory.length === 0) {
    return null; // Don't render anything if there's no history yet
  }

  const latestSegment = storyHistory[storyHistory.length - 1];
  
  const urgencyColorMap: Record<UrgencyLevel, string> = {
    low: 'bg-blue-500',
    medium: 'bg-yellow-500',
    high: 'bg-red-600',
  };

  return (
    <div className="flex-1 flex flex-col p-4 sm:p-6 lg:p-8 overflow-y-auto">
      <div className="bg-black/50 rounded-lg shadow-2xl overflow-hidden">
        <div className="aspect-w-16 aspect-h-9">
           <img
            key={latestSegment.id}
            src={latestSegment.imageUrl}
            alt={latestSegment.imagePrompt}
            className="object-cover w-full h-full animate-fade-in"
          />
        </div>
        <div className="p-6">
          <p className="text-gray-300 leading-relaxed whitespace-pre-wrap mb-6">{latestSegment.story}</p>
          
          {latestSegment.advisorDialogue && latestSegment.advisorDialogue.length > 0 && (
            <div className="space-y-4 border-t border-gray-700 pt-4">
              {latestSegment.advisorDialogue.map((advisor, index) => (
                <div key={index} className="border-l-4 border-red-500/80 pl-4 py-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${urgencyColorMap[advisor.urgency] ?? 'bg-gray-500'}`}
                      title={`Urgency: ${advisor.urgency.charAt(0).toUpperCase() + advisor.urgency.slice(1)}`}
                    ></span>
                    <p className="font-semibold text-red-400">{advisor.advisor}:</p>
                  </div>
                  <p className="text-gray-400 italic pl-5">"{advisor.dialogue}"</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div ref={endOfMessagesRef} />
    </div>
  );
};

export default StoryDisplay;
