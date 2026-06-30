import { LotteryResult, PredictionsDocument } from './types';

const DATA_URL = '/results.json';
const PREDICTIONS_URL = '/predictions.json';

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
