import { useState, useEffect, useRef, useCallback, ChangeEvent } from 'react';
import { Search, Sparkles, TrendingUp, Settings, Pencil, Flame, Zap, RotateCcw, Atom, Shuffle, Loader2, AlertTriangle, Wifi } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { fetchLotteryData, fetchStrategiesWeighted } from './dataService';
import { findHistoricalMatch, generateNumbers, generateWithStrategies } from './utils';
import type { LotteryResult, GenerationPreferences, GeneratedNumbers, StrategyId, EngineType } from './types';
import { CookieBanner } from './components/CookieBanner';
import { PrivacyModal } from './components/PrivacyModal';

const ITEM_H = 48;
const VISIBLE = 5;

interface StrategyDef {
  id: StrategyId;
  name: string;
  desc: string;
  color: string;
  Icon: LucideIcon;
}

const STRATEGY_DEFS: StrategyDef[] = [
  { id: 'hot',     name: 'Hot Streak',   desc: 'Leans on the most-drawn balls across all historical draws.', color: '#fe8302', Icon: Flame },
  { id: 'recent',  name: 'Recent Form',  desc: 'Recency-weighted — the last year of draws dominates.',       color: '#0190d6', Icon: Zap },
  { id: 'overdue', name: 'Overdue',      desc: 'Targets the cold balls that are statistically due.',          color: '#329c52', Icon: RotateCcw },
  { id: 'decay',   name: 'Decay Sample', desc: '40 exponential sources — the 6 fastest emissions win.',       color: '#9785b8', Icon: Atom },
  { id: 'random',  name: 'Pure Random',  desc: 'Crypto quick pick — every ball equally likely.',              color: '#6b7280', Icon: Shuffle },
];

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
  const [engine, setEngine] = useState<EngineType>('gaussian');
  const [selectedStrategies, setSelectedStrategies] = useState<StrategyId[]>(['hot']);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [liveMeta, setLiveMeta] = useState<Array<{ strategy: string; constraintSatisfied: boolean } | null>>([]);
  const [preferences, setPreferences] = useState<GenerationPreferences>({
    spread: 'wide',
    leaning: 'middle',
    consecutive: 'yes',
  });
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [gdprDismissed, setGdprDismissed] = useState(() => localStorage.getItem('lotto_gdpr_dismissed') === 'true');
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

  useEffect(() => {
    if (showPickerModal && pickerRef.current) {
      pickerRef.current.scrollTop = (tempCount - 1) * ITEM_H;
    }
  }, [showPickerModal]); // eslint-disable-line react-hooks/exhaustive-deps

  const adjustCount = useCallback((delta: number) => {
    setBulkCount(prev => {
      const next = Math.max(1, Math.min(20, prev + delta));
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
    if (!isNaN(n) && n >= 1 && n <= 20) setBulkCount(n);
  };

  const handleCountBlur = () => {
    const n = parseInt(bulkInputStr, 10);
    const clamped = isNaN(n) || n < 1 ? 1 : Math.min(20, n);
    setBulkCount(clamped);
    setBulkInputStr(String(clamped));
  };

  const openPicker = () => {
    setTempCount(bulkCount);
    setShowPickerModal(true);
  };

  const handlePickerScroll = () => {
    const el = pickerRef.current;
    if (!el) return;
    const index = Math.round(el.scrollTop / ITEM_H);
    setTempCount(Math.max(1, Math.min(20, index + 1)));
  };

  const confirmPicker = () => {
    setBulkCount(tempCount);
    setBulkInputStr(String(tempCount));
    setShowPickerModal(false);
  };

  const toggleStrategy = (id: StrategyId) => {
    setSelectedStrategies(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    if (data.length === 0) return;

    if (engine === 'live') {
      setLiveLoading(true);
      setLiveError(null);
      const doc = await fetchStrategiesWeighted({
        lean: preferences.leaning,
        spread: preferences.spread,
        consecutive: preferences.consecutive === 'yes',
        count: Math.min(bulkCount, 5),
      });
      setLiveLoading(false);
      if (!doc) {
        setLiveError(
          'Could not reach the live prediction API. Is it running? Start it with: ' +
          'python -m uvicorn api.main:app --reload'
        );
        return;
      }
      setGeneratedList(doc.sets.map(s => ({ numbers: s.main_numbers, powerball: s.powerball })));
      setLiveMeta(doc.sets.map(s => ({ strategy: s.strategy, constraintSatisfied: s.constraint_satisfied })));
      return;
    }

    setLiveError(null);
    const tickets: GeneratedNumbers[] = [];
    for (let i = 0; i < bulkCount; i++) {
      if (engine === 'strategy') {
        tickets.push(generateWithStrategies(data, selectedStrategies, preferences));
      } else {
        tickets.push(generateNumbers(data, preferences));
      }
    }
    setGeneratedList(tickets);
    setLiveMeta([]);
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
  const drumPadding = Math.floor(VISIBLE / 2) * ITEM_H;

  const activeDef = engine === 'strategy'
    ? STRATEGY_DEFS.find(d => selectedStrategies.includes(d.id)) ?? null
    : null;

  const segBtn = (active: boolean, activeClass: string) =>
    `px-4 py-1.5 rounded-md text-sm font-semibold transition-all ${active ? activeClass : 'bg-transparent text-gray-500 hover:text-gray-700'}`;

  const prefBtn = (active: boolean, color: 'base' | 'blue') =>
    `flex-1 py-2 px-4 rounded-lg font-medium text-sm transition-all border ${
      active
        ? color === 'base' ? 'bg-base text-white border-base shadow-sm' : 'bg-highlight-blue text-white border-highlight-blue shadow-sm'
        : 'bg-white text-gray-700 border-gray-300'
    }`;

  const prefBtnSm = (active: boolean, color: 'base' | 'blue') =>
    `flex-1 py-1.5 px-3 rounded-lg text-sm font-medium transition-all border ${
      active
        ? color === 'base' ? 'bg-base text-white border-base shadow-sm' : 'bg-highlight-blue text-white border-highlight-blue shadow-sm'
        : 'bg-white text-gray-700 border-gray-300'
    }`;

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

        {/* Main layout */}
        <div className="flex flex-col lg:flex-row gap-6">

          {/* Lucky Tickets — left on desktop */}
          <div className="order-2 lg:order-1 w-full lg:w-[28rem] flex-shrink-0 lg:sticky lg:top-8 lg:h-[calc(100vh-4rem)]">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden lg:h-full lg:flex lg:flex-col">

              {/* Panel header */}
              <div className="px-6 pt-5 pb-4 border-b border-gray-100 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-highlight-blue" />
                  <h3 className="text-lg font-semibold text-gray-800">Lucky Tickets</h3>
                </div>
              </div>

              {/* Mobile counter */}
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

              {/* Desktop counter */}
              <div className="hidden lg:block p-6 border-b border-gray-100 flex-shrink-0">
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
                    disabled={bulkCount >= 20}
                    className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 active:scale-95 disabled:opacity-25 flex items-center justify-center transition-all text-gray-600 font-bold text-lg leading-none"
                  >
                    +
                  </button>
                </div>
                <p className="text-xs text-gray-400 text-center mt-3">
                  Scroll, click ±, or type · max 20
                </p>
              </div>

              {/* Generate button */}
              <div className="p-5 border-b border-gray-100 flex-shrink-0">
                <button
                  onClick={handleGenerate}
                  disabled={loading || liveLoading || data.length === 0}
                  className="w-full py-4 bg-gradient-to-r from-base to-highlight-blue text-white text-lg font-bold rounded-xl hover:from-base/90 hover:to-highlight-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2"
                >
                  {liveLoading && <Loader2 className="w-5 h-5 animate-spin" />}
                  {loading
                    ? 'Loading Data...'
                    : liveLoading
                    ? 'Generating...'
                    : `Generate${bulkCount > 1 ? ` ${bulkCount} Tickets` : ''}`}
                </button>
                {liveError && (
                  <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3.5 py-3 text-xs text-red-700">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{liveError}</span>
                  </div>
                )}
              </div>

              {/* Generated tickets */}
              {generatedList.length > 0 && (
                <div className="flex-1 min-h-0 flex flex-col">
                  {/* Label with engine indicator */}
                  <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-center gap-2 flex-shrink-0">
                    {engine === 'gaussian' ? (
                      <Settings className="w-4 h-4 text-base" />
                    ) : engine === 'live' ? (
                      <Wifi className="w-4 h-4 text-highlight-blue" />
                    ) : activeDef ? (
                      <activeDef.Icon size={16} color={activeDef.color} />
                    ) : (
                      <Shuffle className="w-4 h-4 text-gray-400" />
                    )}
                    <p className="text-xs font-semibold text-gray-500 text-center uppercase tracking-wider">
                      {generatedList.length > 1 ? `${generatedList.length} Tickets` : 'Your Lucky Numbers'}
                    </p>
                  </div>

                  {/* Desktop: scrollable number balls */}
                  <div className="hidden lg:block flex-1 overflow-y-auto px-4 py-3 space-y-2.5">
                    {generatedList.map((ticket, ticketIdx) => (
                      <div key={ticketIdx} className="rounded-xl bg-gray-50 px-3 py-2.5">
                        <div className="flex items-center gap-2.5">
                          <span className="text-sm font-semibold text-gray-400 w-5 flex-shrink-0 tabular-nums text-right">
                            {ticketIdx + 1}
                          </span>
                          <div className="flex items-center gap-2 flex-1">
                            {ticket.numbers.map((num, idx) => (
                              <span
                                key={idx}
                                className="w-10 h-10 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-base font-bold shadow-sm tabular-nums"
                              >
                                {num}
                              </span>
                            ))}
                            <span className="w-10 h-10 rounded-full bg-gradient-to-br from-accent to-accent flex items-center justify-center text-white text-base font-bold shadow-md border-2 border-white tabular-nums">
                              {ticket.powerball}
                            </span>
                          </div>
                        </div>
                        {liveMeta[ticketIdx] && (
                          <div className="flex items-center gap-1.5 mt-1.5 pl-7.5 ml-5">
                            <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">
                              {liveMeta[ticketIdx]!.strategy.replace(/_/g, ' ')}
                            </span>
                            {!liveMeta[ticketIdx]!.constraintSatisfied && (
                              <span className="inline-flex items-center gap-0.5 text-[11px] font-medium text-amber-600">
                                <AlertTriangle className="w-3 h-3" /> constraints not fully met
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Mobile: full-width cards */}
                  <div className="lg:hidden p-4 space-y-4">
                    {generatedList.map((ticket, ticketIdx) => (
                      <div
                        key={ticketIdx}
                        className="bg-gradient-to-br from-base/10 to-highlight-blue/10 rounded-xl p-4 border-2 border-base/20"
                      >
                        <p className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wider">
                          Ticket {ticketIdx + 1}
                          {liveMeta[ticketIdx] && (
                            <span className="ml-2 normal-case text-gray-400 font-medium">
                              — {liveMeta[ticketIdx]!.strategy.replace(/_/g, ' ')}
                              {!liveMeta[ticketIdx]!.constraintSatisfied && (
                                <span className="ml-1 text-amber-600">⚠ unmet constraints</span>
                              )}
                            </span>
                          )}
                        </p>
                        <div className="flex items-center justify-center gap-3 flex-wrap">
                          {ticket.numbers.map((num, idx) => (
                            <div
                              key={idx}
                              className="w-14 h-14 rounded-full bg-gradient-to-br from-base to-base flex items-center justify-center text-white text-xl font-bold shadow-lg animate-bounce"
                              style={{
                                animationDelay: `${(ticketIdx * 7 + idx) * 60}ms`,
                                animationDuration: '1s',
                                animationIterationCount: '1',
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
                              animationIterationCount: '1',
                            }}
                          >
                            {ticket.powerball}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right column */}
          <div className="order-1 lg:order-2 flex-1 min-w-0 flex flex-col gap-6 lg:sticky lg:top-8 lg:h-[calc(100vh-4rem)]">

            {/* Latest Result */}
            {latestResult && (
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl flex-shrink-0">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-white/60" />
                  <h2 className="text-xl font-semibold text-white">Latest Result</h2>
                  <span className="text-white/50 ml-auto text-sm">{latestResult.date}</span>
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
                <p className="text-white/40 text-xs mt-4">Based on {data.length} historical draws</p>
              </div>
            )}

            {/* Generation Engine card */}
            <div className="lg:flex-1 lg:min-h-0">
              <div className="bg-white rounded-2xl shadow-2xl overflow-y-auto lg:h-full flex flex-col">

                {/* Engine header with segmented toggle */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3 flex-shrink-0">
                  <Settings className="w-5 h-5 text-highlight-blue" />
                  <span className="font-semibold text-gray-700">Generation Engine</span>
                  <div className="ml-auto flex bg-gray-100 rounded-lg p-1 gap-1">
                    <button
                      onClick={() => setEngine('gaussian')}
                      className={segBtn(engine === 'gaussian', 'bg-base text-white shadow-sm')}
                    >
                      Bell Curve
                    </button>
                    <button
                      onClick={() => setEngine('strategy')}
                      className={segBtn(engine === 'strategy', 'bg-highlight-blue text-white shadow-sm')}
                    >
                      Blend
                    </button>
                    <button
                      onClick={() => setEngine('live')}
                      className={segBtn(engine === 'live', 'bg-highlight-blue text-white shadow-sm')}
                    >
                      Strategies
                    </button>
                  </div>
                </div>

                {/* Bell Curve panel */}
                {engine === 'gaussian' && (
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex flex-col gap-3.5">
                    <p className="text-xs text-gray-500 leading-relaxed">
                      Hybrid Gaussian weighting over historical frequency. Shape the bell curve, then generate.
                    </p>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Spread</label>
                      <div className="flex gap-2 flex-1">
                        {(['tight', 'wide', 'mixed'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, spread: opt })} className={prefBtn(preferences.spread === opt, 'base')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Leaning</label>
                      <div className="flex gap-2 flex-1">
                        {(['left', 'middle', 'right'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, leaning: opt })} className={prefBtn(preferences.leaning === opt, 'blue')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Consecutive Numbers</label>
                      <div className="flex gap-2 flex-1">
                        {(['yes', 'no'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, consecutive: opt })} className={prefBtn(preferences.consecutive === opt, 'base')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Blend panel (client-side strategy mix) */}
                {engine === 'strategy' && (
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex flex-col gap-2.5">
                    <p className="text-xs text-gray-500 leading-relaxed">
                      Check any philosophies to blend — their weightings combine into one model for every ticket you generate.
                    </p>
                    {STRATEGY_DEFS.map(({ id, name, desc, color, Icon }) => {
                      const selected = selectedStrategies.includes(id);
                      return (
                        <button
                          key={id}
                          onClick={() => toggleStrategy(id)}
                          className="flex items-center gap-3.5 w-full text-left px-3.5 py-3 rounded-xl cursor-pointer transition-all"
                          style={{
                            background: selected ? `${color}14` : '#fff',
                            border: `2px solid ${selected ? color : '#e5e7eb'}`,
                          }}
                        >
                          <span
                            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                            style={{ background: `${color}1f` }}
                          >
                            <Icon size={20} color={color} />
                          </span>
                          <span className="flex-1 min-w-0">
                            <span className="block text-sm font-semibold text-gray-800">{name}</span>
                            <span className="block text-xs text-gray-500 mt-0.5 leading-snug">{desc}</span>
                          </span>
                          <span
                            className="w-5 h-5 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0 transition-all"
                            style={{
                              background: selected ? color : '#fff',
                              border: `2px solid ${selected ? color : '#d1d5db'}`,
                              color: selected ? '#fff' : 'transparent',
                            }}
                          >
                            ✓
                          </span>
                        </button>
                      );
                    })}

                    {/* Refine Weighting */}
                    <div className="mt-1.5 pt-3.5 border-t border-gray-200 flex flex-col gap-2.5">
                      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Refine Weighting</span>
                      <div className="flex items-center gap-3.5">
                        <label className="w-28 flex-shrink-0 text-sm font-medium text-gray-700">Leaning</label>
                        <div className="flex gap-1.5 flex-1">
                          {(['left', 'middle', 'right'] as const).map(opt => (
                            <button key={opt} onClick={() => setPreferences({ ...preferences, leaning: opt })} className={prefBtnSm(preferences.leaning === opt, 'blue')}>
                              {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-3.5">
                        <label className="w-28 flex-shrink-0 text-sm font-medium text-gray-700">Spread</label>
                        <div className="flex gap-1.5 flex-1">
                          {(['tight', 'wide', 'mixed'] as const).map(opt => (
                            <button key={opt} onClick={() => setPreferences({ ...preferences, spread: opt })} className={prefBtnSm(preferences.spread === opt, 'base')}>
                              {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-3.5">
                        <label className="w-28 flex-shrink-0 text-sm font-medium text-gray-700">Consecutive</label>
                        <div className="flex gap-1.5 flex-1">
                          {(['yes', 'no'] as const).map(opt => (
                            <button key={opt} onClick={() => setPreferences({ ...preferences, consecutive: opt })} className={prefBtnSm(preferences.consecutive === opt, 'base')}>
                              {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Strategies (live API) panel */}
                {engine === 'live' && (
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex flex-col gap-3.5">
                    <p className="text-xs text-gray-500 leading-relaxed">
                      Powered by the same 5-strategy model as the historical predictions, with your
                      constraints enforced live by the prediction API. Returns up to 5 sets per request.
                    </p>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Spread</label>
                      <div className="flex gap-2 flex-1">
                        {(['tight', 'wide', 'mixed'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, spread: opt })} className={prefBtn(preferences.spread === opt, 'base')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Leaning</label>
                      <div className="flex gap-2 flex-1">
                        {(['left', 'middle', 'right'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, leaning: opt })} className={prefBtn(preferences.leaning === opt, 'blue')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="w-36 flex-shrink-0 text-sm font-medium text-gray-700">Consecutive Numbers</label>
                      <div className="flex gap-2 flex-1">
                        {(['yes', 'no'] as const).map(opt => (
                          <button key={opt} onClick={() => setPreferences({ ...preferences, consecutive: opt })} className={prefBtn(preferences.consecutive === opt, 'base')}>
                            {opt.charAt(0).toUpperCase() + opt.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Manual History Check */}
                <div className="p-6">
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <Search className="w-4 h-4 text-highlight-blue" />
                      <h3 className="text-base font-semibold text-gray-800">Check Your Own Numbers</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                      Enter 6 main numbers to check if the exact combination exists in the dataset.
                    </p>
                    <div className="flex flex-col gap-2">
                      <input
                        type="text"
                        value={manualNumbers}
                        onChange={(e) => setManualNumbers(e.target.value)}
                        placeholder="e.g. 3, 7, 12, 18, 24, 31"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-800 placeholder:text-gray-400 focus:border-highlight-blue focus:outline-none focus:ring-2 focus:ring-highlight-blue/20 text-sm"
                      />
                      <button
                        onClick={handleManualCheck}
                        disabled={loading || data.length === 0}
                        className="w-full rounded-lg bg-gray-900 px-4 py-2.5 font-semibold text-white text-sm transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Check Against Dataset
                      </button>
                    </div>
                    {manualCheckMessage && (
                      <div className="mt-3 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
                        {manualCheckMessage}
                      </div>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="px-6 pb-6">
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                      {error}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {!gdprDismissed && (
        <CookieBanner
          onPrivacyClick={() => setShowPrivacy(true)}
          onDismiss={() => {
            localStorage.setItem('lotto_gdpr_dismissed', 'true');
            setGdprDismissed(true);
          }}
        />
      )}
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}

      {/* iOS-style picker modal (mobile only) */}
      {showPickerModal && (
        <div className="lg:hidden fixed inset-0 z-50 flex items-end">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowPickerModal(false)}
          />
          <div className="relative w-full bg-white rounded-t-3xl shadow-2xl">
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>
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
            <div
              className="relative overflow-hidden"
              style={{ height: ITEM_H * VISIBLE }}
            >
              <div
                className="absolute inset-x-8 border-t-2 border-b-2 border-gray-200 pointer-events-none z-10"
                style={{ top: drumPadding, height: ITEM_H }}
              />
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
                {Array.from({ length: 20 }, (_, i) => i + 1).map(n => (
                  <div
                    key={n}
                    className={`snap-center flex items-center justify-center font-semibold transition-all duration-100 select-none ${
                      n === tempCount ? 'text-gray-900 text-3xl' : 'text-gray-400 text-xl'
                    }`}
                    style={{ height: ITEM_H }}
                  >
                    {n}
                  </div>
                ))}
              </div>
              <div
                className="absolute inset-x-0 top-0 pointer-events-none z-20 bg-gradient-to-b from-white via-white/70 to-transparent"
                style={{ height: drumPadding }}
              />
              <div
                className="absolute inset-x-0 bottom-0 pointer-events-none z-20 bg-gradient-to-t from-white via-white/70 to-transparent"
                style={{ height: drumPadding }}
              />
            </div>
            <div className="h-8" />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
