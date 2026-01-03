import pandas as pd
import json
from pathlib import Path

def excel_to_json():
    """Convert december.xlsx to results.json format for the React app"""
    
    # Read the Excel file
    excel_path = Path(__file__).parent / 'lotto-data' / 'december.xlsx'
    df = pd.read_excel(excel_path, sheet_name='Lotto Powerball')
    
    # Convert to the required JSON structure
    results = []
    
    for _, row in df.iterrows():
        # Extract date
        date_value = row['Date']
        
        # Format date as string
        if pd.notna(date_value):
            date_str = pd.to_datetime(date_value).strftime('%Y-%m-%d')
        else:
            continue
            
        # Extract main numbers from columns '1' through '6'
        numbers = []
        for col in ['1', '2', '3', '4', '5', '6']:
            if col in df.columns and pd.notna(row[col]):
                numbers.append(int(row[col]))
        
        # Extract powerball
        powerball = None
        if 'Powerball Number' in df.columns and pd.notna(row['Powerball Number']):
            powerball = int(row['Powerball Number'])
            
        # Only add if we have complete data
        if len(numbers) == 6 and powerball is not None:
            results.append({
                'date': date_str,
                'numbers': sorted(numbers),
                'powerball': powerball
            })
    
    # Sort by date (most recent first)
    results.sort(key=lambda x: x['date'], reverse=True)
    
    # Write to JSON file
    output_path = Path(__file__).parent.parent / 'Frontend' / 'public' / 'results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(results)} lottery results to {output_path}")
    print(f"First result: {results[0]}")
    print(f"Last result: {results[-1]}")

if __name__ == '__main__':
    excel_to_json()
