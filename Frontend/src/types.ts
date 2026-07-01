export interface LotteryResult {
  date: string;
  numbers: number[];
  powerball: number;
}

export type SpreadType = 'tight' | 'wide' | 'mixed';
export type LeaningType = 'left' | 'right' | 'middle';
export type ConsecutiveType = 'yes' | 'no';

export interface GenerationPreferences {
  spread: SpreadType;
  leaning: LeaningType;
  consecutive: ConsecutiveType;
}

export type EngineType = 'gaussian' | 'strategy';
export type StrategyId = 'hot' | 'recent' | 'overdue' | 'decay' | 'random';

export interface GeneratedNumbers {
  numbers: number[];
  powerball: number;
}

// --- Predictions contract -------------------------------------------------
// Mirrors research/docs/predictions_contract.md (the authority). snake_case keys
// match predictions.json exactly — no remapping. Do not redefine these elsewhere.

export type PredictionStrategy =
  | 'burst_volatility'
  | 'mean_reversion'
  | 'momentum_carry'
  | 'balanced_hybrid'
  | 'lean_bias';

export interface PredictionSet {
  id: number;
  strategy: PredictionStrategy;
  main_numbers: number[];
  powerball: number;
  rationale: string;
}

export interface PredictionsMetadata {
  total_draws_analyzed: number;
  date_range: string;
  uniformity_confirmed: boolean;
  chi_square_p_main: number;
  chi_square_p_powerball: number;
  applied_filters?: {           // present only on live API responses
    date_from: string | null;
    lean: string;
    spread: string;
    consecutive: boolean;
  };
}

export interface PredictionsDocument {
  draw_reference: number;
  generated_at: string;
  sets: PredictionSet[];
  metadata: PredictionsMetadata;
}

export interface PredictionSetWeighted {
  id: number;
  strategy: PredictionStrategy;
  main_numbers: number[];
  powerball: number;
  rationale: string;
  constraint_satisfied: boolean;
}

export interface PredictionsWeightedDocument {
  draw_reference: number;
  generated_at: string;
  sets: PredictionSetWeighted[];
  metadata: {
    total_draws_analyzed: number;
    date_range: string;
    uniformity_confirmed: boolean;
    chi_square_p_main: number;
    chi_square_p_powerball: number;
    applied_filters: {
      date_from: string | null;
      lean: string;
      spread: string;
      consecutive: boolean;
      enforcement: 'active';
    };
  };
}

// --- Live API response types (FastAPI /predict/weighted) ------------------

export interface ApiTicket {
  main_numbers: number[];
  powerball: number;
  spread: number;
  lean: string;
  has_consecutive: boolean;
  constraint_satisfied: boolean;
}

export interface ApiWeightedResponse {
  engine: string;
  mode: string;
  generated_at: string;
  params: Record<string, unknown>;
  tickets: ApiTicket[];
  metadata: Record<string, unknown>;
}
