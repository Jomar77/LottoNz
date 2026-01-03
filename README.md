# LottoNz Smart Picker

A modern, data-driven lottery number generator using weighted algorithms based on historical NZ Lotto Powerball data.

## Project Overview

This project consists of two main components:

### Frontend (React App)
- Modern React 18 + TypeScript application
- Weighted number generation algorithm
- Beautiful, responsive UI with Tailwind CSS
- Customizable generation preferences
- Real-time client-side processing

### Backend (Python Scripts)
- Data scraping and cleaning utilities
- Excel to JSON conversion
- Historical data analysis
- Original Python-based lottery algorithm (lotto_V3.py)

## Quick Start

### Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```

Visit: [http://localhost:5173/LottoNz/](http://localhost:5173/LottoNz/)

### Update Data
```bash
cd Backend
python convert_to_json.py
```

## Features

✨ **Smart Number Generation**
- Frequency-weighted algorithm (1834 historical draws)
- Spread control: tight (≤20), wide (≥15), or mixed
- Leaning bias: left (1-13), middle (15-25), or right (27-40)
- Consecutive number preferences
- Powerball: random 1-10

🎨 **Modern UI**
- NZ-themed green/blue color scheme
- Fully responsive design
- Smooth animations
- Collapsible preferences panel
- Latest draw display

📊 **Data-Driven**
- 1834 historical draws (2001-2025)
- Real-time frequency analysis
- Unique combination validation

## Project Structure

```
LottoNz/
├── Frontend/                 # React application
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   ├── utils.ts         # Generation algorithms
│   │   ├── dataService.ts   # Data fetching
│   │   └── types.ts         # TypeScript types
│   ├── public/
│   │   └── results.json     # Historical data (1834 draws)
│   └── package.json
│
├── Backend/                  # Python scripts
│   ├── lotto_V3.py          # Original Python algorithm
│   ├── convert_to_json.py   # Excel → JSON converter
│   ├── datacleaner.py       # Data cleaning utilities
│   └── lotto-data/
│       └── december.xlsx    # Source data
│
└── README.md                # This file
```

## Algorithm

The weighted algorithm follows these steps:

1. **Calculate Frequencies**: Count occurrences of each number (1-40) in historical data
2. **Apply Leaning Bias**: Multiply weights by 2x for preferred range
3. **Weighted Selection**: Use cumulative probability for random selection
4. **Validate Constraints**: Check spread and consecutive requirements
5. **Generate Powerball**: Random number 1-10 (no weighting)

Max 1000 attempts to find valid combination, falls back to default if needed.

## Data Sources

- **Primary**: `Backend/lotto-data/december.xlsx` (Excel format)
- **Converted**: `Frontend/public/results.json` (JSON format)
- **Format**: `{ date: string, numbers: number[], powerball: number }`

## Technologies

**Frontend:**
- React 18, TypeScript, Vite
- Tailwind CSS, Lucide React
- Modern ES modules

**Backend:**
- Python 3.x
- pandas (Excel processing)
- Selenium (web scraping - optional)

## Development

### Frontend Development
```bash
cd Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Update Lottery Data
```bash
cd Backend
python convert_to_json.py
```

This reads `lotto-data/december.xlsx` and generates `Frontend/public/results.json`.

## Deployment

1. Build the frontend:
```bash
cd Frontend
npm run build
```

2. Deploy `Frontend/dist/` to your hosting service
3. Configure for GitHub Pages (base path: `/LottoNz/`)

## License

Private project - All rights reserved

## Author

Created for NZ Lotto Powerball analysis and smart number generation. 🎰

A customizable New Zealand Lotto Powerball number generator that uses historical data analysis and weighted probability to generate unique lottery number combinations.

## 🌟 Features

- **Historical Data Analysis**: Analyzes past Lotto Powerball draws to calculate number frequencies
- **Customizable Number Generation**:
  - **Spread Control**: Choose tight, wide, or mixed number spreads
  - **Range Bias**: Favor low (1-20), high (21-40), or middle (15-25) numbers
  - **Consecutive Numbers**: Include or exclude consecutive number pairs
- **Duplicate Detection**: Ensures generated combinations have never been drawn before
- **Multiple Entries**: Generate multiple unique number sets in one run
- **Frequency Weighting**: Uses historical frequency data to weight number selection

## 📋 Requirements

- Python 3.7+
- pandas
- openpyxl (for Excel file handling)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/Jomar77/LottoNz.git
cd LottoNz
```

2. Install required packages:
```bash
pip install pandas openpyxl
```

3. Ensure you have the historical data file in the correct location:
   - File path: `lotto-data/december.xlsx`
   - Sheet name: `Lotto Powerball`

## 💻 Usage

### Running the Main Generator

```bash
python lotto_V3.py
```

### Interactive Prompts

The script will guide you through customization options:

#### 1. Number Spread Preference
- **a) Tight spread**: Numbers close together (e.g., 12, 15, 17, 19, 21, 23)
- **b) Wide spread**: Numbers spread far apart (e.g., 3, 12, 19, 28, 35, 40)
- **c) Mixed spread**: Balanced distribution

#### 2. Number Range Preference
- **l) Left leaning**: Favors lower numbers (1-20)
- **r) Right leaning**: Favors higher numbers (21-40)
- **m) Middle focused**: Favors middle range (15-25)

#### 3. Consecutive Numbers
- **y) Yes**: Ensures at least one pair of consecutive numbers (e.g., 14, 15)
- **n) No**: No preference for consecutive numbers

#### 4. Number of Entries
- Enter how many unique number sets you want to generate

### Example Session

```
🎯 CUSTOMIZE YOUR LOTTERY NUMBERS 🎯
==================================================

1. Number Spread Preference:
   a) Tight spread (numbers close together)
   b) Wide spread (numbers spread out)
   c) Mixed spread (balanced)
Choose spread (a/b/c): b

2. Number Range Preference:
   l) Left leaning (favor lower numbers 1-20)
   r) Right leaning (favor higher numbers 21-40)
   m) Middle focused (favor middle numbers 15-25)
Choose leaning (l/r/m): m

3. Consecutive Numbers:
   y) Include at least one pair of consecutive numbers
   n) No preference for consecutive numbers
Include consecutive numbers? (y/n): y

4. How many number sets would you like? 3

🔄 Generating 3 customized number set(s)...

============================================================
🎲 ENTRY #1 - YOUR CUSTOMIZED LOTTO NUMBERS 🎲
============================================================
Main Numbers: 12, 15, 16, 22, 28, 35
Powerball:    8
Number Spread: 23 (Range: 12 - 35)
Consecutive Numbers: ✓ Yes
============================================================
```

## 📁 Project Structure

```
LottoNz/
├── lotto_V3.py              # Main number generator (latest version)
├── lotto_V2.py              # Previous version
├── lotto_V1.py              # Initial version
├── datacleaner.py           # Data cleaning utilities
├── heatmap_Anx.py           # Visualization tools
├── findline.py              # Helper utilities
├── lotto-data/              # Historical lottery data
│   ├── december.xlsx        # Required data file
│   ├── data.csv
│   └── lotto_results.csv
├── dataScrape/              # Web scraping scripts
│   ├── ds_selenium.py
│   └── ds.py
└── *.ipynb                  # Jupyter notebooks for analysis
```

## 🎲 How It Works

1. **Data Loading**: Reads historical Lotto Powerball results from Excel file
2. **Frequency Analysis**: Calculates how often each number has been drawn
3. **Weighted Selection**: Uses frequency data to create probability weights
4. **Bias Application**: Applies user-selected biases (spread, range, consecutive)
5. **Validation**: Checks generated combinations against historical data
6. **Uniqueness Guarantee**: Ensures the combination has never appeared before

## 📊 Data Format

The Excel file should have the following columns:
- Date
- Draw Number
- Num1, Num2, Num3, Num4, Num5, Num6 (Main numbers)
- Bonus Number
- Powerball Number

## ⚙️ Customization

To modify the data source, edit the file path in `lotto_V3.py`:

```python
file_path = r"lotto-data\december.xlsx"
sheet_name = 'Lotto Powerball'
```

## 📝 Additional Files

- **lotto.ipynb**: Jupyter notebook for data exploration
- **powerball.ipynb**: Powerball-specific analysis
- **gaus-alx.ipynb**: Statistical analysis using Gaussian methods
- **heatmap_Anx.py**: Generate heatmaps of number frequency

## ⚠️ Disclaimer

This tool is for entertainment purposes only. Lottery draws are random events, and past results do not influence future outcomes. Please gamble responsibly.

## 📜 License

This project is open source and available for personal use.

## 🤝 Contributing

Feel free to fork this repository and submit pull requests for improvements or new features!

---

**Good luck! 🍀**
