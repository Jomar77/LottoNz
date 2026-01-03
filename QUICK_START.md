# LottoNz Smart Picker - Quick Start Guide

## 🚀 Getting Started (First Time)

### Step 1: Install Dependencies
```bash
cd Frontend
npm install
```

### Step 2: Start Development Server
```bash
npm run dev
```

### Step 3: Open in Browser
Visit: **http://localhost:5173/LottoNz/**

---

## 🎮 How to Use

### Generate Your Lucky Numbers

1. **Open the app** in your browser
2. **Review latest draw** displayed at the top
3. **(Optional) Customize preferences** by clicking "Generation Preferences"
   - **Spread**: tight/wide/mixed
   - **Leaning**: left/middle/right  
   - **Consecutive**: yes/no
4. **Click "Generate Lucky Numbers"**
5. **View your generated numbers** with animated display

### Default Settings
- Spread: **Wide** (≥15)
- Leaning: **Middle** (15-25 range favored)
- Consecutive: **Yes** (includes consecutive pairs)

---

## 🔧 Common Commands

### Development
```bash
cd Frontend
npm run dev          # Start dev server (http://localhost:5173/LottoNz/)
```

### Production Build
```bash
cd Frontend
npm run build        # Build for production → dist/
npm run preview      # Preview production build
```

### Update Data
```bash
cd Backend
python convert_to_json.py    # Convert Excel → JSON
```

---

## 📊 Understanding the Algorithm

### How It Works
1. **Analyzes** 1834 historical draws (2001-2025)
2. **Calculates** frequency of each number
3. **Applies** your preference weights
4. **Generates** 6 main numbers (1-40)
5. **Adds** random Powerball (1-10)

### Preferences Explained

#### Spread
- **Tight**: Numbers close together (max-min ≤ 20)
  - Example: 12, 15, 17, 19, 21, 23
- **Wide**: Numbers spread out (max-min ≥ 15)
  - Example: 3, 12, 19, 28, 35, 40
- **Mixed**: No constraint

#### Leaning
- **Left**: Favors 1-13 (2x weight)
- **Middle**: Favors 15-25 (2x weight)
- **Right**: Favors 27-40 (2x weight)

#### Consecutive
- **Yes**: Must include pairs like 14,15 or 23,24
- **No**: No consecutive numbers

---

## 📁 Key Files

```
Frontend/
├── src/
│   ├── App.tsx           # Main UI component
│   ├── utils.ts          # Generation algorithm
│   └── dataService.ts    # Data loading
├── public/
│   └── results.json      # Historical data (1834 draws)
└── package.json          # Dependencies

Backend/
├── convert_to_json.py    # Excel → JSON converter
└── lotto-data/
    └── december.xlsx     # Source data
```

---

## 🐛 Troubleshooting

### Development server won't start
```bash
cd Frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Data not loading
- Check `Frontend/public/results.json` exists
- Verify file contains valid JSON
- Re-run: `python Backend/convert_to_json.py`

### Build errors
```bash
cd Frontend
npm run build
# Check TypeScript errors in output
```

---

## 🎯 Tips for Best Results

1. **Try different preferences** to see varied number sets
2. **Use "Mixed" spread** for balanced distribution
3. **Middle leaning** often produces well-distributed numbers
4. **Generate multiple times** to find your favorite combination
5. **Check latest draw** to see recent trends

---

## 📱 Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

---

## 🆘 Need Help?

1. Check `Frontend/README.md` for detailed documentation
2. Review `IMPLEMENTATION_SUMMARY.md` for technical details
3. Examine `Backend/lotto_V3.py` for original algorithm

---

## 🎊 You're Ready!

**Your LottoNz Smart Picker is ready to generate lucky numbers!**

Good luck! 🍀
