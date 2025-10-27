import pandas as pd
import numpy as np
from scipy import stats

def determine_gaussian_side(df, start_col='C', end_col='H'):
    """
    Determine which side of a Gaussian bell curve each row falls on.
    
    Parameters:
    df: DataFrame with data
    start_col: Starting column (default 'C')  
    end_col: Ending column (default 'H')
    
    Returns:
    DataFrame with original data plus analysis columns
    """
    
    # Convert column letters to indices if needed
    if isinstance(start_col, str):
        start_idx = ord(start_col.upper()) - ord('A')
        end_idx = ord(end_col.upper()) - ord('A')
        columns = df.columns[start_idx:end_idx+1]
    else:
        columns = df.columns[start_col:end_col+1]
    
    results = df.copy()
    
    # For each row, analyze the distribution
    for idx, row in df.iterrows():
        # Get values from specified columns
        values = row[columns].dropna().astype(float)
        
        if len(values) < 3:  # Need minimum data points
            results.loc[idx, 'gaussian_side'] = 'insufficient_data'
            results.loc[idx, 'side_confidence'] = 0
            continue
        
        # Calculate statistics
        mean_val = np.mean(values)
        median_val = np.median(values)
        std_val = np.std(values)
        
        # Method 1: Compare mean to median
        if abs(mean_val - median_val) < 0.1 * std_val:
            side = 'center'
            confidence = 1.0 - abs(mean_val - median_val) / std_val
        elif mean_val > median_val:
            side = 'right_skewed'  # Tail extends to the right
            confidence = abs(mean_val - median_val) / std_val
        else:
            side = 'left_skewed'   # Tail extends to the left
            confidence = abs(mean_val - median_val) / std_val
        
        # Method 2: Skewness test (more robust)
        skewness = stats.skew(values)
        
        if abs(skewness) < 0.5:
            side_skew = 'center'
            conf_skew = 1.0 - abs(skewness) / 0.5
        elif skewness > 0:
            side_skew = 'right_skewed'
            conf_skew = min(abs(skewness) / 2.0, 1.0)
        else:
            side_skew = 'left_skewed'
            conf_skew = min(abs(skewness) / 2.0, 1.0)
        
        # Method 3: Position relative to theoretical normal distribution
        # Fit normal distribution and see where most data falls
        fitted_mean, fitted_std = stats.norm.fit(values)
        
        # Count values on each side of the fitted mean
        left_count = sum(v < fitted_mean for v in values)
        right_count = sum(v > fitted_mean for v in values)
        
        if abs(left_count - right_count) <= 1:
            side_position = 'center'
        elif left_count > right_count:
            side_position = 'left_heavy'
        else:
            side_position = 'right_heavy'
        
        # Combine methods for final determination
        results.loc[idx, 'mean_median_side'] = side
        results.loc[idx, 'skewness_side'] = side_skew
        results.loc[idx, 'position_side'] = side_position
        results.loc[idx, 'skewness_value'] = skewness
        results.loc[idx, 'mean_value'] = mean_val
        results.loc[idx, 'median_value'] = median_val
        results.loc[idx, 'std_value'] = std_val
        
        # Final consensus
        sides = [side, side_skew, side_position]
        if sides.count('left_skewed') + sides.count('left_heavy') >= 2:
            final_side = 'left'
        elif sides.count('right_skewed') + sides.count('right_heavy') >= 2:
            final_side = 'right' 
        else:
            final_side = 'center'
            
        results.loc[idx, 'gaussian_side'] = final_side
        results.loc[idx, 'confidence'] = np.mean([confidence, conf_skew])
    
    return results

# Alternative simpler version focusing just on lottery numbers
def lottery_gaussian_side(df, num_columns):
    """
    Simplified version for lottery number analysis.
    
    Parameters:
    df: DataFrame with lottery numbers
    num_columns: List of column names containing the numbers
    """
    results = []
    
    for idx, row in df.iterrows():
        numbers = [row[col] for col in num_columns if pd.notna(row[col])]
        
        if len(numbers) < 4:
            results.append({'row': idx, 'side': 'insufficient', 'score': 0})
            continue
            
        # Calculate center point (for lottery 1-40, center is 20.5)
        center_point = 20.5
        
        # Calculate weighted position
        avg_position = np.mean(numbers)
        
        # Determine side based on average position
        if abs(avg_position - center_point) < 2:
            side = 'center'
            score = 1.0 - abs(avg_position - center_point) / 2
        elif avg_position > center_point:
            side = 'right'
            score = min((avg_position - center_point) / 10, 1.0)
        else:
            side = 'left' 
            score = min((center_point - avg_position) / 10, 1.0)
        
        # Additional spread analysis
        spread = max(numbers) - min(numbers)
        if spread > 30:
            spread_type = 'wide'
        elif spread < 15:
            spread_type = 'tight'
        else:
            spread_type = 'normal'
            
        results.append({
            'row': idx,
            'side': side,
            'score': score,
            'avg_position': avg_position,
            'spread': spread,
            'spread_type': spread_type,
            'numbers': numbers
        })
    
    return pd.DataFrame(results)

# Example usage:
# df = pd.read_excel('your_file.xlsx')
# analysis = determine_gaussian_side(df, 'C', 'H')
# print(analysis[['gaussian_side', 'confidence', 'skewness_value']])
# Try to load the real Excel sheet; fall back to the screenshot sample if anything goes wrong.
file_path = r"lotto-data\october.xlsx"
sheet_name = 'Lotto Powerball'

try:
    print(f"Attempting to read Excel file: {file_path} (sheet: {sheet_name})")
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Ensure the expected columns (rename if the sheet uses positional headers)
    expected_cols = [
        "Date", "Draw Number", "Num1", "Num2", "Num3",
        "Num4", "Num5", "Num6", "Bonus Number", "Powerball Number"
    ]
    if len(df.columns) >= len(expected_cols):
        # If headers aren't exact, map by position
        df.columns = expected_cols + list(df.columns[len(expected_cols):])
    else:
        # If too few columns, raise to trigger fallback
        raise ValueError("Unexpected column layout in Excel sheet")

    # Diagnostics
    total_rows = len(df)
    main_cols = ["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]
    rows_with_all_main = df.dropna(subset=main_cols).shape[0]
    rows_with_powerball = df["Powerball Number"].notna().sum() if "Powerball Number" in df.columns else 0
    print(f"Total rows in sheet: {total_rows}")
    print(f"Rows with all 6 main numbers present: {rows_with_all_main}")
    print(f"Rows with Powerball present: {rows_with_powerball}")

    # Keep rows that have all 6 main numbers even if Powerball missing
    df_cleaned = df.dropna(subset=main_cols, how='any').copy()

    # Coerce types
    df_cleaned["Date"] = pd.to_datetime(df_cleaned["Date"], dayfirst=False, errors='coerce')
    numeric_columns = main_cols + ["Draw Number", "Bonus Number", "Powerball Number"]
    for col in numeric_columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

    print(f"Using {len(df_cleaned)} usable rows from Excel sheet (main numbers present).")

except Exception as e:
    print(f"Could not load Excel sheet ({e}); falling back to embedded sample data.")

    # create dataframe from screenshot (two example rows)
    df_cleaned = pd.DataFrame([
        {
            "Date": "9/20/2025",
            "Draw Number": 2518,
            "Num1": 23,
            "Num2": 21,
            "Num3": 13,
            "Num4": 32,
            "Num5": 22,
            "Num6": 9,
            "Bonus Number": 27,
            "Powerball Number": 1,
        },
        {
            "Date": "9/17/2025",
            "Draw Number": 2517,
            "Num1": 37,
            "Num2": 14,
            "Num3": 12,
            "Num4": 6,
            "Num5": 20,
            "Num6": 33,
            "Bonus Number": 3,
            "Powerball Number": 2,
        }
    ])

    # Parse Date and coerce numeric columns for the fallback sample
    df_cleaned["Date"] = pd.to_datetime(df_cleaned["Date"], dayfirst=False, errors='coerce')
    numeric_columns = ["Draw Number", "Num1", "Num2", "Num3", "Num4", "Num5", "Num6", "Bonus Number", "Powerball Number"]
    df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors='coerce')
# For lottery data:
lottery_analysis = lottery_gaussian_side(df_cleaned, ['Num1', 'Num2', 'Num3', 'Num4', 'Num5', 'Num6'])
print(lottery_analysis.head(10))