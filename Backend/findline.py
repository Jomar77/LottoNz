import csv
import os

# Example set of numbers to find
desired_numbers = []

def find_line_with_numbers(file_path, numbers_to_find):
    """Finds and prints the line containing the specified set of numbers."""
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        
        for row_number, row in enumerate(reader, start=1):
            # Check if all desired numbers are in the current row
            if all(num in row for num in numbers_to_find):
                print(f"Found numbers {numbers_to_find} in row {row_number}: {row}")
            else:
                #print the line with the nearest output
                print("something here")

            

def main():
    # Ensure the output file exists
    output_file = "lotto_results.csv"

    input_numbers = input("Enter the numbers to find: ")
    desired_numbers = list(map(int, input_numbers.split(',')))
    if not os.path.exists(output_file):
        print(f"{output_file} does not exist.")
        return
    
    find_line_with_numbers(output_file, desired_numbers)

if __name__ == "__main__":
    main()
