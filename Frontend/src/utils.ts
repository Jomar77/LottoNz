import { LotteryResult, GenerationPreferences, GeneratedNumbers } from './types';

export function calculateSpread(numbers: number[]): number {
  return Math.max(...numbers) - Math.min(...numbers);
}

export function hasConsecutive(numbers: number[]): boolean {
  const sorted = [...numbers].sort((a, b) => a - b);
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i + 1] - sorted[i] === 1) {
      return true;
    }
  }
  return false;
}

export function isUnique(numbers: number[], historicalData: LotteryResult[]): boolean {
  const numSet = new Set(numbers);
  for (const result of historicalData) {
    const resultSet = new Set(result.numbers);
    const intersection = [...numSet].filter(n => resultSet.has(n));
    if (intersection.length === 6) {
      return false;
    }
  }
  return true;
}

// Gaussian (normal) distribution using Box-Muller transform
function gaussianRandom(mean = 0, stddev = 1): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = Math.random(); // Must use uniform random for Box-Muller
  while (v === 0) v = Math.random(); // Must use uniform random for Box-Muller
  const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  return z * stddev + mean;
}

export function generatePowerball(): number {
  const val = Math.round(gaussianRandom(5.5, 2));
  if (val < 1) return 1;
  if (val > 10) return 10;
  return val;
}

function calculateFrequencies(historicalData: LotteryResult[]): Map<number, number> {
  const frequencies = new Map<number, number>();
  
  for (let i = 1; i <= 40; i++) {
    frequencies.set(i, 0);
  }
  
  for (const result of historicalData) {
    for (const num of result.numbers) {
      frequencies.set(num, (frequencies.get(num) || 0) + 1);
    }
  }
  
  return frequencies;
}

function applyLeaningWeight(num: number, leaning: string, baseWeight: number): number {
  if (leaning === 'left' && num <= 13) {
    return baseWeight * 2;
  } else if (leaning === 'middle' && num >= 15 && num <= 25) {
    return baseWeight * 2;
  } else if (leaning === 'right' && num >= 27) {
    return baseWeight * 2;
  }
  return baseWeight;
}

function weightedRandomChoice(weights: number[]): number {
  const totalWeight = weights.reduce((sum, w) => sum + w, 0);
  let random = Math.random() * totalWeight;
  
  for (let i = 0; i < weights.length; i++) {
    random -= weights[i];
    if (random <= 0) {
      return i + 1;
    }
  }
  
  return weights.length;
}

export function generateNumbers(
  historicalData: LotteryResult[],
  preferences: GenerationPreferences
): GeneratedNumbers {
  const frequencies = calculateFrequencies(historicalData);
  const maxAttempts = 1000;
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const numbers: number[] = [];
    const weights: number[] = [];
    
    for (let i = 1; i <= 40; i++) {
      const baseWeight = (frequencies.get(i) || 0) + 1;
      const weight = applyLeaningWeight(i, preferences.leaning, baseWeight);
      weights.push(weight);
    }
    
    while (numbers.length < 6) {
      const num = weightedRandomChoice(weights);
      if (!numbers.includes(num)) {
        numbers.push(num);
      }
    }
    
    const spread = calculateSpread(numbers);
    const hasConsec = hasConsecutive(numbers);
    
    const spreadValid = 
      (preferences.spread === 'tight' && spread <= 20) ||
      (preferences.spread === 'wide' && spread >= 15) ||
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
  
  const fallbackNumbers = [3, 12, 19, 27, 34, 38];
  return {
    numbers: fallbackNumbers,
    powerball: generatePowerball()
  };
}
