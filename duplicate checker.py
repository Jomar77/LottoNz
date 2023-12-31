import csv
from collections import defaultdict

def check_duplicates(csv_file, column_numbers):
    # Dictionary to store lines and their counts
    line_counts = defaultdict(int)

    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)

        # Iterate through each line in the CSV file
        for row_number, row in enumerate(reader, start=1):  # Start from line 2
            # Convert the row to a tuple to make it hashable
            row_tuple = tuple(row[:column_numbers])

            # Check for duplicates
            if line_counts[row_tuple] > 0:
                print(f"Duplicate found in line {row_number}: {','.join(map(str, row))}")
            else:
                line_counts[row_tuple] += 1

if __name__ == "__main__":
    csv_file_path = "output.csv"  # Replace with the path to your CSV file
    for i in range(3, 7):
        print(f"Checking for duplicates in first {i} columns...")
        print(check_duplicates(csv_file_path, i))
