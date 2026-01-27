import React, { useState } from 'react';
import { Header, Sidebar } from './components/Layout';
import { StepSearch, StepLoad, StepResolve, StepAnalysis } from './components/Steps';
import { AppStep, MarketResult, AnalysisMetrics, MOCK_METRICS } from './types';

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>(AppStep.SEARCH);
  const [completedSteps, setCompletedSteps] = useState<AppStep[]>([]);
  
  // Data State
  const [selectedMarket, setSelectedMarket] = useState<MarketResult | null>(null);
  const [resolvedSide, setResolvedSide] = useState<'YES' | 'NO' | null>(null);
  const [metrics, setMetrics] = useState<AnalysisMetrics | null>(null);

  const handleStepComplete = (step: AppStep) => {
    if (!completedSteps.includes(step)) {
      setCompletedSteps([...completedSteps, step]);
    }
    // Advance to next step automatically
    if (step < AppStep.ANALYSIS) {
      setCurrentStep(step + 1);
    }
  };

  const handleMarketSelect = (market: MarketResult) => {
    setSelectedMarket(market);
    handleStepComplete(AppStep.SEARCH);
  };

  const handleTradesLoaded = () => {
    handleStepComplete(AppStep.LOAD_TRADES);
  };

  const handleResolutionSet = (side: 'YES' | 'NO') => {
    setResolvedSide(side);
    // Mock analysis generation
    const mockCalculatedMetrics = { ...MOCK_METRICS, resolved_side: side };
    setMetrics(mockCalculatedMetrics);
    handleStepComplete(AppStep.RESOLVE);
  };

  const renderContent = () => {
    switch (currentStep) {
      case AppStep.SEARCH:
        return <StepSearch onComplete={handleMarketSelect} />;
      case AppStep.LOAD_TRADES:
        return <StepLoad onComplete={handleTradesLoaded} market={selectedMarket} />;
      case AppStep.RESOLVE:
        return <StepResolve onComplete={handleResolutionSet} />;
      case AppStep.ANALYSIS:
        return metrics ? <StepAnalysis metrics={metrics} /> : <div>Loading...</div>;
      default:
        return <div>Unknown Step</div>;
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] font-sans text-black pb-20 selection:bg-black selection:text-white">
      <Header />
      
      <main className="max-w-[1600px] mx-auto px-4 md:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar (Navigator) */}
          <aside className="lg:col-span-3">
             <Sidebar 
                currentStep={currentStep} 
                completedSteps={completedSteps} 
                onStepClick={setCurrentStep}
             />
          </aside>

          {/* Right Content Area */}
          <section className="lg:col-span-9">
            <div className="bg-white rounded-[48px] p-8 md:p-12 min-h-[600px] border border-black">
               {renderContent()}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
};

export default App;