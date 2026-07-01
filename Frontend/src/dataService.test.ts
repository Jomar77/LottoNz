import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchPredictions, fetchStrategiesWeighted } from './dataService';

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

const sampleWeightedDoc = {
  draw_reference: 1875,
  generated_at: '2026-05-09T08:00:00Z',
  sets: [
    {
      id: 1,
      strategy: 'burst_volatility',
      main_numbers: [2, 5, 7, 11, 28, 35],
      powerball: 3,
      rationale: 'Test rationale.',
      constraint_satisfied: true,
    },
  ],
  metadata: {
    total_draws_analyzed: 1874,
    date_range: '2001-02-17 to 2026-05-09',
    uniformity_confirmed: true,
    chi_square_p_main: 0.585,
    chi_square_p_powerball: 0.178,
    applied_filters: {
      date_from: null,
      lean: 'middle',
      spread: 'mixed',
      consecutive: false,
      enforcement: 'active' as const,
    },
  },
};

describe('fetchStrategiesWeighted', () => {
  it('calls /predict/strategies/weighted with query params and resolves to the parsed document', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => sampleWeightedDoc,
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await fetchStrategiesWeighted({
      lean: 'left',
      spread: 'tight',
      consecutive: false,
      count: 3,
    });

    expect(result).toEqual(sampleWeightedDoc);
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain('/predict/strategies/weighted');
    expect(calledUrl).toContain('lean=left');
    expect(calledUrl).toContain('spread=tight');
    expect(calledUrl).toContain('consecutive=false');
    expect(calledUrl).toContain('count=3');
  });

  it('resolves to null on a non-200 response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new Error('should not be called'); },
    }));
    const result = await fetchStrategiesWeighted({ lean: 'middle', spread: 'mixed', consecutive: false, count: 1 });
    expect(result).toBeNull();
  });

  it('resolves to null on a network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    const result = await fetchStrategiesWeighted({ lean: 'middle', spread: 'mixed', consecutive: false, count: 1 });
    expect(result).toBeNull();
  });
});
