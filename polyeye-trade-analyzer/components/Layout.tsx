import React from 'react';
import { AppStep } from '../types';
import { Search, ListFilter, Scale, BarChart3 } from 'lucide-react';

export const Header: React.FC = () => (
  <header className="py-6 px-8 md:px-12 bg-[#F5F5F7] sticky top-0 z-50 border-b border-black">
    <div className="flex items-center">
       <div className="text-2xl font-thin tracking-[0.2em] uppercase text-black">
         POLYeye
       </div>
    </div>
  </header>
);

interface SidebarProps {
  currentStep: AppStep;
  completedSteps: AppStep[];
  onStepClick: (step: AppStep) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentStep, completedSteps, onStepClick }) => {
  const steps = [
    { id: AppStep.SEARCH, label: 'Search', icon: Search },
    { id: AppStep.LOAD_TRADES, label: 'Load Data', icon: ListFilter },
    { id: AppStep.RESOLVE, label: 'Resolve', icon: Scale },
    { id: AppStep.ANALYSIS, label: 'Analysis', icon: BarChart3 },
  ];

  return (
    <div className="bg-white rounded-[40px] p-4 border border-black sticky top-32">
      <div className="flex flex-col gap-2">
        {steps.map((step) => {
          const isActive = currentStep === step.id;
          const isCompleted = completedSteps.includes(step.id);
          const isClickable = isCompleted || isActive || step.id < currentStep;

          return (
            <button
              key={step.id}
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={`
                relative flex items-center gap-4 p-4 rounded-[32px] transition-all duration-500 group overflow-hidden border border-transparent
                ${isActive ? 'bg-black text-white' : 'text-gray-400 hover:border-black hover:text-black'}
                ${!isClickable ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <div className={`
                h-10 w-10 rounded-full flex items-center justify-center transition-colors duration-300
                ${isActive ? 'bg-white/10 text-white' : isCompleted ? 'bg-gray-100 text-black' : 'bg-gray-50 text-gray-400 group-hover:bg-white group-hover:text-black'}
              `}>
                <step.icon size={18} strokeWidth={1.5} />
              </div>
              
              <div className="text-left">
                 <span className={`block text-[10px] font-light uppercase tracking-wider mb-0.5 ${isActive ? 'text-gray-400' : 'text-gray-400'}`}>Step 0{step.id}</span>
                 <span className={`block text-sm font-light uppercase tracking-wide ${isActive ? 'text-white' : 'text-gray-500 group-hover:text-black'}`}>{step.label}</span>
              </div>
            </button>
          );
        })}
      </div>
      
      {/* Decorative element at bottom of sidebar */}
      <div className="mt-8 p-6 bg-[#F5F5F7] rounded-[32px] text-center border border-transparent">
         <span className="text-[10px] font-light uppercase tracking-widest text-gray-400">v1.0</span>
      </div>
    </div>
  );
};