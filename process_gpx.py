import sys
import re
from csv import writer

# Open GPX file and read data
filename_in = sys.argv[1]
with open(filename_in) as file:
	raw = file.read()

# Use Regex to grab all lat/lon pairs
pattern = re.compile(r'lat="(?P<lat>\d+.\d+)" lon="(?P<lon>\d+.\d+)">\n\s+<ele>(?P<ele>\d+)<')
dat = pattern.findall(raw)

# Write the lat/lon pairs to a CSV file
filename_out = filename_in[0:-4] + '.csv'
with open(filename_out, "w") as file:
	csv_writer = writer(file)
	csv_writer.writerow(['latitude','longitude','elevation'])
	for row in dat:
		csv_writer.writerow(row)