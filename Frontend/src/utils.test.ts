import { describe, it, expect } from 'vitest';
import {
  validatePredictionSet,
  formatStrategyLabel,
  formatFallacyLabel,
  formatFallacyExplanation,
  orderPredictionSets,
} from './utils';
import type { PredictionSet } from './types';

// --- C1 bootstrap ---------------------------------------------------------
describe('vitest bootstrap', () => {
  it('runs', () => {
    expect(1 + 1).toBe(2);
  });
});

// --- C4: validatePredictionSet -------------------------------------------
const validSet: PredictionSet = {
  id: 1,
  strategy: 'burst_volatility',
  main_numbers: [2, 5, 7, 11, 28, 35],
  powerball: 3,
  rationale: 'Test rationale.',
};

describe('validatePredictionSet', () => {
  it('accepts a valid set', () => {
    expect(validatePredictionSet(validSet)).toBe(true);
  });

  it('rejects fewer than 6 main numbers', () => {
    expect(validatePredictionSet({ ...validSet, main_numbers: [2, 5, 7, 11, 28] })).toBe(false);
  });

  it('rejects out-of-range main numbers', () => {
    expect(validatePredictionSet({ ...validSet, main_numbers: [0, 5, 7, 11, 28, 35] })).toBe(false);
    expect(validatePredictionSet({ ...validSet, main_numbers: [2, 5, 7, 11, 28, 41] })).toBe(false);
  });

  it('rejects duplicate main numbers', () => {
    expect(validatePredictionSet({ ...validSet, main_numbers: [2, 2, 7, 11, 28, 35] })).toBe(false);
  });

  it('rejects unsorted main numbers', () => {
    expect(validatePredictionSet({ ...validSet, main_numbers: [35, 5, 7, 11, 28, 2] })).toBe(false);
  });

  it('rejects powerball out of 1-10', () => {
    expect(validatePredictionSet({ ...validSet, powerball: 0 })).toBe(false);
    expect(validatePredictionSet({ ...validSet, powerball: 11 })).toBe(false);
  });
});

// --- C4: formatStrategyLabel ---------------------------------------------
describe('formatStrategyLabel', () => {
  it('maps all five known strategies', () => {
    expect(formatStrategyLabel('burst_volatility')).toBe('Burst & Volatility');
    expect(formatStrategyLabel('mean_reversion')).toBe('Mean Reversion');
    expect(formatStrategyLabel('momentum_carry')).toBe('Momentum Carry-Over');
    expect(formatStrategyLabel('balanced_hybrid')).toBe('Balanced Mix');
    expect(formatStrategyLabel('lean_bias')).toBe('Left / Right Lean');
  });

  it('title-cases unknown strategies as fallback', () => {
    expect(formatStrategyLabel('some_new_strategy')).toBe('Some New Strategy');
  });
});

// --- C4: formatFallacyLabel + formatFallacyExplanation (educational framing)
describe('formatFallacyLabel', () => {
  it('maps strategies to their named fallacy', () => {
    expect(formatFallacyLabel('mean_reversion')).toBe("Gambler's Fallacy");
    expect(formatFallacyLabel('momentum_carry')).toBe('Hot-Hand Fallacy');
    expect(formatFallacyLabel('burst_volatility')).toBe('Clustering Fallacy');
    expect(formatFallacyLabel('balanced_hybrid')).toBe('Diversification Fallacy');
    expect(formatFallacyLabel('lean_bias')).toBe('Positional Bias Fallacy');
  });

  it('returns the strategy label for unknown strategies', () => {
    expect(formatFallacyLabel('unknown')).toBe('Unknown');
  });
});

describe('formatFallacyExplanation', () => {
  it('returns a non-empty explanation for each strategy', () => {
    const strategies = ['burst_volatility', 'mean_reversion', 'momentum_carry', 'balanced_hybrid', 'lean_bias'] as const;
    for (const s of strategies) {
      const ex = formatFallacyExplanation(s);
      expect(ex.length).toBeGreaterThan(10);
      // Must not contain hype words
      expect(ex.toLowerCase()).not.toMatch(/\b(guaranteed|best|win|due to hit|will)\b/);
    }
  });
});

// --- C4: orderPredictionSets ---------------------------------------------
describe('orderPredictionSets', () => {
  it('orders by id ascending', () => {
    const sets: PredictionSet[] = [
      { ...validSet, id: 3, strategy: 'momentum_carry' },
      { ...validSet, id: 1, strategy: 'burst_volatility' },
      { ...validSet, id: 2, strategy: 'mean_reversion' },
    ];
    const result = orderPredictionSets(sets);
    expect(result.map(s => s.id)).toEqual([1, 2, 3]);
  });

  it('drops malformed sets', () => {
    const bad = { ...validSet, main_numbers: [1, 2, 3] }; // only 3 numbers
    const result = orderPredictionSets([validSet, bad]);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(1);
  });

  it('returns empty array when all sets are malformed', () => {
    const bad = { ...validSet, powerball: 99 };
    expect(orderPredictionSets([bad])).toEqual([]);
  });
});
