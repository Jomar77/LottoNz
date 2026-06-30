# Powerball Prediction Algorithm - Implementation Guide

> **Disclaimer**: This algorithm is for entertainment and statistical curiosity only. Lottery draws are independent random events. Past patterns do not predict future outcomes. Play responsibly.

---

## 📋 Overview

This document summarizes the analytical framework used to generate Powerball number predictions based on historical draw data (2001–2026). The algorithm identifies statistical patterns, volatility clusters, and regression candidates to produce strategically distinct number sets.

---

## 🗄️ Data Structure

### Input CSV Format
```csv
date,numbers/0,numbers/1,numbers/2,numbers/3,numbers/4,numbers/5,powerball
2026-05-09,3,10,12,18,26,32,5
```

| Column | Description | Range |
|--------|-------------|-------|
| `date` | Draw date (YYYY-MM-DD) | - |
| `numbers/0` to `numbers/5` | Main numbers (sorted ascending) | 1–40 |
| `powerball` | Powerball number | 1–10 |

### Key Constants
```python
MAIN_NUMBERS_RANGE = (1, 40)
POWERBALL_RANGE = (1, 10)
NUMBERS_PER_DRAW = 6
EXPECTED_MAIN_FREQ = total_draws * 6 / 40  # ~242 per number (20-year dataset)
EXPECTED_PB_FREQ = total_draws / 10         # ~161 per PB (20-year dataset)
```

---

## 🔬 Statistical Methods

### 1. Uniformity Testing (Chi-Square)
```python
from scipy import stats

def test_uniformity(frequencies, expected):
    chi2, p_value = stats.chisquare(frequencies, f_exp=[expected]*len(frequencies))
    return p_value > 0.05  # Fail to reject null = uniform
```

### 2. Coefficient of Variation (CV) - Volatility Metric
```python
def calculate_cv(values):
    import numpy as np
    mean = np.mean(values)
    std = np.std(values)
    return std / mean if mean > 0 else 0
```
- **High CV** = "Burst" numbers (appear in clusters, then go cold)
- **Low CV** = "Stable" numbers (consistent frequency)

### 3. Z-Score for Regression Detection
```python
def calculate_z_score(current_freq, mean_freq, std_freq):
    return (current_freq - mean_freq) / std_freq
```
- `|z| > 2.0` = Statistical outlier
- Negative z = "Cold" number (due for regression)
- Positive z = "Hot" number (may cool down)

### 4. Left/Right Leaning Analysis
```python
LEFT_RANGE = (1, 20)
RIGHT_RANGE = (21, 40)

def classify_lean(numbers):
    left_count = sum(1 for n in numbers if n <= 20)
    right_count = len(numbers) - left_count
    return "left" if left_count > right_count else "right"
```

---

## 🎯 Number Generation Strategies

### Strategy 1: Burst Volatility Set
**Goal**: Capture high-CV numbers that appear in clusters

```python
def generate_burst_set(historical_data, top_n=6):
    # Calculate CV per number across quarters
    quarterly_freqs = calculate_quarterly_frequencies(historical_data)
    cv_scores = {num: calculate_cv(freqs) for num, freqs in quarterly_freqs.items()}
    
    # Select top N by CV + recent appearance boost
    burst_candidates = sorted(cv_scores.items(), key=lambda x: x[1], reverse=True)[:top_n*2]
    
    # Filter for numbers appearing in last 30 draws (momentum boost)
    recent_nums = get_recent_numbers(historical_data, last_n_draws=30)
    final_set = [num for num, _ in burst_candidates if num in recent_nums][:top_n]
    
    return final_set
```

### Strategy 2: Regression (Sleeping Giants) Set
**Goal**: Select numbers statistically below mean frequency

```python
def generate_regression_set(historical_data, z_threshold=-2.0):
    freqs = calculate_frequencies(historical_data)
    mean_freq = np.mean(list(freqs.values()))
    std_freq = np.std(list(freqs.values()))
    
    # Find numbers with z-score below threshold
    cold_numbers = [
        num for num, freq in freqs.items()
        if calculate_z_score(freq, mean_freq, std_freq) < z_threshold
    ]
    
    # Sort by most negative z-score (coldest first)
    cold_numbers.sort(key=lambda n: calculate_z_score(freqs[n], mean_freq, std_freq))
    
    return cold_numbers[:6]
```

### Strategy 3: Momentum Carry-Over Set
**Goal**: Ride recent hot streaks

```python
def generate_momentum_set(historical_data, window=30, min_freq=8):
    recent_draws = historical_data.tail(window)
    freqs = calculate_frequencies(recent_draws)
    
    # Select numbers appearing >= min_freq times in window
    hot_numbers = [num for num, freq in freqs.items() if freq >= min_freq]
    
    # Sort by frequency descending, take top 6
    hot_numbers.sort(key=lambda n: freqs[n], reverse=True)
    return hot_numbers[:6]
```

### Strategy 4: Balanced Hybrid Set
**Goal**: Diversify across hot/cold/mean performers

```python
def generate_hybrid_set(historical_data):
    freqs = calculate_frequencies(historical_data)
    mean_freq = np.mean(list(freqs.values()))
    
    # Categorize numbers
    hot = [n for n, f in freqs.items() if f > mean_freq * 1.05]
    cold = [n for n, f in freqs.items() if f < mean_freq * 0.95]
    neutral = [n for n, f in freqs.items() if mean_freq * 0.95 <= f <= mean_freq * 1.05]
    
    # Build balanced set: 2 hot + 2 cold + 2 neutral
    import random
    result = []
    result.extend(random.sample(hot, min(2, len(hot))))
    result.extend(random.sample(cold, min(2, len(cold))))
    result.extend(random.sample(neutral, min(2, len(neutral))))
    
    # Fill remaining slots if needed
    while len(result) < 6:
        remaining = [n for n in range(1, 41) if n not in result]
        result.append(random.choice(remaining))
    
    return sorted(result)
```

### Strategy 5: Left/Right Leaning Sets
**Goal**: Exploit temporal lean biases

```python
def generate_lean_set(historical_data, lean_direction="left", window_years=1):
    # Filter recent draws by time window
    cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=window_years)
    recent = historical_data[historical_data['date'] >= cutoff_date]
    
    # Calculate lean bias
    left_freq = sum(1 for nums in recent['numbers'] for n in nums if n <= 20)
    right_freq = sum(1 for nums in recent['numbers'] for n in nums if n > 20)
    
    # Select numbers from target side with highest recent frequency
    target_range = LEFT_RANGE if lean_direction == "left" else RIGHT_RANGE
    freqs = calculate_frequencies(recent)
    
    candidates = [
        (num, freqs.get(num, 0)) 
        for num in range(target_range[0], target_range[1]+1)
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    return [num for num, _ in candidates[:6]]
```

---

## 🔄 Powerball Selection Logic

```python
def select_powerball(historical_data, strategy="balanced"):
    pb_freqs = historical_data['powerball'].value_counts()
    
    if strategy == "hot":
        # Most frequent in last 30 draws
        return pb_freqs.head(1).index[0]
    
    elif strategy == "cold":
        # Least frequent overall (regression play)
        return pb_freqs.idxmin()
    
    elif strategy == "cluster":
        # PB that appears with high-CV main numbers
        high_cv_nums = get_high_cv_numbers(historical_data)
        pb_cooccurrence = calculate_pb_cooccurrence(historical_data, high_cv_nums)
        return pb_cooccurrence.idxmax()
    
    else:  # balanced
        # Weighted random by frequency
        import random
        return random.choices(
            population=pb_freqs.index.tolist(),
            weights=pb_freqs.values.tolist(),
            k=1
        )[0]
```

---

## 🧩 Full Algorithm Pipeline

```python
def generate_prediction_sets(historical_data, num_sets=4, exclude_recent_draws=5):
    """
    Generate multiple strategically distinct prediction sets.
    
    Args:
        historical_data: DataFrame with lottery results
        num_sets: Number of sets to generate
        exclude_recent_draws: Avoid duplicating numbers from last N draws
    
    Returns:
        List of dicts: [{'main': [nums], 'pb': int, 'strategy': str}, ...]
    """
    # Get recently drawn numbers to avoid exact duplicates
    recent_numbers = get_recent_numbers(historical_data, exclude_recent_draws)
    
    sets = []
    
    # Set 1: Burst Volatility
    burst_main = generate_burst_set(historical_data)
    sets.append({
        'main': avoid_duplicates(burst_main, recent_numbers),
        'pb': select_powerball(historical_data, strategy="cluster"),
        'strategy': 'burst_volatility'
    })
    
    # Set 2: Regression Play
    regression_main = generate_regression_set(historical_data)
    sets.append({
        'main': avoid_duplicates(regression_main, recent_numbers),
        'pb': select_powerball(historical_data, strategy="cold"),
        'strategy': 'mean_reversion'
    })
    
    # Set 3: Momentum Follow
    momentum_main = generate_momentum_set(historical_data)
    sets.append({
        'main': avoid_duplicates(momentum_main, recent_numbers),
        'pb': select_powerball(historical_data, strategy="hot"),
        'strategy': 'momentum_carry'
    })
    
    # Set 4: Balanced Hybrid
    hybrid_main = generate_hybrid_set(historical_data)
    sets.append({
        'main': avoid_duplicates(hybrid_main, recent_numbers),
        'pb': select_powerball(historical_data, strategy="balanced"),
        'strategy': 'balanced_hybrid'
    })
    
    return sets[:num_sets]

def avoid_duplicates(candidate_nums, recent_numbers, max_overlap=2):
    """
    Ensure generated set doesn't too closely match recent draws.
    """
    if len(set(candidate_nums) & set(recent_numbers)) <= max_overlap:
        return candidate_nums
    
    # Replace overlapping numbers with non-recent alternatives
    available = [n for n in range(1, 41) if n not in recent_numbers and n not in candidate_nums]
    result = candidate_nums.copy()
    
    for i, num in enumerate(result):
        if num in recent_numbers and available:
            result[i] = available.pop(0)
    
    return sorted(result)
```

---

## 📊 Output Format

```json
{
  "draw_reference": 2591,
  "generated_at": "2026-06-27T12:00:00Z",
  "sets": [
    {
      "id": 1,
      "strategy": "burst_volatility",
      "main_numbers": [2, 5, 7, 11, 28, 35],
      "powerball": 3,
      "rationale": "High-CV numbers with recent clustering behavior"
    },
    {
      "id": 2,
      "strategy": "mean_reversion",
      "main_numbers": [8, 14, 23, 36, 39, 40],
      "powerball": 7,
      "rationale": "Numbers below mean frequency due for regression"
    }
    // ... additional sets
  ],
  "metadata": {
    "total_draws_analyzed": 2600,
    "date_range": "2001-01-01 to 2026-05-09",
    "uniformity_confirmed": true,
    "chi_square_p_main": 0.585,
    "chi_square_p_powerball": 0.178
  }
}
```

---

## ⚙️ Implementation Checklist

- [ ] Load and parse CSV data into DataFrame
- [ ] Calculate frequency distributions (overall, quarterly, yearly)
- [ ] Implement CV, Z-score, and Chi-square functions
- [ ] Build strategy-specific generator functions
- [ ] Add duplicate-avoidance logic against recent draws
- [ ] Implement Powerball selection logic
- [ ] Create JSON output formatter
- [ ] Add configuration options (time windows, thresholds, etc.)
- [ ] Include disclaimer and responsible play messaging

---

## 🧪 Testing & Validation

```python
def validate_output(sets, historical_data):
    """Basic validation checks for generated sets."""
    errors = []
    
    for i, s in enumerate(sets):
        # Check main numbers count and range
        if len(s['main']) != 6:
            errors.append(f"Set {i+1}: Expected 6 main numbers")
        if not all(1 <= n <= 40 for n in s['main']):
            errors.append(f"Set {i+1}: Main numbers out of range")
        if len(set(s['main'])) != 6:
            errors.append(f"Set {i+1}: Duplicate main numbers")
        
        # Check Powerball range
        if not 1 <= s['pb'] <= 10:
            errors.append(f"Set {i+1}: Powerball out of range")
        
        # Check sorting
        if s['main'] != sorted(s['main']):
            errors.append(f"Set {i+1}: Main numbers not sorted")
    
    return errors
```

---

## ⚠️ Important Notes

1. **Randomness is fundamental**: This algorithm identifies *historical patterns*, not predictive signals. Each draw is independent.
2. **Avoid overfitting**: Use rolling time windows (e.g., 20-year, 5-year, 1-year) to prevent curve-fitting to noise.
3. **Update frequencies regularly**: Re-calculate stats after each new draw to keep the model current.
4. **User transparency**: Always display the strategy rationale so users understand the "why" behind each set.
5. **Legal compliance**: Include responsible gambling messaging and age verification if deploying publicly.

---

## 🚀 Quick Start Pseudocode

```python
# 1. Load data
df = pd.read_csv('results.csv', parse_dates=['date'])

# 2. Pre-calculate statistics
stats = precompute_statistics(df)

# 3. Generate sets for next draw
predictions = generate_prediction_sets(
    historical_data=df,
    num_sets=4,
    exclude_recent_draws=5
)

# 4. Format and return
output = format_output(predictions, stats)
print(json.dumps(output, indent=2))
```

---

> 🎲 **Final Reminder**: No algorithm can beat true randomness. Use this framework for entertainment, education, or pattern exploration — not as a guarantee of winning. Good luck, and play responsibly! 🍀