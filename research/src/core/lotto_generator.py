import pandas as pd
import random

# Load the Excel file with the correct sheet name
file_path = r"lotto-data\december.xlsx"
sheet_name = 'Lotto Powerball'

# Load the Excel file
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Rename columns to match your Excel structure
df.columns = [
    "Date", "Draw Number", "Num1", "Num2", "Num3", 
    "Num4", "Num5", "Num6", "Bonus Number", "Powerball Number"
]

# --- Diagnostics (helps explain row counts) ---
total_rows = len(df)
main_cols = ["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]
rows_with_all_main = df.dropna(subset=main_cols).shape[0]
rows_with_powerball = df["Powerball Number"].notna().sum()
print(f"Total rows in sheet: {total_rows}")
print(f"Rows with all 6 main numbers present: {rows_with_all_main}")
print(f"Rows with Powerball present: {rows_with_powerball}")

# Clean the data
# Keep any row that contains all six main numbers even if Powerball is missing.
df_cleaned = df.dropna(subset=main_cols, how='any').copy()

# Convert numeric columns to numeric types (Powerball may still have NaNs)
numeric_columns = main_cols + ["Powerball Number"]
df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors='coerce')

print("Loaded data from Lotto Powerball sheet (after keeping rows with full main numbers):")
print(df_cleaned.head())
print(f"Total usable rows (all 6 main numbers present): {len(df_cleaned)}")

# Frequency analysis
all_numbers = df_cleaned[["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]].values.flatten()
all_numbers = [num for num in all_numbers if not pd.isnull(num)]
number_counts = pd.Series(all_numbers).value_counts()

def get_user_preferences():
    """Get user customization preferences."""
    print("\n🎯 CUSTOMIZE YOUR LOTTERY NUMBERS 🎯")
    print("="*50)
    
    # Spread preference
    print("\n1. Number Spread Preference:")
    print("   a) Tight spread (numbers close together)")
    print("   b) Wide spread (numbers spread out)")
    print("   c) Mixed spread (balanced)")
    spread = input("Choose spread (a/b/c): ").lower()
    
    # Leaning preference
    print("\n2. Number Range Preference:")
    print("   l) Left leaning (favor lower numbers 1-20)")
    print("   r) Right leaning (favor higher numbers 21-40)")
    print("   m) Middle focused (favor middle numbers 15-25)")
    leaning = input("Choose leaning (l/r/m): ").lower()
    
    # Consecutive numbers
    print("\n3. Consecutive Numbers:")
    print("   y) Include at least one pair of consecutive numbers")
    print("   n) No preference for consecutive numbers")
    consecutive = input("Include consecutive numbers? (y/n): ").lower()
    
    # Number of entries
    num_entries = int(input("\n4. How many number sets would you like? "))
    
    return spread, leaning, consecutive, num_entries

def apply_leaning_bias(population, weights, leaning_type):
    """Apply bias based on leaning preference."""
    if leaning_type == 'l':  # Left leaning (favor 1-20)
        for i, num in enumerate(population):
            if num <= 20:
                weights[i] *= 2.0  # Double weight for lower numbers
    elif leaning_type == 'r':  # Right leaning (favor 21-40)
        for i, num in enumerate(population):
            if num >= 21:
                weights[i] *= 2.0  # Double weight for higher numbers
    elif leaning_type == 'm':  # Middle focused (favor 15-25)
        for i, num in enumerate(population):
            if 15 <= num <= 25:
                weights[i] *= 2.0  # Double weight for middle numbers
    
    return weights

def has_consecutive_numbers(numbers):
    """Check if the list contains at least one pair of consecutive numbers."""
    sorted_nums = sorted(numbers)
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i + 1] - sorted_nums[i] == 1:
            return True
    return False

def calculate_spread(numbers):
    """Calculate the spread (range) of numbers."""
    return max(numbers) - min(numbers)

def generate_customized_numbers(spread_pref, leaning_pref, consecutive_pref):
    """Generate numbers based on user preferences."""
    max_attempts = 500
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        # Get population and weights
        population = list(number_counts.index)
        weights = list(number_counts.values)
        
        # Apply leaning bias
        weights = apply_leaning_bias(population, weights, leaning_pref)
        
        # Create cumulative weights for weighted sampling
        total = sum(weights)
        cumulative_weights = [w/total for w in weights]
        for i in range(1, len(cumulative_weights)):
            cumulative_weights[i] += cumulative_weights[i-1]
        
        # Generate 6 unique numbers
        generated_numbers = []
        spread_attempts = 0
        
        while len(generated_numbers) < 6 and spread_attempts < 100:
            spread_attempts += 1
            r = random.random()
            for i, weight in enumerate(cumulative_weights):
                if r <= weight:
                    candidate = int(population[i])
                    if candidate not in generated_numbers:
                        # Check spread constraint
                        temp_numbers = generated_numbers + [candidate]
                        if len(temp_numbers) >= 3:  # Check spread after 3 numbers
                            current_spread = calculate_spread(temp_numbers)
                            if spread_pref == 'a' and current_spread > 15:  # Tight spread
                                continue
                            elif spread_pref == 'b' and current_spread < 20:  # Wide spread
                                continue
                        
                        generated_numbers.append(candidate)
                    break
        
        # If we don't have 6 numbers, continue trying
        if len(generated_numbers) < 6:
            continue
        
        # Enforce consecutive preference strictly by rerolling if not met
        if consecutive_pref == 'y' and not has_consecutive_numbers(generated_numbers):
            # Reroll this attempt — do not try to "force" a consecutive by replacing numbers
            continue
        if consecutive_pref == 'n' and has_consecutive_numbers(generated_numbers):
            # User doesn't want consecutive numbers — reroll
            continue
        
        # Final spread check
        final_spread = calculate_spread(generated_numbers)
        if spread_pref == 'a' and final_spread > 20:  # Tight spread final check
            continue
        elif spread_pref == 'b' and final_spread < 15:  # Wide spread final check
            continue
        
        # Check uniqueness against historical data
        if not check_numbers_in_sheet(df_cleaned, generated_numbers):
            return sorted(generated_numbers), final_spread, has_consecutive_numbers(generated_numbers)
    
    # If we can't find a perfect match, return the last generated set
    print(f"Warning: Generated numbers after {max_attempts} attempts (may not meet all preferences)")
    return sorted(generated_numbers), calculate_spread(generated_numbers), has_consecutive_numbers(generated_numbers)

def check_numbers_in_sheet(df, generated_numbers):
    """Check if the exact 6-number combination exists in historical data."""
    generated_set = set(generated_numbers)
    
    for index, row in df.iterrows():
        row_numbers = set([
            row["Num1"], row["Num2"], row["Num3"], 
            row["Num4"], row["Num5"], row["Num6"]
        ])
        row_numbers = {num for num in row_numbers if not pd.isnull(num)}
        
        if generated_set == row_numbers:
            print(f"Found matching combination in draw {row['Draw Number']} on {row['Date']}")
            return True
    
    return False

def display_results(numbers, spread, has_consecutive, powerball, entry_num):
    """Display the generated numbers with analysis."""
    print(f"\n{'='*60}")
    print(f"🎲 ENTRY #{entry_num} - YOUR CUSTOMIZED LOTTO NUMBERS 🎲")
    print(f"{'='*60}")
    print(f"Main Numbers: {', '.join(map(str, numbers))}")
    print(f"Powerball:    {powerball}")
    print(f"Number Spread: {spread} (Range: {min(numbers)} - {max(numbers)})")
    print(f"Consecutive Numbers: {'✓ Yes' if has_consecutive else '✗ No'}")
    print(f"{'='*60}")

# Main execution
def main():
    print("🎰 CUSTOMIZABLE LOTTO NUMBER GENERATOR 🎰")
    
    # Get user preferences
    spread_pref, leaning_pref, consecutive_pref, num_entries = get_user_preferences()
    
    print(f"\n🔄 Generating {num_entries} customized number set(s)...")
    
    for entry in range(1, num_entries + 1):
        # Generate customized numbers
        selected_numbers, spread, has_consec = generate_customized_numbers(
            spread_pref, leaning_pref, consecutive_pref
        )
        
        # Pick random powerball
        powerball = int(random.choice(df_cleaned["Powerball Number"].dropna()))
        
        # Display results
        display_results(selected_numbers, spread, has_consec, powerball, entry)
    
    print(f"\n✨ Generated {num_entries} unique combination(s) that never appeared before! ✨")
    print("Good luck! 🍀")

if __name__ == "__main__":
    main()
