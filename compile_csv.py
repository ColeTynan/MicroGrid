#Compile CSV : This is used by the "controller" pi to compile all the data files sent to it from the agents within
# the migrogrid into one, easily digestible, pretty little file. 

import csv
import os
import sys

#Go through files, ordered by pi number, and copy all data into an array for each pi. (being the g_Star data)
#Create output file and print out data row by row. Must make it variable for a different number of pis somehow...

directory = "/home/pi/csvFiles/"
num_of_pis = sys.argv[1]
database = list()
database.append(list()) #the first list containing the labels of each row

numElems = 0
for filename in os.listdir(directory):
	if filename.endswith(".CSV") or filename.endswith(".csv"):
		with open(directory + filename, 'r') as input_file:
			reader = csv.reader(input_file, delimiter=',')		
			database[0].append(filename)
			for row in reader:
				while True:
					try:
						database[int(row[0])].append(row[2])
						break
					except:
						database.append(list())

with open('results.csv', 'w+') as output_file:
	out_writer = csv.writer(output_file, delimiter=',')
	for i in range(0,len(database)):
		out_writer.writerow(database[i])
