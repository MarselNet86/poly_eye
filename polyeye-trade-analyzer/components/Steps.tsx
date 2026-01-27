import React, { useState } from 'react';
import { Search, Upload, Download, ArrowRight, BarChart3, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, Button, Input, SectionHeader } from './Shared';
import { MarketResult, MOCK_MARKETS, AnalysisMetrics, MOCK_METRICS, MOCK_CHART_DATA } from '../types';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

// --- Step 1: Search ---
interface StepSearchProps {
  onComplete: (market: MarketResult) => void;
}

export const StepSearch: React.FC<StepSearchProps> = ({ onComplete }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MarketResult[]>([]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate API delay
    setTimeout(() => {
      setResults(MOCK_MARKETS.filter(m => m.market_title.toLowerCase().includes(query.toLowerCase())));
      setLoading(false);
    }, 800);
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-500">
      <SectionHeader title="Find Market" subtitle="Search for the Polymarket event you wish to analyze." />
      
      <form onSubmit={handleSearch} className="flex gap-4 mb-12">
        <Input 
          placeholder="e.g. 'Bitcoin 2024' or 'Election'" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Searching...' : <Search size={20} strokeWidth={1.5} />}
        </Button>
      </form>

      <div className="space-y-4">
        {results.map((market) => (
          <div 
            key={market.condition_id}
            onClick={() => onComplete(market)}
            className="group cursor-pointer bg-white rounded-3xl p-6 border border-black transition-all duration-300 hover:bg-black hover:text-white flex justify-between items-center"
          >
            <div>
              <h4 className="font-light text-xl mb-1">{market.market_title}</h4>
              <div className="flex gap-4 text-xs font-mono font-light text-gray-400 group-hover:text-gray-300">
                <span>ID: {market.condition_id}</span>
                <span>•</span>
                <span>{market.event_title}</span>
              </div>
            </div>
            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-white group-hover:text-black transition-all">
              <ArrowRight size={18} strokeWidth={1.5} />
            </div>
          </div>
        ))}
        {results.length === 0 && !loading && query && (
          <div className="text-center text-gray-400 py-10 font-mono text-sm font-light">No markets found. Try "Bitcoin".</div>
        )}
      </div>
    </div>
  );
};

// --- Step 2: Load Trades ---
interface StepLoadProps {
  onComplete: () => void;
  market: MarketResult | null;
}

export const StepLoad: React.FC<StepLoadProps> = ({ onComplete, market }) => {
  const [method, setMethod] = useState<'api' | 'file'>('api');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onComplete();
    }, 1200);
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-500">
      <SectionHeader title="Load Data" subtitle={`Import trade history for "${market?.market_title || 'Market'}"`} />

      <div className="flex bg-white rounded-full p-1 w-fit mb-8 border border-black">
        <button 
          onClick={() => setMethod('api')}
          className={`px-6 py-2 rounded-full text-sm font-light uppercase tracking-wider transition-all ${method === 'api' ? 'bg-black text-white' : 'text-gray-400 hover:text-black'}`}
        >
          API Fetch
        </button>
        <button 
          onClick={() => setMethod('file')}
          className={`px-6 py-2 rounded-full text-sm font-light uppercase tracking-wider transition-all ${method === 'file' ? 'bg-black text-white' : 'text-gray-400 hover:text-black'}`}
        >
          Upload JSON
        </button>
      </div>

      <Card className="max-w-xl">
        {method === 'api' ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input label="Condition ID" value={market?.condition_id || ''} readOnly className="text-gray-500 border-gray-300" />
            <Input label="User Address" placeholder="0x..." required />
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Fetching...' : 'Fetch Trades'}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="border border-dashed border-black rounded-3xl h-48 flex flex-col items-center justify-center text-gray-400 hover:bg-gray-50 transition-colors cursor-pointer group">
                <Upload size={32} strokeWidth={1} className="mb-4 group-hover:text-black" />
                <span className="uppercase text-xs font-bold tracking-widest">Drop JSON File Here</span>
                <input type="file" className="hidden" />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Parsing...' : 'Process File'}
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
};

// --- Step 3: Resolve ---
interface StepResolveProps {
  onComplete: (side: 'YES' | 'NO') => void;
}

export const StepResolve: React.FC<StepResolveProps> = ({ onComplete }) => {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-500">
      <SectionHeader title="Resolution" subtitle="How did the market resolve? Set the outcome to calculate PnL." />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button onClick={() => onComplete('YES')} className="group bg-white p-10 rounded-[40px] border border-black hover:bg-black hover:text-white transition-all text-left flex flex-col justify-between h-64">
          <div className="h-12 w-12 rounded-full border border-current flex items-center justify-center mb-4">
            <CheckCircle2 strokeWidth={1.5} />
          </div>
          <div>
            <span className="block text-4xl font-thin mb-2">YES</span>
            <span className="opacity-50 text-sm font-light uppercase tracking-wider">Winning Outcome</span>
          </div>
        </button>

        <button onClick={() => onComplete('NO')} className="group bg-white p-10 rounded-[40px] border border-black hover:bg-black hover:text-white transition-all text-left flex flex-col justify-between h-64">
           <div className="h-12 w-12 rounded-full border border-current flex items-center justify-center mb-4">
            <AlertCircle strokeWidth={1.5} />
          </div>
          <div>
            <span className="block text-4xl font-thin mb-2">NO</span>
            <span className="opacity-50 text-sm font-light uppercase tracking-wider">Winning Outcome</span>
          </div>
        </button>

        <button onClick={() => onComplete('YES')} className="group bg-gray-50 p-10 rounded-[40px] border border-black hover:bg-black hover:text-white transition-all text-left flex flex-col justify-between h-64 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5">
             <Search size={100} strokeWidth={0.5} color="currentColor" />
          </div>
          <div className="h-12 w-12 rounded-full border border-current flex items-center justify-center mb-4 z-10">
            <span className="font-mono text-xs">AI</span>
          </div>
          <div className="z-10">
            <span className="block text-4xl font-thin mb-2">AUTO</span>
            <span className="opacity-50 text-sm font-light uppercase tracking-wider">Infer from data</span>
          </div>
        </button>
      </div>
    </div>
  );
};

// --- Step 4: Analysis ---
interface StepAnalysisProps {
  metrics: AnalysisMetrics;
}

export const StepAnalysis: React.FC<StepAnalysisProps> = ({ metrics }) => {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <SectionHeader title="Performance" />
        <Button variant="outline">
          <Download size={18} strokeWidth={1.5} /> Download PDF
        </Button>
      </div>

      {/* Main KPI Card - Switched to White with Black Border for Minimal look */}
      <div className="bg-white rounded-[40px] p-8 md:p-12 text-black mb-8 relative overflow-hidden border border-black">
        <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-12">
          <div>
            <span className="text-gray-500 uppercase tracking-widest text-xs font-light mb-2 block">Total Profit / Loss</span>
            <div className={`text-6xl md:text-8xl font-thin tracking-tighter ${metrics.pnl >= 0 ? 'text-black' : 'text-red-500'}`}>
              ${metrics.pnl.toFixed(2)}
            </div>
            <div className="mt-6 flex gap-8">
               <div>
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-1 font-light">Total Spent</div>
                  <div className="text-xl font-light font-mono">${metrics.total_spent.toFixed(2)}</div>
               </div>
               <div>
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-1 font-light">Final Value</div>
                  <div className="text-xl font-light font-mono">${metrics.final_value.toFixed(2)}</div>
               </div>
            </div>
          </div>
          
          <div className="flex flex-col justify-end">
             <div className="space-y-4 font-mono text-sm border-t border-black pt-6">
                <div className="flex justify-between">
                  <span className="text-gray-500 font-light">Trade Count</span>
                  <span className="font-bold">{metrics.trade_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 font-light">Resolved Side</span>
                  <span className="font-bold">{metrics.resolved_side}</span>
                </div>
             </div>
          </div>
        </div>
      </div>

      {/* Secondary Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <Card title="Position Analysis" className="h-[400px] flex flex-col">
           <ResponsiveContainer width="100%" height="100%">
             <AreaChart data={MOCK_CHART_DATA}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#000" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#000" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{fontSize: 12, fill: '#999', fontWeight: 300}} dy={10} />
                <YAxis tickLine={false} axisLine={false} tick={{fontSize: 12, fill: '#999', fontWeight: 300}} tickFormatter={(value) => `$${value}`} />
                <Tooltip 
                  contentStyle={{borderRadius: '16px', border: '1px solid black', boxShadow: 'none'}}
                  cursor={{stroke: '#000', strokeWidth: 1}}
                />
                <Area type="monotone" dataKey="value" stroke="#000" strokeWidth={1} fillOpacity={1} fill="url(#colorValue)" />
             </AreaChart>
           </ResponsiveContainer>
        </Card>

        <div className="grid grid-cols-2 gap-4">
             <Card title="YES Volume" className="flex flex-col justify-center">
                <div className="text-3xl font-thin text-black mb-1">{metrics.yes_buy_sh + metrics.yes_sell_sh}</div>
                <div className="text-xs text-gray-400 font-mono font-light">SHARES TRADED</div>
             </Card>
             <Card title="NO Volume" className="flex flex-col justify-center">
                <div className="text-3xl font-thin text-black mb-1">{metrics.no_buy_sh + metrics.no_sell_sh}</div>
                <div className="text-xs text-gray-400 font-mono font-light">SHARES TRADED</div>
             </Card>
             <Card title="Remaining YES" className="flex flex-col justify-center">
                <div className="text-3xl font-thin text-black mb-1">{metrics.remaining_yes.toFixed(0)}</div>
                <div className="text-xs text-gray-400 font-mono font-light">HELD AT CLOSE</div>
             </Card>
             <Card title="Remaining NO" className="flex flex-col justify-center">
                <div className="text-3xl font-thin text-black mb-1">{metrics.remaining_no.toFixed(0)}</div>
                <div className="text-xs text-gray-400 font-mono font-light">HELD AT CLOSE</div>
             </Card>
        </div>
      </div>
    </div>
  );
};