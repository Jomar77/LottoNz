import { BookOpen, AlertTriangle, FlaskConical, Zap, RotateCcw, TrendingUp, Scale, MoveHorizontal } from 'lucide-react';
import type { PredictionsDocument, PredictionSet, PredictionStrategy } from './types';
import {
  formatStrategyLabel,
  formatFallacyLabel,
  formatFallacyExplanation,
  orderPredictionSets,
} from './utils';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface PatternExplorerProps {
  doc: PredictionsDocument | null;
}

// ---------------------------------------------------------------------------
// Strategy icons
// ---------------------------------------------------------------------------
const STRATEGY_ICONS: Record<PredictionStrategy, React.ReactNode> = {
  burst_volatility: <Zap className="w-4 h-4" />,
  mean_reversion: <RotateCcw className="w-4 h-4" />,
  momentum_carry: <TrendingUp className="w-4 h-4" />,
  balanced_hybrid: <Scale className="w-4 h-4" />,
  lean_bias: <MoveHorizontal className="w-4 h-4" />,
};

// ---------------------------------------------------------------------------
// UniformityHero — the statistical heart of the section
// ---------------------------------------------------------------------------
function UniformityHero({ doc }: { doc: PredictionsDocument }) {
  const { total_draws_analyzed, date_range, uniformity_confirmed, chi_square_p_main } = doc.metadata;
  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-5 border border-white/20 mb-6">
      <div className="flex items-start gap-3">
        <FlaskConical className="w-5 h-5 text-white/70 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-white font-semibold text-sm mb-1">What the data actually shows</p>
          <p className="text-white/80 text-sm leading-relaxed">
            Across <span className="text-white font-medium">{total_draws_analyzed.toLocaleString()} draws</span>{' '}
            ({date_range}), every number from 1–40 tested{' '}
            <span className="text-white font-medium">statistically equally likely</span>
            {uniformity_confirmed
              ? ` — chi-square p-value ${chi_square_p_main} (p > 0.05, uniform).`
              : ` — however the chi-square test flagged non-uniformity (p = ${chi_square_p_main}).`}
            {' '}No number is luckier than any other.
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// StrategyCard — one fallacy card per set
// ---------------------------------------------------------------------------
function StrategyCard({ set }: { set: PredictionSet }) {
  const icon = STRATEGY_ICONS[set.strategy as PredictionStrategy] ?? <BookOpen className="w-4 h-4" />;
  const fallacyLabel = formatFallacyLabel(set.strategy);
  const fallacyExplanation = formatFallacyExplanation(set.strategy);
  const strategyLabel = formatStrategyLabel(set.strategy);

  return (
    <div className="bg-white rounded-2xl shadow-md p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <span className="text-gray-400">{icon}</span>
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{strategyLabel}</span>
        <span className="ml-auto text-xs font-medium text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
          {fallacyLabel}
        </span>
      </div>

      {/* Fallacy explanation */}
      <p className="text-xs text-gray-500 mb-4 leading-relaxed">{fallacyExplanation}</p>

      {/* Numbers */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        {set.main_numbers.map((num) => (
          <div
            key={num}
            className="w-11 h-11 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 text-base font-bold"
          >
            {num}
          </div>
        ))}
        <div className="w-11 h-11 rounded-full bg-amber-100 border-2 border-amber-300 flex items-center justify-center text-amber-700 text-base font-bold ml-1">
          {set.powerball}
        </div>
      </div>

      {/* Rationale (from engine — additional context) */}
      <p className="text-xs text-gray-400 italic">{set.rationale}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PatternExplorer — main component
// ---------------------------------------------------------------------------
export function PatternExplorer({ doc }: PatternExplorerProps) {
  if (!doc) {
    return null;
  }

  const validSets = orderPredictionSets(doc.sets);
  if (validSets.length === 0) {
    return null;
  }

  const { total_draws_analyzed, date_range } = doc.metadata;
  const { generated_at } = doc;
  const generatedDate = new Date(generated_at).toLocaleDateString('en-NZ', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <section className="mt-8 max-w-6xl mx-auto px-4">
      {/* Section header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-1">
          <FlaskConical className="w-5 h-5 text-white/70" />
          <h2 className="text-2xl font-bold text-white">Pattern Explorer</h2>
        </div>
        <p className="text-white/70 text-sm">
          We mined {total_draws_analyzed.toLocaleString()} draws ({date_range}) for "patterns", then proved with our own statistics that the draws are uniform random noise. The cards below show themed number sets — one per common gambling fallacy — alongside the reason each strategy has no real edge.
        </p>
      </div>

      {/* Uniformity hero */}
      <UniformityHero doc={doc} />

      {/* Strategy cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
        {validSets.map((set) => (
          <StrategyCard key={set.id} set={set} />
        ))}
      </div>

      {/* Footer */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-xs text-white/50 space-y-1">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-white/40" />
          <p>
            <strong className="text-white/70">These are not predictions.</strong> Lottery draws are independent, uniform-random events — no method, algorithm, or historical pattern can improve your odds. The numbers above are themed alternatives to a random quick-pick, provided for entertainment and educational purposes only.
          </p>
        </div>
        <p>
          If gambling is causing you harm, free support is available 24/7:{' '}
          <span className="text-white/70 font-medium">gamblinghelpline.co.nz</span> or call{' '}
          <span className="text-white/70 font-medium">0800 654 655</span>. You must be 18+ to play NZ Lotto.
        </p>
        <p className="text-white/30">
          Generated {generatedDate} from {total_draws_analyzed.toLocaleString()} draws.
        </p>
      </div>
    </section>
  );
}
