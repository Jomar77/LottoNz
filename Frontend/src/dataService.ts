import { LotteryResult, PredictionsDocument, PredictionsWeightedDocument } from './types';

const DATA_URL = '/results.json';
const PREDICTIONS_URL = '/predictions.json';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function fetchLotteryData(): Promise<LotteryResult[]> {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching lottery data:', error);
    throw error;
  }
}

export async function fetchPredictions(): Promise<PredictionsDocument | null> {
  try {
    const response = await fetch(PREDICTIONS_URL);
    if (!response.ok) {
      console.warn(`fetchPredictions: ${response.status} — predictions unavailable`);
      return null;
    }
    return await response.json() as PredictionsDocument;
  } catch (error) {
    console.error('fetchPredictions: failed to parse predictions.json', error);
    return null;
  }
}

export interface StrategiesWeightedParams {
  lean: 'left' | 'right' | 'middle';
  spread: 'tight' | 'wide' | 'mixed';
  consecutive: boolean;
  count: number;
  dateFrom?: string;
  seed?: number;
}

export async function fetchStrategiesWeighted(
  params: StrategiesWeightedParams
): Promise<PredictionsWeightedDocument | null> {
  const query = new URLSearchParams({
    lean: params.lean,
    spread: params.spread,
    consecutive: String(params.consecutive),
    count: String(params.count),
  });
  if (params.dateFrom) query.set('date_from', params.dateFrom);
  if (params.seed !== undefined) query.set('seed', String(params.seed));

  try {
    const response = await fetch(`${API_BASE_URL}/predict/strategies/weighted?${query}`);
    if (!response.ok) {
      console.warn(`fetchStrategiesWeighted: ${response.status} — live API unavailable`);
      return null;
    }
    return await response.json() as PredictionsWeightedDocument;
  } catch (error) {
    console.error('fetchStrategiesWeighted: request failed — is `uvicorn api.main:app --reload` running?', error);
    return null;
  }
}
