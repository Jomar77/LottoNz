import { useState, useEffect } from 'react';
import { Sparkles, TrendingUp, Settings, ChevronDown, ChevronUp } from 'lucide-react';
import { fetchLotteryData } from './dataService';
import { generateNumbers } from './utils';
import { LotteryResult, GenerationPreferences, GeneratedNumbers } from './types';

function App() {
  const [data, setData] = useState<LotteryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatedNumbers, setGeneratedNumbers] = useState<GeneratedNumbers | null>(null);
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
    const numbers = generateNumbers(data, preferences);
    setGeneratedNumbers(numbers);
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
          <p className="text-highlight-blue/30 text-lg">Weighted number generation based on historical data</p>
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

          {/* Generate Button */}
          <div className="p-6">
            <button
              onClick={handleGenerate}
              disabled={loading || data.length === 0}
              className="w-full py-4 bg-gradient-to-r from-base to-highlight-blue text-white text-xl font-bold rounded-xl hover:from-base/90 hover:to-highlight-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? 'Loading Data...' : 'Generate Lucky Numbers'}
            </button>
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
          {generatedNumbers && (
            <div className="px-6 pb-6">
              <div className="bg-gradient-to-br from-base/10 to-highlight-blue/10 rounded-xl p-6 border-2 border-base/20">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
                  Your Lucky Numbers
                </h3>
                <div className="flex items-center justify-center gap-3 flex-wrap">
                  {generatedNumbers.numbers.map((num, idx) => (
                    <div
                      key={idx}
                      className="w-16 h-16 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-2xl font-bold shadow-lg animate-bounce"
                      style={{ animationDelay: `${idx * 100}ms`, animationDuration: '1s', animationIterationCount: '1' }}
                    >
                      {num}
                    </div>
                  ))}
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-2xl font-bold shadow-lg border-4 border-white animate-bounce"
                    style={{ animationDelay: '600ms', animationDuration: '1s', animationIterationCount: '1' }}
                  >
                    {generatedNumbers.powerball}
                  </div>
                </div>
              </div>
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
