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

export interface GeneratedNumbers {
  numbers: number[];
  powerball: number;
}

// --- Predictions contract -------------------------------------------------
// Mirrors backend/docs/predictions_contract.md (the authority). snake_case keys
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
}

export interface PredictionsDocument {
  draw_reference: number;
  generated_at: string;
  sets: PredictionSet[];
  metadata: PredictionsMetadata;
}
