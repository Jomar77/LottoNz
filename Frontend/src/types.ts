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
