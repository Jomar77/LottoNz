import random
import csv

def generate_lottery_numbers(skewness, mean_mapping, std_dev=10, size=6, low=1, high=40):
    mean = random.choice(mean_mapping[skewness])
    numbers = set()
    while len(numbers) < size:
        num = int(random.gauss(mean, std_dev))
        if low <= num <= high:
            numbers.add(num)
    return sorted(numbers)

def generate_bonus_number(low=1, high=10, std_dev=2):
    while True:
        num = int(random.gauss(5, std_dev))
        if low <= num <= high:
            return num

def entry_exists(entry):
    try:
        with open('lotto_results.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for line in csv_reader:
                if line == entry:
                    return True
    except FileNotFoundError:
        print("jom its broken") # File doesn't exist, so the entry is unique

def main():
    print("Welcome to the Lottery numbers generator")
    num_entries = int(input("How many entries would you like? "))
    mean_mapping = {'l': [13, 17], 'r': [23, 26]}
    
    for _ in range(num_entries):
        skewness = input("Enter 'l' for left skewness or 'r' for right skewness: ").lower()

        if skewness not in mean_mapping:
            print("Invalid input")
            return

        numbers = generate_lottery_numbers(skewness, mean_mapping)
        bonus = generate_bonus_number()
        if entry_exists(numbers):
            print("This entry already exists")
        else:
            print("Entry: " + ','.join(map(str, numbers)) + " Bonus: " + str(bonus))

if __name__ == "__main__":
    main()
