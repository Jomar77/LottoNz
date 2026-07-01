import pandas as pd
import json
from pathlib import Path


def _find_excel_file() -> Path:
    """Find december.xlsx across supported project layouts."""
    here = Path(__file__).resolve()
    src_dir = here.parent.parent
    backend_dir = src_dir.parent
    repo_dir = backend_dir.parent

    candidates = [
        src_dir / 'lotto-data' / 'december.xlsx',
        backend_dir / 'lotto-data' / 'december.xlsx',
        repo_dir / 'data' / 'raw' / 'december.xlsx',
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    candidate_list = "\n".join(f"- {p}" for p in candidates)
    raise FileNotFoundError(
        "Could not find december.xlsx in any known location. Checked:\n"
        f"{candidate_list}"
    )


def _resolve_results_output() -> Path:
    """Resolve frontend/public/results.json path with a fallback layout."""
    here = Path(__file__).resolve()
    repo_dir = here.parents[3]

    primary = repo_dir / 'frontend' / 'public' / 'results.json'
    fallback = repo_dir / 'Frontend' / 'public' / 'results.json'

    if primary.parent.exists() or not fallback.parent.exists():
        return primary
    return fallback


def excel_to_json():
    """Convert december.xlsx to results.json format for the React app"""
    
    # Read the Excel file
    excel_path = _find_excel_file()
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
    output_path = _resolve_results_output()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(results)} lottery results to {output_path}")
    if results:
        print(f"First result: {results[0]}")
        print(f"Last result: {results[-1]}")
    else:
        print("No valid rows found in the spreadsheet.")

if __name__ == '__main__':
    excel_to_json()
