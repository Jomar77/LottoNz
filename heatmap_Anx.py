import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations


file_path = r"lotto-data\lotto_results.csv"
df = pd.read_csv(file_path)

def plotter():
    # Load the CSV file
    data = pd.read_csv(file_path, header=None)

    # Number of rows
    num_rows = len(data)

    # Initialize similarity matrix
    similarity_matrix = np.zeros((num_rows, num_rows), dtype=int)

    # Compute similarities
    for i, j in combinations(range(num_rows), 2):
        shared_numbers = len(set(data.iloc[i]) & set(data.iloc[j]))
        similarity_matrix[i, j] = shared_numbers
        similarity_matrix[j, i] = shared_numbers  # Matrix is symmetric

    # Create a heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(similarity_matrix, annot=False, cmap="YlGnBu", cbar=True)
    plt.title("Heatmap of Row Similarities")
    plt.xlabel("Row Index")
    plt.ylabel("Row Index")
    plt.show()

    # Generate a histogram of similarities
    similarities = [similarity_matrix[i, j] for i, j in combinations(range(num_rows), 2)]
    plt.figure(figsize=(8, 6))
    sns.histplot(similarities, bins=range(0, 7), kde=False, color='blue')
    plt.title("Distribution of Shared Numbers Between Row Pairs")
    plt.xlabel("Number of Shared Numbers")
    plt.ylabel("Count of Row Pairs")
    plt.xticks(range(0, 7))
    plt.show()

    # Boxplot for statistical insights
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=similarities, color='orange')
    plt.title("Boxplot of Shared Numbers Between Row Pairs")
    plt.xlabel("Number of Shared Numbers")
    plt.show()



def load_lotto_data(file_path):
    # Read CSV and name columns
    df = pd.read_csv(file_path, header=None)
    df.columns = [f'Num{i+1}' for i in range(6)]
    return df

def combi_counter(df):
    if df.empty:
        print("Error: No data found")
        return [], pd.Series()
        
    # Get all rows as sets
    rows_as_sets = []
    try:
        for index, row in df.iterrows():
            row_set = set(row.values)  # Simplified access to row values
            rows_as_sets.append((index, row_set))
    except Exception as e:
        print(f"Error processing rows: {e}")
        return [], pd.Series()

    # Store matching pairs and their numbers
    matching_pairs = []
    numbers_in_matches = []

    # Compare each pair of rows
    for (idx1, row1), (idx2, row2) in combinations(rows_as_sets, 2):
        if len(row1 & row2) >= 5:
            matching_pairs.append((idx1, idx2))
            numbers_in_matches.extend(list(row1 & row2))

    if not numbers_in_matches:
        print("No matching combinations found")
        return [], pd.Series()

    # Convert to pandas Series for easy counting
    number_freq = pd.Series(numbers_in_matches).value_counts()
    
    # Print analysis
    print("\nAnalysis of rows with 5+ matching numbers:")
    print(f"Total matching pairs found: {len(matching_pairs)}")
    print("\nMost frequent numbers in matching rows:")
    print(number_freq.head())
    
    if numbers_in_matches:
        print("\nStatistical Summary:")
        print(f"Mean: {np.mean(numbers_in_matches):.2f}")
        print(f"Median: {np.median(numbers_in_matches):.2f}")
        print(f"Std Dev: {np.std(numbers_in_matches):.2f}")
    
    return matching_pairs, number_freq

# Main execution
if __name__ == "__main__":
    try:
        df = load_lotto_data(file_path)
        matching_pairs, number_freq = combi_counter(df)
    except FileNotFoundError:
        print("Error: lotto_results.csv file not found")
    except Exception as e:
        print(f"Error: {e}")