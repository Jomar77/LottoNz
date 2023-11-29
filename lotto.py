import random
import math

def main():
    print("Welcome to the Lottery numbers generator")
    num_entries = int(input("How many entries would you like? "))
    print()
    
    for i in range(num_entries):
        print("Entry", i+1, end=": ")
        
        skewness = input("Enter 'l' for left skewness or 'r' for right skewness: ")
        std_dev = 10
        meanLeft =[14,17]
        meanRight =[20,23]
        
        if skewness.lower() == 'l':
            mean = random.choice(meanLeft)
        elif skewness.lower() == 'r':
            mean = random.choice(meanRight)
        else:
            print("Invalid input")
            return
        
        
        numarr = []
        for j in range(6):
            #num should not be repeated
            num = math.ceil(random.gauss(mean, std_dev))
    
            #check if num is already in the array, then append it
            
            while num < 1 or num > 40 or check(num, numarr):
                num = math.ceil(random.gauss(mean, std_dev))
                
            numarr.append(num)
            print(numarr[j], end=" ")
        

        num = math.ceil(random.gauss(5, 3))
        
        while num < 1 or num > 10 or check(num, numarr):
            num = math.ceil(random.gauss(5, 2))
        
        print("Bonus:", num)

        
        if checkFile(numarr):
            print("This entry already exists")
            break

    print()

#recursive function that checks if the number is already in the array
def check(num, numarr):
    return num in numarr

import csv



#check if the list above is in the csv file

def checkFile(List):
    with open('output.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        
        for line in csv_reader:
            if line == List:
                return True
    return False


main()