import React from 'react';

interface ChoiceInputProps {
  choices: string[];
  onChoice: (choice: string) => void;
  isLoading: boolean;
}

const ChoiceInput: React.FC<ChoiceInputProps> = ({ choices, onChoice, isLoading }) => {
  return (
    <div className="p-4 sm:p-6 border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {choices.map((choice, index) => (
          <button
            key={index}
            onClick={() => onChoice(choice)}
            disabled={isLoading}
            className="w-full text-left p-4 rounded-lg bg-gray-800 hover:bg-red-800/80 disabled:bg-gray-600 disabled:cursor-not-allowed transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
          >
            <span className="font-semibold text-gray-200">{choice}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ChoiceInput;
