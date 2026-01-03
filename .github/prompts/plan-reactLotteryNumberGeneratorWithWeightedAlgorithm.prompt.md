# Plan: React Lottery Number Generator with Weighted Algorithm

Build a client-side React app that fetches historical lottery data from GitHub and generates weighted lucky numbers using frequency analysis and user-customizable constraints, porting the Python logic from [lotto_V3.py](Backend/lotto_V3.py).

## Steps

1. **Set up React project structure** in [Frontend](Frontend) folder with React, TypeScript, Tailwind CSS, and lucide-react dependencies via package.json and configuration files.

2. **Generate results.json from december.xlsx** - Create a conversion script to transform the Excel data into JSON format matching the CSV structure (array of objects with date, numbers array of 6 numbers, and powerball). This JSON will be hosted on GitHub Pages and fetched by the React app.

3. **Create data fetching service** to load `results.json` from GitHub Pages URL on mount, with loading/error states and TypeScript interfaces matching the CSV-based structure (array of objects: `{ date: string, numbers: number[], powerball: number }`).

4. **Port Python frequency-weighted algorithm** to TypeScript in `generateNumbers()` function: calculate frequency distribution from historical data (6 main numbers only), implement cumulative probability weighted random selection (replicating the `random.choices` logic), add constraint validation for spread preferences (tight ≤20, wide ≥15), leaning bias (low/high/middle with 2x weight multiplier), and consecutive number preferences. Powerball (1-10) will be generated randomly client-side without weighting.

5. **Build UI components** in [App.tsx](Frontend/App.tsx): header with "LottoNz Smart Picker" title, latest result display (most recent draw date + numbers), "Generate Numbers" button with integrated dropdown/accordion for preference controls (spread: tight/wide/mixed, leaning: left/right/middle, consecutive: yes/no) with default settings (wide, middle, yes), and output display area highlighting the 6 main numbers plus powerball with proper styling.

6. **Apply Tailwind CSS styling** with green/blue NZ-themed color palette, mobile-responsive layout (card-based design), smooth animations for number generation, collapsible dropdown for preferences, and attractive visual hierarchy using gradients, shadows, and proper spacing.

7. **Add helper functions** for spread calculation (max - min), consecutive detection (sorted pair comparison), historical uniqueness check (set intersection with past draws), powerball random generation (1-10), and number formatting/display utilities.

## Implementation Details

### Data Structure
- **results.json format**: `[{ "date": "2023-10-25", "numbers": [1, 2, 3, 4, 5, 6], "powerball": 7 }, ...]`
- Source data: Backend/december.xlsx (sheet: 'Lotto Powerball')
- JSON will be generated from Excel and hosted for GitHub Pages consumption

### Default Settings
- **Spread**: Wide (≥15)
- **Leaning**: Middle (numbers 15-25 get 2x weight)
- **Consecutive**: Yes (must include at least one consecutive pair)

### Powerball Generation
- Client-side random generation from range 1-10
- No historical weighting applied to powerball numbers
