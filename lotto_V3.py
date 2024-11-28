
import pandas as pd


# Load the Excel file and relevant sheet
file_path = r"lotto-data\lotto-1987-2023.xlsx"  # Replace with your file path
sheet_name = 'Winning Number Results'

# Load the sheet, skipping the first 4 rows
df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=4)

# Rename columns for better readability
df.columns = [
    "Draw",
    "Draw Date",
    "Num1",
    "Num2",
    "Num3",
    "Num4",
    "Num5",
    "Num6",
    "Bonus Ball",
    "2nd Bonus Ball",
    "Powerball"
]

# Drop rows where critical number columns are NaN
df_cleaned = df.dropna(subset=["Num1", "Powerball"])

# Convert numerical columns to numeric data types
numeric_columns = ["Num1", "Num2", "Num3", "Num4", "Num5", "Num6", "Powerball"]
df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Display the cleaned dataset
print(df_cleaned.head())


import random

# Combine all six number columns into a single list for analysis
all_numbers = df_cleaned[["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]].values.flatten()
all_numbers = [num for num in all_numbers if not pd.isnull(num)]  # Remove NaN values

# Count the frequency of each number
number_counts = pd.Series(all_numbers).value_counts()

# Select 6 random numbers weighted by frequency



def generate_unique_numbers():
    while True:
        # Convert index to list to use with random.sample
        population = list(number_counts.index)
        weights = list(number_counts.values)
        
        # Create cumulative weights for weighted sampling
        total = sum(weights)
        cumulative_weights = [w/total for w in weights]
        for i in range(1, len(cumulative_weights)):
            cumulative_weights[i] += cumulative_weights[i-1]
            
        # Generate 6 unique numbers using weighted sampling
        generated_numbers = []
        while len(generated_numbers) < 6:
            r = random.random()
            for i, weight in enumerate(cumulative_weights):
                if r <= weight:
                    if population[i] not in generated_numbers:
                        generated_numbers.append(int(population[i]))
                    break
                    
        if not check_numbers_in_sheet(df, generated_numbers):
            return ','.join(map(str, sorted(generated_numbers)))

# Pick a random Powerball from the Powerball column




def check_numbers_in_sheet(df, generated_numbers):
    """
    Check if the generated numbers are present in the DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the lottery numbers.
    generated_numbers (list): A list of numbers to check.

    Returns:
    bool: True if the numbers are present, False otherwise.
    """
    # Convert the generated numbers to a set for easier comparison
    generated_set = set(generated_numbers)

    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        # Extract the numbers from the row
        row_numbers = set(row[["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]].values)
        
        # Check if the generated numbers are a subset of the row numbers
        if generated_set.issubset(row_numbers):
            return True

    return False


selected_numbers = generate_unique_numbers()
powerball = int(random.choice(df_cleaned["Powerball"].dropna()))

# Display the results
print("Your Lotto Numbers:", selected_numbers)
print("Your Powerball:", powerball)
