import { useState, useEffect } from 'react';
import { Search, Sparkles, TrendingUp, Settings, ChevronDown, ChevronUp } from 'lucide-react';
import { fetchLotteryData } from './dataService';
import { findHistoricalMatch, generateNumbers } from './utils';
import { LotteryResult, GenerationPreferences, GeneratedNumbers } from './types';

function App() {
  const [data, setData] = useState<LotteryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatedList, setGeneratedList] = useState<GeneratedNumbers[]>([]);
  const [bulkCount, setBulkCount] = useState(1);
  const [manualNumbers, setManualNumbers] = useState('');
  const [manualCheckMessage, setManualCheckMessage] = useState<string | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<GenerationPreferences>({
    spread: 'wide',
    leaning: 'middle',
    consecutive: 'yes'
  });

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const results = await fetchLotteryData();
        setData(results);
        setError(null);
      } catch (err) {
        setError('Failed to load lottery data. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleGenerate = () => {
    if (data.length === 0) return;
    const tickets: GeneratedNumbers[] = [];
    for (let i = 0; i < bulkCount; i++) {
      tickets.push(generateNumbers(data, preferences));
    }
    setGeneratedList(tickets);
  };

  const handleManualCheck = () => {
    if (data.length === 0) {
      setManualCheckMessage('Historical data is still loading.');
      return;
    }

    const parsedNumbers = manualNumbers
      .trim()
      .split(/[\s,]+/)
      .filter(value => value !== '')
      .map(value => Number(value))
      .filter(value => !Number.isNaN(value) && value !== 0);

    if (parsedNumbers.length !== 6) {
      setManualCheckMessage('Enter exactly 6 numbers separated by commas or spaces.');
      return;
    }

    if (new Set(parsedNumbers).size !== 6) {
      setManualCheckMessage('Your selection has duplicate numbers. Please enter 6 unique numbers.');
      return;
    }

    const outOfRange = parsedNumbers.find(num => num < 1 || num > 40);
    if (outOfRange !== undefined) {
      setManualCheckMessage('Numbers must be between 1 and 40.');
      return;
    }

    const match = findHistoricalMatch(parsedNumbers, data);
    if (match) {
      setManualCheckMessage(`Exact duplicate found in the dataset on ${match.date}.`);
      return;
    }

    setManualCheckMessage('No exact duplicate found in the historical dataset.');
  };

  const latestResult = data.length > 0 ? data[0] : null;

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Sparkles className="w-12 h-12 text-base/60" />
            LottoNz Smart Picker
            <Sparkles className="w-12 h-12 text-highlight-blue/60" />
          </h1>
          <p className="text-white text-lg">Weighted number generation based on historical data</p>
        </div>

        {/* Latest Result Card */}
        {latestResult && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-white/20 shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-base/60" />
              <h2 className="text-xl font-semibold text-white">Latest Result</h2>
              <span className="text-highlight-blue/40 ml-auto">{latestResult.date}</span>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              {latestResult.numbers.map((num, idx) => (
                <div
                  key={idx}
                  className="w-14 h-14 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-xl font-bold shadow-lg"
                >
                  {num}
                </div>
              ))}
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-xl font-bold shadow-lg border-2 border-white">
                {latestResult.powerball}
              </div>
            </div>
          </div>
        )}

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Preferences Section */}
          <div className="border-b border-gray-200">
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-highlight-blue" />
                <span className="font-semibold text-gray-700">Generation Preferences</span>
              </div>
              {showPreferences ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>

            {showPreferences && (
              <div className="px-6 pb-6 pt-2 bg-gray-50 space-y-4">
                {/* Spread */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Spread
                  </label>
                  <div className="flex gap-2">
                    {(['tight', 'wide', 'mixed'] as const).map((option) => (
                      <button
                        key={option}
                        onClick={() => setPreferences({ ...preferences, spread: option })}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                          preferences.spread === option
                            ? 'bg-base text-white shadow-md'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                      >
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Leaning */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Leaning
                  </label>
                  <div className="flex gap-2">
                    {(['left', 'middle', 'right'] as const).map((option) => (
                      <button
                        key={option}
                        onClick={() => setPreferences({ ...preferences, leaning: option })}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                          preferences.leaning === option
                            ? 'bg-highlight-blue text-white shadow-md'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                      >
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Consecutive */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Consecutive Numbers
                  </label>
                  <div className="flex gap-2">
                    {(['yes', 'no'] as const).map((option) => (
                      <button
                        key={option}
                        onClick={() => setPreferences({ ...preferences, consecutive: option })}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                          preferences.consecutive === option
                            ? 'bg-base text-white shadow-md'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                      >
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bulk Count + Generate */}
          <div className="p-6 space-y-3">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Number of tickets
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 5, 10, 20].map((n) => (
                  <button
                    key={n}
                    onClick={() => setBulkCount(n)}
                    className={`w-10 h-10 rounded-lg font-semibold text-sm transition-all ${
                      bulkCount === n
                        ? 'bg-base text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={handleGenerate}
              disabled={loading || data.length === 0}
              className="w-full py-4 bg-gradient-to-r from-base to-highlight-blue text-white text-xl font-bold rounded-xl hover:from-base/90 hover:to-highlight-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? 'Loading Data...' : `Generate ${bulkCount > 1 ? `${bulkCount} Tickets` : 'Lucky Numbers'}`}
            </button>
          </div>

          {/* Manual History Check */}
          <div className="px-6 pb-6">
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Search className="w-5 h-5 text-highlight-blue" />
                <h3 className="text-lg font-semibold text-gray-800">Check Your Own Numbers</h3>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Enter 6 main numbers to see whether the exact combination already exists in the dataset.
              </p>
              <div className="flex flex-col gap-3">
                <input
                  type="text"
                  value={manualNumbers}
                  onChange={(event) => setManualNumbers(event.target.value)}
                  placeholder="Example: 3, 7, 12, 18, 24, 31"
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-800 placeholder:text-gray-400 focus:border-highlight-blue focus:outline-none focus:ring-2 focus:ring-highlight-blue/20"
                />
                <button
                  onClick={handleManualCheck}
                  disabled={loading || data.length === 0}
                  className="w-full rounded-lg bg-gray-900 px-4 py-3 font-semibold text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Check Against Dataset
                </button>
              </div>
              {manualCheckMessage && (
                <div className="mt-4 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
                  {manualCheckMessage}
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-6 pb-6">
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            </div>
          )}

          {/* Generated Numbers Display */}
          {generatedList.length > 0 && (
            <div className="px-6 pb-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 text-center">
                {generatedList.length > 1 ? `Your ${generatedList.length} Lucky Tickets` : 'Your Lucky Numbers'}
              </h3>
              {generatedList.map((ticket, ticketIdx) => (
                <div
                  key={ticketIdx}
                  className="bg-gradient-to-br from-base/10 to-highlight-blue/10 rounded-xl p-4 border-2 border-base/20"
                >
                  {generatedList.length > 1 && (
                    <p className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wider">
                      Ticket {ticketIdx + 1}
                    </p>
                  )}
                  <div className="flex items-center justify-center gap-3 flex-wrap">
                    {ticket.numbers.map((num, idx) => (
                      <div
                        key={idx}
                        className="w-14 h-14 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-xl font-bold shadow-lg animate-bounce"
                        style={{ animationDelay: `${(ticketIdx * 7 + idx) * 60}ms`, animationDuration: '1s', animationIterationCount: '1' }}
                      >
                        {num}
                      </div>
                    ))}
                    <div
                      className="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-xl font-bold shadow-lg border-4 border-white animate-bounce"
                      style={{ animationDelay: `${(ticketIdx * 7 + 6) * 60}ms`, animationDuration: '1s', animationIterationCount: '1' }}
                    >
                      {ticket.powerball}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-white/70 text-sm">
          <p>Based on {data.length} historical draws</p>
        </div>
      </div>
    </div>
  );
}

export default App;
