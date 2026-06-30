import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchPredictions } from './dataService';

// Stub global fetch for each test
beforeEach(() => {
  vi.restoreAllMocks();
});

const sampleDoc = {
  draw_reference: 1875,
  generated_at: '2026-05-09T08:00:00Z',
  sets: [
    {
      id: 1,
      strategy: 'burst_volatility',
      main_numbers: [2, 5, 7, 11, 28, 35],
      powerball: 3,
      rationale: 'Test rationale.',
    },
  ],
  metadata: {
    total_draws_analyzed: 1874,
    date_range: '2001-02-17 to 2026-05-09',
    uniformity_confirmed: true,
    chi_square_p_main: 0.585,
    chi_square_p_powerball: 0.178,
  },
};

describe('fetchPredictions', () => {
  it('resolves to the parsed document on success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => sampleDoc,
    }));
    const result = await fetchPredictions();
    expect(result).toEqual(sampleDoc);
  });

  it('resolves to null on 404', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => { throw new Error('Not Found'); },
    }));
    const result = await fetchPredictions();
    expect(result).toBeNull();
  });

  it('resolves to null on invalid JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => { throw new SyntaxError('Unexpected token'); },
    }));
    const result = await fetchPredictions();
    expect(result).toBeNull();
  });
});
