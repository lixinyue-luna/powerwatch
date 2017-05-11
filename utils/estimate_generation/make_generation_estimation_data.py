# This Python file uses the following encoding: utf-8
"""
PowerWatch
make_generation_estimation_data.py
Make data file for generation estimation ML algorithm.
"""

import sys, os

sys.path.insert(0, os.pardir)
sys.path.insert(0, os.path.join(os.pardir, os.pardir))
import powerwatch as pw

# file locations
#DATABASE_FILE = pw.make_file_path(fileType="src_bin", filename="ARG-Database.bin")
#DATABASE_FILE = pw.make_file_path(fileType="src_bin", filename="USA-Database.bin")
DATABASE_FILE = pw.make_file_path(fileType="src_bin", filename="WRI-Database.bin")

OUTPUT_CSV = "generation_data_wri.csv"

# load databases
plant_dictionary = pw.load_database(DATABASE_FILE)

# write out all generation data to CSV file
plants_with_data = 0
total_plants = 0

missing_data = {'capacity':0, 'generation':0, 'fuel':0, 'year':0, 'location':0}

with open(OUTPUT_CSV,'w') as f:

    f.write('id,country,capacity_mwh,commissioning_year,latitude,longitude,generation_gwh,capacity_factor,fuel1,fuel2,fuel3,fuel4\n')

    for idnr,plant in plant_dictionary.iteritems():

    	total_plants += 1

    	if plant.capacity is pw.NO_DATA_NUMERIC:
    		missing_data['capacity'] += 1
    		continue

    	if plant.generation[0].gwh is None:
    		missing_data['generation'] += 1
    		continue

    	#if plant.generation[0].gwh is None:
    	#	missing_data['generation'] += 1

    	if plant.fuel is pw.NO_DATA_SET:
    		missing_data['fuel'] += 1
    		continue

    	if plant.commissioning_year is pw.NO_DATA_NUMERIC:
    		missing_data['year'] += 1
    		continue

    	if plant.location is pw.NO_DATA_OTHER:
    		missing_data['location'] += 1
    		continue

    	if not plant.location.latitude or not plant.location.longitude:
    		missing_data['location'] += 1
    		continue

		# take first generation object in list - TO FIX
		generation = plant.generation[0].gwh
		country = plant.country
		capacity = plant.capacity
		year = plant.commissioning_year
		latitude = plant.location.latitude
		longitude = plant.location.longitude
		cap_factor = 1000 * generation / (capacity * 24 * 365)
		fuel = ",".join(plant.fuel)

		writestr = "{0},{1},{2},{3},{4},{5},{6},{7},{8}\n".format(idnr,country,capacity,year,latitude,longitude,generation,cap_factor,fuel)
		f.write(writestr)
		plants_with_data += 1

for indicator,val in missing_data.iteritems():
	print("Plants missing {0}: {1}".format(indicator,val))

print("Loaded {0} total plants; {1} with full data for generation estimation.".format(total_plants,plants_with_data))
