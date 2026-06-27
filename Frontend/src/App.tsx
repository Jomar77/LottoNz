import { useState, useEffect, useRef, useCallback, ChangeEvent } from 'react';
import { Search, Sparkles, TrendingUp, Settings, ChevronDown, ChevronUp, Pencil } from 'lucide-react';
import { fetchLotteryData } from './dataService';
import { findHistoricalMatch, generateNumbers } from './utils';
import { LotteryResult, GenerationPreferences, GeneratedNumbers } from './types';

const ITEM_H = 48; // picker item height in px
const VISIBLE = 5;  // visible rows in picker drum

function App() {
  const [data, setData] = useState<LotteryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatedList, setGeneratedList] = useState<GeneratedNumbers[]>([]);
  const [bulkCount, setBulkCount] = useState(1);
  const [bulkInputStr, setBulkInputStr] = useState('1');
  const [countBounce, setCountBounce] = useState(false);
  const [showPickerModal, setShowPickerModal] = useState(false);
  const [tempCount, setTempCount] = useState(1);
  const [manualNumbers, setManualNumbers] = useState('');
  const [manualCheckMessage, setManualCheckMessage] = useState<string | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<GenerationPreferences>({
    spread: 'wide',
    leaning: 'middle',
    consecutive: 'yes'
  });

  const scrollZoneRef = useRef<HTMLDivElement>(null);
  const pickerRef = useRef<HTMLDivElement>(null);

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

  // Scroll picker to saved position each time modal opens
  useEffect(() => {
    if (showPickerModal && pickerRef.current) {
      pickerRef.current.scrollTop = (tempCount - 1) * ITEM_H;
    }
  }, [showPickerModal]); // eslint-disable-line react-hooks/exhaustive-deps

  // Desktop: mouse-wheel on the scroll zone
  const adjustCount = useCallback((delta: number) => {
    setBulkCount(prev => {
      const next = Math.max(1, Math.min(50, prev + delta));
      setBulkInputStr(String(next));
      return next;
    });
    setCountBounce(true);
    setTimeout(() => setCountBounce(false), 180);
  }, []);

  useEffect(() => {
    const el = scrollZoneRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      adjustCount(e.deltaY < 0 ? 1 : -1);
    };
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, [adjustCount]);

  const handleCountInput = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '');
    setBulkInputStr(raw);
    const n = parseInt(raw, 10);
    if (!isNaN(n) && n >= 1 && n <= 50) setBulkCount(n);
  };

  const handleCountBlur = () => {
    const n = parseInt(bulkInputStr, 10);
    const clamped = isNaN(n) || n < 1 ? 1 : Math.min(50, n);
    setBulkCount(clamped);
    setBulkInputStr(String(clamped));
  };

  // Mobile iOS picker
  const openPicker = () => {
    setTempCount(bulkCount);
    setShowPickerModal(true);
  };

  const handlePickerScroll = () => {
    const el = pickerRef.current;
    if (!el) return;
    const index = Math.round(el.scrollTop / ITEM_H);
    setTempCount(Math.max(1, Math.min(50, index + 1)));
  };

  const confirmPicker = () => {
    setBulkCount(tempCount);
    setBulkInputStr(String(tempCount));
    setShowPickerModal(false);
  };

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
  const drumPadding = Math.floor(VISIBLE / 2) * ITEM_H; // 96px — centers first/last item

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-6xl mx-auto">
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

        {/* Two-column layout */}
        <div className="flex flex-col lg:flex-row gap-6 items-start">

          {/* Left column: main card */}
          <div className="flex-1 min-w-0">
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
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Spread</label>
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

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Leaning</label>
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

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Consecutive Numbers</label>
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

              {/* Manual History Check */}
              <div className="p-6">
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
            </div>
          </div>

          {/* Right column: Lucky Tickets side panel */}
          <div className="w-full lg:w-80 flex-shrink-0 lg:sticky lg:top-8">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
              {/* Panel header */}
              <div className="px-6 pt-5 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-highlight-blue" />
                  <h3 className="text-lg font-semibold text-gray-800">Lucky Tickets</h3>
                </div>
              </div>

              {/* ── Mobile counter: big number + Edit button ── */}
              <div className="lg:hidden p-6 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider text-center mb-4">
                  Number of Tickets
                </p>
                <div className="flex items-center justify-center gap-4">
                  <span
                    className="text-6xl font-bold text-gray-800"
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {bulkCount}
                  </span>
                  <button
                    onClick={openPicker}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-highlight-blue/10 text-highlight-blue text-sm font-semibold hover:bg-highlight-blue/20 active:scale-95 transition-all"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                    Edit
                  </button>
                </div>
              </div>

              {/* ── Desktop counter: ± buttons + mouse-wheel input ── */}
              <div className="hidden lg:block p-6 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider text-center mb-4">
                  Number of Tickets
                </p>
                <div
                  ref={scrollZoneRef}
                  className="flex items-center justify-center gap-5 cursor-ns-resize select-none"
                  title="Scroll to adjust"
                >
                  <button
                    onClick={() => adjustCount(-1)}
                    disabled={bulkCount <= 1}
                    className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 active:scale-95 disabled:opacity-25 flex items-center justify-center transition-all text-gray-600 font-bold text-lg leading-none"
                  >
                    −
                  </button>

                  <div className={`transition-transform duration-150 ease-out ${countBounce ? 'scale-125' : 'scale-100'}`}>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={bulkInputStr}
                      onChange={handleCountInput}
                      onBlur={handleCountBlur}
                      className="w-20 text-center text-5xl font-bold text-gray-800 bg-transparent border-none outline-none focus:ring-2 focus:ring-highlight-blue/30 rounded-lg cursor-text"
                      style={{ fontVariantNumeric: 'tabular-nums' }}
                      maxLength={2}
                    />
                  </div>

                  <button
                    onClick={() => adjustCount(1)}
                    disabled={bulkCount >= 50}
                    className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 active:scale-95 disabled:opacity-25 flex items-center justify-center transition-all text-gray-600 font-bold text-lg leading-none"
                  >
                    +
                  </button>
                </div>
                <p className="text-xs text-gray-400 text-center mt-3">
                  Scroll, click ±, or type · max 50
                </p>
              </div>

              {/* Generate button */}
              <div className="p-5 border-b border-gray-100">
                <button
                  onClick={handleGenerate}
                  disabled={loading || data.length === 0}
                  className="w-full py-4 bg-gradient-to-r from-base to-highlight-blue text-white text-lg font-bold rounded-xl hover:from-base/90 hover:to-highlight-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  {loading ? 'Loading Data...' : `Generate${bulkCount > 1 ? ` ${bulkCount} Tickets` : ''}`}
                </button>
              </div>

              {/* Generated tickets */}
              {generatedList.length > 0 && (
                <>
                  <div className="px-5 py-3 bg-gray-50">
                    <p className="text-xs font-semibold text-gray-500 text-center uppercase tracking-wider">
                      {generatedList.length > 1 ? `${generatedList.length} Tickets` : 'Your Lucky Numbers'}
                    </p>
                  </div>

                  {/* Desktop: compact scrollable list */}
                  <div className="hidden lg:block divide-y divide-gray-100 overflow-y-auto max-h-[52vh]">
                    {generatedList.map((ticket, ticketIdx) => (
                      <div key={ticketIdx} className="px-4 py-3">
                        {generatedList.length > 1 && (
                          <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                            Ticket {ticketIdx + 1}
                          </p>
                        )}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {ticket.numbers.map((num, idx) => (
                            <div
                              key={idx}
                              className="w-9 h-9 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-sm font-bold shadow-md animate-bounce"
                              style={{
                                animationDelay: `${(ticketIdx * 7 + idx) * 60}ms`,
                                animationDuration: '1s',
                                animationIterationCount: '1'
                              }}
                            >
                              {num}
                            </div>
                          ))}
                          <div
                            className="w-9 h-9 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-sm font-bold shadow-md border-2 border-white animate-bounce"
                            style={{
                              animationDelay: `${(ticketIdx * 7 + 6) * 60}ms`,
                              animationDuration: '1s',
                              animationIterationCount: '1'
                            }}
                          >
                            {ticket.powerball}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Mobile: full-width cards with large balls */}
                  <div className="lg:hidden p-4 space-y-4">
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
                              style={{
                                animationDelay: `${(ticketIdx * 7 + idx) * 60}ms`,
                                animationDuration: '1s',
                                animationIterationCount: '1'
                              }}
                            >
                              {num}
                            </div>
                          ))}
                          <div
                            className="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-xl font-bold shadow-lg border-4 border-white animate-bounce"
                            style={{
                              animationDelay: `${(ticketIdx * 7 + 6) * 60}ms`,
                              animationDuration: '1s',
                              animationIterationCount: '1'
                            }}
                          >
                            {ticket.powerball}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-white/70 text-sm">
          <p>Based on {data.length} historical draws</p>
        </div>
      </div>

      {/* ── iOS-style picker modal (mobile only) ── */}
      {showPickerModal && (
        <div className="lg:hidden fixed inset-0 z-50 flex items-end">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowPickerModal(false)}
          />

          {/* Bottom sheet */}
          <div className="relative w-full bg-white rounded-t-3xl shadow-2xl">
            {/* Drag handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            {/* Header row */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <button
                onClick={() => setShowPickerModal(false)}
                className="text-gray-500 font-medium text-sm px-1 py-1"
              >
                Cancel
              </button>
              <h3 className="font-semibold text-gray-800 text-base">Number of Tickets</h3>
              <button
                onClick={confirmPicker}
                className="text-highlight-blue font-semibold text-sm px-1 py-1"
              >
                Done
              </button>
            </div>

            {/* Drum picker */}
            <div
              className="relative overflow-hidden"
              style={{ height: ITEM_H * VISIBLE }}
            >
              {/* Center selection bar */}
              <div
                className="absolute inset-x-8 bg-gray-100 rounded-xl pointer-events-none z-10"
                style={{ top: drumPadding, height: ITEM_H }}
              />

              {/* Scrollable number list */}
              <div
                ref={pickerRef}
                onScroll={handlePickerScroll}
                className="picker-scroll h-full overflow-y-scroll snap-y snap-mandatory"
                style={{
                  scrollbarWidth: 'none',
                  msOverflowStyle: 'none',
                  paddingTop: drumPadding,
                  paddingBottom: drumPadding,
                }}
              >
                {Array.from({ length: 50 }, (_, i) => i + 1).map(n => (
                  <div
                    key={n}
                    className={`snap-center flex items-center justify-center font-semibold transition-all duration-100 select-none ${
                      n === tempCount
                        ? 'text-gray-900 text-3xl'
                        : 'text-gray-400 text-xl'
                    }`}
                    style={{ height: ITEM_H }}
                  >
                    {n}
                  </div>
                ))}
              </div>

              {/* Top fade */}
              <div
                className="absolute inset-x-0 top-0 pointer-events-none z-20 bg-gradient-to-b from-white via-white/70 to-transparent"
                style={{ height: drumPadding }}
              />
              {/* Bottom fade */}
              <div
                className="absolute inset-x-0 bottom-0 pointer-events-none z-20 bg-gradient-to-t from-white via-white/70 to-transparent"
                style={{ height: drumPadding }}
              />
            </div>

            {/* Safe-area spacer */}
            <div className="h-8" />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
