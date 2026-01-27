export enum AppStep {
  SEARCH = 1,
  LOAD_TRADES = 2,
  RESOLVE = 3,
  ANALYSIS = 4,
}

export interface MarketResult {
  condition_id: string;
  market_title: string;
  event_title: string;
}

export interface AnalysisMetrics {
  resolved_side: 'YES' | 'NO';
  trade_count: number;
  remaining_yes: number;
  remaining_no: number;
  final_value: number;
  total_spent: number;
  pnl: number;
  yes_buy_sh: number;
  yes_buy_cost: number;
  yes_sell_sh: number;
  yes_sell_cost: number;
  no_buy_sh: number;
  no_buy_cost: number;
  no_sell_sh: number;
  no_sell_cost: number;
}

export interface ChartDataPoint {
  date: string;
  value: number;
  shares: number;
}

export const MOCK_MARKETS: MarketResult[] = [
  {
    condition_id: "0x43b...82a",
    market_title: "Will Bitcoin hit $100k in 2024?",
    event_title: "Crypto Price Action 2024"
  },
  {
    condition_id: "0x91c...11b",
    market_title: "Fed Interest Rate Cut in March?",
    event_title: "US Monetary Policy"
  },
  {
    condition_id: "0x22a...cc4",
    market_title: "Dune: Part Two Opening Weekend > $80M",
    event_title: "Box Office Markets"
  }
];

export const MOCK_METRICS: AnalysisMetrics = {
  resolved_side: 'YES',
  trade_count: 142,
  remaining_yes: 1500.50,
  remaining_no: 0,
  final_value: 1500.50,
  total_spent: 850.25,
  pnl: 650.25,
  yes_buy_sh: 2000,
  yes_buy_cost: 1200,
  yes_sell_sh: 500,
  yes_sell_cost: 400,
  no_buy_sh: 100,
  no_buy_cost: 50,
  no_sell_sh: 100,
  no_sell_cost: 45
};

export const MOCK_CHART_DATA: ChartDataPoint[] = [
  { date: 'Jan', value: 100, shares: 200 },
  { date: 'Feb', value: 120, shares: 450 },
  { date: 'Mar', value: 300, shares: 800 },
  { date: 'Apr', value: 250, shares: 750 },
  { date: 'May', value: 400, shares: 1200 },
  { date: 'Jun', value: 850, shares: 1500 },
];