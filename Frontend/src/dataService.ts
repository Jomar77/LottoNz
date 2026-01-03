import { LotteryResult } from './types';

const DATA_URL = import.meta.env.PROD 
  ? 'https://raw.githubusercontent.com/yourusername/LottoNz/main/data/results.json'
  : '/results.json';

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
