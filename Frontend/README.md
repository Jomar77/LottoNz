# LottoNz Smart Picker - Frontend

Modern React application for generating weighted lottery numbers based on historical data.

## Features

✨ **Smart Number Generation**
- Frequency-weighted algorithm based on historical data (1834 draws from 2001-2025)
- Customizable preferences: spread (tight/wide/mixed), leaning (left/middle/right), consecutive numbers
- Real-time client-side generation

🎨 **Modern UI**
- Beautiful NZ-themed green/blue color palette
- Fully responsive mobile-first design
- Smooth animations and transitions
- Collapsible preferences panel

📊 **Data-Driven**
- Latest draw results displayed
- Historical data from december.xlsx
- JSON-based data format

## Setup

### 1. Install Dependencies
```bash
cd Frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```
Open [http://localhost:5173/LottoNz/](http://localhost:5173/LottoNz/)

### 3. Build for Production
```bash
npm run build
```
Output will be in `Frontend/dist/`

### 4. Preview Production Build
```bash
npm run preview
```

## Project Structure

```
Frontend/
├── public/
│   └── results.json          # Historical lottery data (1834 draws)
├── src/
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # React entry point
│   ├── index.css            # Global styles
│   ├── types.ts             # TypeScript interfaces
│   ├── dataService.ts       # Data fetching logic
│   ├── utils.ts             # Number generation algorithms
│   └── vite-env.d.ts        # Vite type definitions
├── index.html               # HTML entry point
├── package.json             # Dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── postcss.config.js        # PostCSS configuration
```

## Algorithm Details

### Weighted Selection
- Numbers are weighted based on their historical frequency
- More frequent numbers have higher probability of selection

### Leaning Bias
- **Left** (1-13): 2x weight multiplier
- **Middle** (15-25): 2x weight multiplier  
- **Right** (27-40): 2x weight multiplier

### Spread Constraints
- **Tight**: Max - Min ≤ 20
- **Wide**: Max - Min ≥ 15
- **Mixed**: No constraint

### Consecutive Numbers
- **Yes**: Must include at least one consecutive pair
- **No**: No consecutive numbers allowed

### Powerball
- Randomly generated from 1-10
- No historical weighting applied

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **PostCSS** - CSS processing

## Data Update

To update the lottery data:

1. Place updated Excel file in `Backend/lotto-data/december.xlsx`
2. Run the conversion script:
```bash
cd Backend
python convert_to_json.py
```
3. The `Frontend/public/results.json` file will be updated automatically

## Deployment

The app is configured for GitHub Pages with base path `/LottoNz/`.

To deploy:
1. Build the app: `npm run build`
2. Upload the `dist/` folder to GitHub Pages
3. Ensure `results.json` is accessible

## Environment Variables

The app uses different data sources for dev vs production:
- **Development**: `/results.json` (local file)
- **Production**: GitHub raw URL (configure in `src/dataService.ts`)

## License

Private project for LottoNz Smart Picker

