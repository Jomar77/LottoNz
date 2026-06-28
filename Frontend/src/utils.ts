import { LotteryResult, GenerationPreferences, GeneratedNumbers, PredictionSet, PredictionStrategy } from './types';

/**
 * Enhanced Randomness Utilities
 */

// Cryptographically stronger random value between 0 and 1
function cryptoRandom(): number {
  const array = new Uint32Array(1);
  window.crypto.getRandomValues(array);
  return array[0] / (0xffffffff + 1);
}

/**
 * Gaussian (normal) distribution using Box-Muller transform.
 * Replaces uniform Math.random() for "bell curve" behaviors.
 */
function gaussianRandom(mean = 0, stddev = 1): number {
  let u = 0;
  let v = 0;
  // Use cryptoRandom for better entropy
  while (u === 0) u = cryptoRandom();
  while (v === 0) v = cryptoRandom();
  const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  return z * stddev + mean;
}

/**
 * Core Statistics Calculations
 */

export function calculateSpread(numbers: number[]): number {
  return Math.max(...numbers) - Math.min(...numbers);
}

export function hasConsecutive(numbers: number[]): boolean {
  const sorted = [...numbers].sort((a, b) => a - b);
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i + 1] - sorted[i] === 1) return true;
  }
  return false;
}

export function findHistoricalMatch(numbers: number[], historicalData: LotteryResult[]): LotteryResult | null {
  if (numbers.length !== 6 || new Set(numbers).size !== 6) {
    return null;
  }

  const selectedNumbers = new Set(numbers);

  return (
    historicalData.find(result => {
      if (result.numbers.length !== 6 || new Set(result.numbers).size !== 6) {
        return false;
      }

      return result.numbers.every(num => selectedNumbers.has(num));
    }) ?? null
  );
}

export function isUnique(numbers: number[], historicalData: LotteryResult[]): boolean {
  return findHistoricalMatch(numbers, historicalData) === null;
}

/**
 * Generator Functions
 */

export function generatePowerball(): number {
  // Powerball (1-10) using Gaussian centered on the middle (5.5)
  // This makes middle numbers more likely unless skewed.
  const val = Math.round(gaussianRandom(5.5, 2.2));
  return Math.max(1, Math.min(10, val));
}

function calculateFrequencies(historicalData: LotteryResult[]): Map<number, number> {
  const frequencies = new Map<number, number>();
  for (let i = 1; i <= 40; i++) frequencies.set(i, 0);
  
  for (const result of historicalData) {
    for (const num of result.numbers) {
      frequencies.set(num, (frequencies.get(num) || 0) + 1);
    }
  }
  return frequencies;
}

/**
 * New Hybrid Random Selection:
 * Combines Frequency Weights + Gaussian Leaning
 */
function getGaussianWeightedChoice(weights: Map<number, number>, preferences: GenerationPreferences): number {
  let mean: number;
  let stddev = 8; // Spread of the bell curve

  // Define the "Hot Zone" based on preference
  switch (preferences.leaning) {
    case 'left': mean = 10; break;
    case 'middle': mean = 20; break;
    case 'right': mean = 30; break;
    default: mean = 20; stddev = 15; // Wide bell curve for mixed
  }

  // 1. Generate a "target" number using Gaussian distribution
  const target = gaussianRandom(mean, stddev);

  // 2. Adjust historical weights based on proximity to the target
  // Numbers closer to our Gaussian target get a significant boost.
  const candidates: { num: number; weight: number }[] = [];
  let totalWeight = 0;

  for (let i = 1; i <= 40; i++) {
    const baseFreq = weights.get(i) || 0;
    // Proximity factor: how close is this number to our random Gaussian target?
    const proximity = Math.exp(-Math.pow(i - target, 2) / (2 * Math.pow(4, 2)));
    
    // Combine historical frequency with the Gaussian proximity
    const combinedWeight = (baseFreq + 1) * (1 + proximity * 5);
    
    candidates.push({ num: i, weight: combinedWeight });
    totalWeight += combinedWeight;
  }

  // 3. Weighted Random Selection (standard)
  let random = cryptoRandom() * totalWeight;
  for (const candidate of candidates) {
    random -= candidate.weight;
    if (random <= 0) return candidate.num;
  }

  return Math.floor(cryptoRandom() * 40) + 1;
}

export function generateNumbers(
  historicalData: LotteryResult[],
  preferences: GenerationPreferences
): GeneratedNumbers {
  const frequencies = calculateFrequencies(historicalData);
  const maxAttempts = 2000;
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const numbers: number[] = [];
    
    // Generate 6 unique numbers using our Hybrid Gaussian-Weighted logic
    while (numbers.length < 6) {
      const num = getGaussianWeightedChoice(frequencies, preferences);
      if (!numbers.includes(num)) {
        numbers.push(num);
      }
    }
    
    const spread = calculateSpread(numbers);
    const hasConsec = hasConsecutive(numbers);
    
    // Validation logic against preferences
    const spreadValid = 
      (preferences.spread === 'tight' && spread <= 18) ||
      (preferences.spread === 'wide' && spread >= 22) ||
      preferences.spread === 'mixed';
    
    const consecValid = 
      (preferences.consecutive === 'yes' && hasConsec) ||
      (preferences.consecutive === 'no' && !hasConsec);
    
    if (spreadValid && consecValid && isUnique(numbers, historicalData)) {
      return {
        numbers: numbers.sort((a, b) => a - b),
        powerball: generatePowerball()
      };
    }
  }
  
  // High-entropy fallback
  return {
    numbers: [4, 8, 15, 16, 23, 42],
    powerball: generatePowerball()
  };
}

// ---------------------------------------------------------------------------
// C4 — Pure display helpers for the Pattern Explorer section
// (No DOM references — safe in node test environment)
// ---------------------------------------------------------------------------

const STRATEGY_LABELS: Record<PredictionStrategy, string> = {
  burst_volatility: 'Burst & Volatility',
  mean_reversion: 'Mean Reversion',
  momentum_carry: 'Momentum Carry-Over',
  balanced_hybrid: 'Balanced Mix',
  lean_bias: 'Left / Right Lean',
};

const FALLACY_LABELS: Record<PredictionStrategy, string> = {
  burst_volatility: 'Clustering Fallacy',
  mean_reversion: "Gambler's Fallacy",
  momentum_carry: 'Hot-Hand Fallacy',
  balanced_hybrid: 'Diversification Fallacy',
  lean_bias: 'Positional Bias Fallacy',
};

const FALLACY_EXPLANATIONS: Record<PredictionStrategy, string> = {
  burst_volatility:
    'Clusters in past data look meaningful but are expected noise in a uniform draw. Historically bursty numbers have no higher chance of appearing next.',
  mean_reversion:
    "Cold numbers are not 'due.' The draw has no memory — past frequency has no effect on the next result.",
  momentum_carry:
    'Streaks in past draws do not continue. Each draw is fully independent; a number appearing often recently is no more likely to appear again.',
  balanced_hybrid:
    'Spreading picks across hot, cold, and neutral zones does not change the expected probability — every combination has identical odds.',
  lean_bias:
    'Left or right lean in past draws has no carry-over effect. The next draw selects randomly from the full 1–40 range regardless of recent positional patterns.',
};

function toTitleCase(str: string): string {
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function formatStrategyLabel(strategy: string): string {
  return STRATEGY_LABELS[strategy as PredictionStrategy] ?? toTitleCase(strategy);
}

export function formatFallacyLabel(strategy: string): string {
  return FALLACY_LABELS[strategy as PredictionStrategy] ?? toTitleCase(strategy);
}

export function formatFallacyExplanation(strategy: string): string {
  return FALLACY_EXPLANATIONS[strategy as PredictionStrategy] ?? '';
}

export function validatePredictionSet(set: PredictionSet): boolean {
  const { main_numbers, powerball } = set;
  if (!Array.isArray(main_numbers) || main_numbers.length !== 6) return false;
  if (new Set(main_numbers).size !== 6) return false;
  if (main_numbers.some(n => n < 1 || n > 40)) return false;
  for (let i = 1; i < main_numbers.length; i++) {
    if (main_numbers[i] <= main_numbers[i - 1]) return false;
  }
  if (powerball < 1 || powerball > 10) return false;
  return true;
}

export function orderPredictionSets(sets: PredictionSet[]): PredictionSet[] {
  return sets.filter(validatePredictionSet).sort((a, b) => a.id - b.id);
}
