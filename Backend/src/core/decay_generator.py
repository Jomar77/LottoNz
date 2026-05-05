"""
Radioactive-Decay-Inspired Lottery Number Generator
----------------------------------------------------
Run from the backend/ directory:

    python src/core/decay_generator.py
    python src/core/decay_generator.py --count 5
    python src/core/decay_generator.py --count 3 --seed 42
    python src/core/decay_generator.py --mode temporal
    python src/core/decay_generator.py --mode temporal --half-life 26
    python src/core/decay_generator.py --show-rates
    python src/core/decay_generator.py --eval
    python src/core/decay_generator.py --eval --mode temporal
    python src/core/decay_generator.py --count 10 --no-uniqueness-check

Modes
-----
classic  (default)
    lambda_n = Laplace-smoothed historical count / total.
    Every past draw carries equal weight regardless of when it happened.

temporal
    Anchored to 2001-02-17 (first NZ Powerball draw).
    lambda_n = sum of exp(-alpha * weeks_since_appearance) for every draw
               where ball n appeared, plus a small epsilon baseline.
    alpha = ln(2) / half_life_weeks.
    Contribution of each appearance decays continuously from the moment it
    occurred; recent appearances dominate, old ones fade toward zero.
    The rate grows each week a ball appears and decays between appearances —
    continuous-time radioactive physics applied to a discrete draw schedule.

Algorithm (both modes)
    40 virtual sources (one per ball 1-40). Sample tau_n ~ Exp(lambda_n)
    per source; the 6 smallest tau are the drawn numbers. Powerball uses a
    separate 10-source chamber. Equivalent to weighted-sampling-without-
    replacement with weights proportional to lambda_n.
"""

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR     = Path(__file__).resolve().parent
REPO_ROOT      = SCRIPT_DIR.parents[2]
DATA_PATH      = REPO_ROOT / "frontend" / "public" / "results.json"
POWERBALL_EPOCH = date(2001, 2, 17)   # first NZ Powerball draw


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[error] results.json not found at {path}\n"
                 "Run from the backend/ directory or adjust the path.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Lambda derivation
# ---------------------------------------------------------------------------

def derive_lambdas_classic(draws: list[dict]):
    """Return (lam_main[40], lam_pb[10], counts_main[40], counts_pb[10])."""
    n = len(draws)
    counts_main = np.zeros(40, dtype=int)
    counts_pb   = np.zeros(10, dtype=int)
    for d in draws:
        for num in d["numbers"]:
            counts_main[int(num) - 1] += 1
        counts_pb[int(d["powerball"]) - 1] += 1
    lam_main = (counts_main + 1) / (n * 6 + 40)
    lam_pb   = (counts_pb   + 1) / (n     + 10)
    return lam_main, lam_pb, counts_main, counts_pb


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def derive_lambdas_temporal(draws: list[dict], half_life_weeks: float,
                             reference_date: date | None = None):
    """
    Return (lam_main[40], lam_pb[10], activity_main[40], activity_pb[10], ref_date).

    Activity decays continuously from each appearance date to reference_date.
    Normalised so lam sums to 1.0 across each pool.
    """
    if reference_date is None:
        reference_date = max(_parse_date(d["date"]) for d in draws)

    alpha         = math.log(2) / half_life_weeks
    epsilon       = 1e-3   # baseline so every ball is reachable

    activity_main = np.full(40, epsilon)
    activity_pb   = np.full(10, epsilon)

    for d in draws:
        weeks_ago    = (reference_date - _parse_date(d["date"])).days / 7.0
        contribution = math.exp(-alpha * weeks_ago)
        for num in d["numbers"]:
            activity_main[int(num) - 1] += contribution
        activity_pb[int(d["powerball"]) - 1] += contribution

    lam_main = activity_main / activity_main.sum()
    lam_pb   = activity_pb   / activity_pb.sum()
    return lam_main, lam_pb, activity_main, activity_pb, reference_date


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------

def decay_draw(lam_main: np.ndarray, lam_pb: np.ndarray,
               rng: np.random.Generator) -> tuple[list[int], int]:
    """Sample one ticket. tau_n ~ Exp(lambda_n); pick 6 smallest."""
    tau_main  = rng.exponential(scale=1.0 / lam_main)
    numbers   = sorted((np.argsort(tau_main)[:6] + 1).tolist())
    tau_pb    = rng.exponential(scale=1.0 / lam_pb)
    powerball = int(np.argmin(tau_pb) + 1)
    return numbers, powerball


# ---------------------------------------------------------------------------
# Historical uniqueness
# ---------------------------------------------------------------------------

def build_historical_sets(draws: list[dict]) -> set[frozenset]:
    return {frozenset(d["numbers"]) for d in draws}


def is_historically_unique(numbers: list[int], hist: set[frozenset]) -> bool:
    return frozenset(numbers) not in hist


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def run_eval(lam_main: np.ndarray, lam_pb: np.ndarray,
             draws: list[dict], mode: str, half_life: float | None) -> None:
    N_SIM  = 10_000
    SEEDS  = [0, 1, 2, 3, 4]

    hl_tag = f"  half-life={half_life}w" if half_life else ""
    print(f"\n{'='*62}")
    print(f"  EVAL  mode={mode}{hl_tag}  N={N_SIM} tickets x {len(SEEDS)} seeds")
    print(f"{'='*62}")

    # Historical empirical distribution
    hist_counts = np.zeros(40)
    for d in draws:
        for num in d["numbers"]:
            hist_counts[int(num) - 1] += 1
    hist_freq = hist_counts / hist_counts.sum()
    hist_sets = build_historical_sets(draws)
    unif      = np.full(40, 1 / 40)

    chi2_ps, kl_hists, kl_unifs, means, stds, uniqs, coverages = [], [], [], [], [], [], []

    for seed in SEEDS:
        rng     = np.random.default_rng(seed)
        tickets = [decay_draw(lam_main, lam_pb, rng) for _ in range(N_SIM)]
        flat    = np.array([n for nums, _ in tickets for n in nums])

        obs = np.zeros(40)
        for n in flat:
            obs[int(n) - 1] += 1

        # Chi-square vs uniform
        _, p = stats.chisquare(obs, f_exp=np.full(40, N_SIM * 6 / 40))
        chi2_ps.append(p)

        # KL divergences
        gf = obs / obs.sum()
        kl_hists.append(float(np.sum(gf * np.log((gf + 1e-12) / (hist_freq + 1e-12)))))
        kl_unifs.append(float(np.sum(gf * np.log((gf + 1e-12) / unif))))

        means.append(float(flat.mean()))
        stds.append(float(flat.std()))
        coverages.append(int((obs > 0).sum()))
        uniqs.append(sum(1 for nums, _ in tickets if is_historically_unique(nums, hist_sets)) / N_SIM)

    # Seed consistency
    rng_a = np.random.default_rng(999)
    rng_b = np.random.default_rng(999)
    same  = all(decay_draw(lam_main, lam_pb, rng_a) == decay_draw(lam_main, lam_pb, rng_b)
                for _ in range(200))

    # NIST monobit + runs (seed=0)
    rng0    = np.random.default_rng(0)
    bits    = []
    for nums, pb in [decay_draw(lam_main, lam_pb, rng0) for _ in range(N_SIM)]:
        for n in sorted(nums):
            bits.extend([(n >> i) & 1 for i in range(5, -1, -1)])
        bits.extend([(pb >> i) & 1 for i in range(3, -1, -1)])
    bits   = np.array(bits)
    nb     = len(bits)
    pi_hat = bits.mean()
    s_obs  = abs(np.sum(2 * bits - 1)) / math.sqrt(nb)
    mono_p = float(math.erfc(s_obs / math.sqrt(2)))
    v_obs  = 1 + int(np.sum(bits[:-1] != bits[1:]))
    runs_p = float(math.erfc(
        abs(v_obs - 2 * nb * pi_hat * (1 - pi_hat)) /
        (2 * math.sqrt(2 * nb) * pi_hat * (1 - pi_hat))
    ))

    def ms(arr):
        a = np.array(arr)
        return f"{a.mean():.4f}  +/-  {a.std():.4f}"

    print()
    print(f"  Distribution (main numbers, chi-sq vs uniform)")
    print(f"    p-value                   : {ms(chi2_ps)}")
    print(f"    Verdict                   : EXPECTED FAIL - we intentionally weight by")
    print(f"                                frequency, so output is NOT uniform.")
    print(f"                                KL vs historical (below) is the real check.")

    print(f"\n  KL divergence (nats, lower = closer to that distribution)")
    print(f"    vs historical empirical   : {ms(kl_hists)}")
    kl_h = np.mean(kl_hists)
    if kl_h < 0.001:
        kl_verdict = "Excellent - output almost identical to historical."
    elif kl_h < 0.005:
        kl_verdict = "Good - small divergence from historical."
    elif kl_h < 0.02:
        kl_verdict = "Moderate - recent-draw emphasis shifts distribution."
    else:
        kl_verdict = "High - strong recency bias, far from full history."
    print(f"                              : {kl_verdict}")
    print(f"    vs uniform                : {ms(kl_unifs)}")

    print(f"\n  Descriptive stats (main numbers)")
    print(f"    Mean  (uniform = 20.500)  : {ms(means)}")
    print(f"    Std   (uniform = 11.690)  : {ms(stds)}")

    print(f"\n  Coverage")
    print(f"    Balls seen / 40           : {np.mean(coverages):.1f} / 40")
    print(f"    All 40 reachable          : {'PASS' if np.mean(coverages) == 40 else 'FAIL — some balls blocked'}")

    print(f"\n  Uniqueness (vs {len(draws)} historical draws)")
    print(f"    % tickets not in history  : {np.mean(uniqs)*100:.2f}%")

    print(f"\n  Reproducibility")
    print(f"    Same seed => same output  : {'PASS' if same else 'FAIL'}")

    print(f"\n  NIST SP 800-22 (2/15 tests, seed=0, {nb:,} bits)")
    print(f"    Monobit  p = {mono_p:.4f}   => EXPECTED FAIL")
    print(f"    Runs     p = {runs_p:.4f}   => EXPECTED FAIL")
    print(f"    Note: NIST tests require balanced bit streams from hardware TRNGs.")
    print(f"          Encoding balls 1-40 in 6 bits is structurally unbalanced")
    print(f"          (e.g. bit 5 is 1 only for balls 32-40, not 50% of the time).")
    print(f"          These failures indicate encoding structure, not RNG quality.")
    print(f"          The correct quality check is KL divergence above.")

    print(f"\n{'='*62}")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_rates_classic(lam_main, lam_pb, counts_main, counts_pb, n_draws):
    unif = 6 / 40
    print(f"\n{'-'*66}")
    print(f"  CLASSIC MODE  (Laplace-smoothed historical frequency)")
    print(f"  Uniform baseline per ball: {unif:.5f}")
    print(f"{'-'*66}")
    print(f"  {'Ball':>4}  {'Count':>6}  {'lam(raw)':>9}  {'lam(smooth)':>12}  delta")
    print(f"  {'-'*4}  {'-'*6}  {'-'*9}  {'-'*12}  {'-'*6}")
    for i in range(40):
        raw  = counts_main[i] / (n_draws * 6)
        d    = lam_main[i] - unif
        sign = "+" if d >= 0 else "-"
        print(f"  {i+1:>4}  {counts_main[i]:>6}  {raw:>9.5f}  {lam_main[i]:>12.5f}  {sign}{abs(d):.5f}")
    print(f"\n  {'PB':>4}  {'Count':>6}  {'lam(smooth)':>12}")
    print(f"  {'-'*4}  {'-'*6}  {'-'*12}")
    for i in range(10):
        print(f"  {i+1:>4}  {counts_pb[i]:>6}  {lam_pb[i]:>12.5f}")
    print()


def print_rates_temporal(lam_main, lam_pb, act_main, act_pb, half_life, ref_date):
    unif = 1 / 40
    print(f"\n{'-'*66}")
    print(f"  TEMPORAL MODE  (half-life={half_life}w, reference={ref_date})")
    print(f"  Activity = weighted sum of past appearances (exp decay).")
    print(f"  Lambda   = normalised activity (sums to 1.0 across pool).")
    print(f"{'-'*66}")
    print(f"  {'Ball':>4}  {'Activity':>10}  {'Lambda':>10}  delta vs 1/40")
    print(f"  {'-'*4}  {'-'*10}  {'-'*10}  {'-'*14}")
    for i in range(40):
        d    = lam_main[i] - unif
        sign = "+" if d >= 0 else "-"
        print(f"  {i+1:>4}  {act_main[i]:>10.4f}  {lam_main[i]:>10.5f}  {sign}{abs(d):.5f}")
    print(f"\n  {'PB':>4}  {'Activity':>10}  {'Lambda':>10}")
    print(f"  {'-'*4}  {'-'*10}  {'-'*10}")
    for i in range(10):
        print(f"  {i+1:>4}  {act_pb[i]:>10.4f}  {lam_pb[i]:>10.5f}")
    print()


def print_ticket(entry: int, numbers: list[int], powerball: int,
                 unique: bool | None, mode: str) -> None:
    spread     = max(numbers) - min(numbers)
    has_consec = any(numbers[i+1] - numbers[i] == 1 for i in range(len(numbers)-1))
    utag = ""
    if unique is True:
        utag = "  [unique in history]"
    elif unique is False:
        utag = "  [duplicate - could not find unique in 200 attempts]"

    print(f"\n  {'='*58}")
    print(f"  TICKET #{entry}  ({mode} decay)")
    print(f"  {'='*58}")
    print(f"  Main Numbers : {', '.join(f'{n:2d}' for n in numbers)}")
    print(f"  Powerball    : {powerball}")
    print(f"  Spread       : {spread}  ({min(numbers)}-{max(numbers)})")
    print(f"  Consecutive  : {'yes' if has_consec else 'no'}{utag}")
    print(f"  {'='*58}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Radioactive-decay-inspired NZ Lotto ticket generator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--count",   "-n", type=int,  default=None,
                   help="Tickets to generate (default: prompt)")
    p.add_argument("--seed",    "-s", type=int,  default=None,
                   help="RNG seed for reproducibility")
    p.add_argument("--mode",    "-m", default="classic",
                   choices=["classic", "temporal"],
                   help="classic=flat frequency, temporal=time-weighted (default: classic)")
    p.add_argument("--half-life", type=float, default=52.0,
                   help="Half-life in weeks for temporal mode (default: 52 = 1 year)")
    p.add_argument("--show-rates", action="store_true",
                   help="Print per-ball lambda table before generating")
    p.add_argument("--eval",       action="store_true",
                   help="Run statistical evals (10k tickets x 5 seeds)")
    p.add_argument("--no-uniqueness-check", action="store_true",
                   help="Skip checking tickets against historical draws")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"\n  [RDG]  RADIOACTIVE DECAY LOTTERY GENERATOR")
    print(f"  Mode: {args.mode.upper()}"
          + (f"  |  Half-life: {args.half_life}w" if args.mode == "temporal" else ""))
    print(f"  Data: {DATA_PATH.relative_to(REPO_ROOT)}")

    draws = load_data(DATA_PATH)
    draws_sorted = sorted(draws, key=lambda d: d["date"])
    print(f"  Draws: {len(draws)}  ({draws_sorted[0]['date']} to {draws_sorted[-1]['date']})")

    if args.mode == "temporal":
        print(f"  Epoch: {POWERBALL_EPOCH}  (NZ Powerball introduced)")

    # --- Derive lambdas ---
    if args.mode == "classic":
        lam_main, lam_pb, counts_main, counts_pb = derive_lambdas_classic(draws)
    else:
        lam_main, lam_pb, act_main, act_pb, ref_date = derive_lambdas_temporal(
            draws, args.half_life
        )

    # --- Show rates ---
    if args.show_rates:
        if args.mode == "classic":
            print_rates_classic(lam_main, lam_pb, counts_main, counts_pb, len(draws))
        else:
            print_rates_temporal(lam_main, lam_pb, act_main, act_pb, args.half_life, ref_date)

    # --- Eval ---
    if args.eval:
        run_eval(lam_main, lam_pb, draws, args.mode,
                 args.half_life if args.mode == "temporal" else None)
        if args.count is None:
            return

    # --- Generate tickets ---
    count = args.count
    if count is None:
        try:
            count = int(input("\n  How many tickets? "))
        except (ValueError, EOFError):
            count = 1

    seed = args.seed
    if seed is None:
        seed_input = input("  Seed (leave blank for random): ").strip()
        seed = int(seed_input) if seed_input.isdigit() else None

    rng = np.random.default_rng(seed)
    if seed is not None:
        print(f"  RNG seed: {seed}")

    hist = None if args.no_uniqueness_check else build_historical_sets(draws)

    print(f"\n  Generating {count} ticket(s)...\n")
    for i in range(1, count + 1):
        for _ in range(200):
            numbers, powerball = decay_draw(lam_main, lam_pb, rng)
            if hist is None or is_historically_unique(numbers, hist):
                unique = None if hist is None else True
                break
        else:
            unique = False

        print_ticket(i, numbers, powerball, unique, args.mode)

    print(f"\n  Done. Good luck!\n")


if __name__ == "__main__":
    main()
