import csv
import re

def extract_numbers_from_csv(input_file):
    # Regular expression pattern to match numbers inside brackets
    pattern = re.compile(r'\[(.*?)\]')
    
    with open(input_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        
        # Read each row in the CSV file
        for row in csvreader:
            # Join all columns to form a single string
            text = ' '.join(row)
            
            # Search for patterns matching the regular expression
            match = pattern.search(text)
            if match:
                # Extract the matched group (the part inside the brackets)
                numbers = match.group(1)
                numbers = numbers.replace("'", "").replace("  ", ",")
                # Format the numbers as a comma-separated string
                print(numbers)
               

# Usage example
input_file = 'data.csv'
extract_numbers_from_csv(input_file)
