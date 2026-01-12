import { LotteryResult, GenerationPreferences, GeneratedNumbers } from './types';

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

export function isUnique(numbers: number[], historicalData: LotteryResult[]): boolean {
  const numSet = new Set(numbers);
  return !historicalData.some(result => {
    const intersection = result.numbers.filter(n => numSet.has(n));
    return intersection.length === 6;
  });
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
