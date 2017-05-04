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
DATABASE_ARG = pw.make_file_path(fileType="src_bin", filename="ARG-Database.bin")
DATABASE_USA = pw.make_file_path(fileType="src_bin", filename="USA-Database.bin")
OUTPUT_CSV = "generation_data.csv"

# load databases
plant_dictionary_ARG = pw.load_database(DATABASE_ARG)
plant_dictionary_USA = pw.load_database(DATABASE_USA)

# write out all generation data to CSV file
plants_with_data = 0
total_plants = 0
with open(OUTPUT_CSV,'w') as f:

    f.write('id,country,capacity_mwh,commissioning_year,latitude,longitude,generation_gwh,capacity_factor,fuel1,fuel2,fuel3,fuel4\n')

    for idnr,plant in plant_dictionary_USA.iteritems():

    	total_plants += 1

        if (plant.capacity is not pw.NO_DATA_NUMERIC) and (plant.generation is not None) and (plant.fuel is not None):
            if (plant.location is not None) and (plant.location.latitude is not pw.NO_DATA_NUMERIC) and (plant.location.longitude is not pw.NO_DATA_NUMERIC):
            	if (plant.commissioning_year) and (plant.generation[0].gwh is not None):

            		# take first generation object in list - TO FIX
            		genobj = plant.generation[0]
            		generation = genobj.gwh

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

print("Loaded {0} total plants; {1} with full data for generation estimation.".format(total_plants,plants_with_data))
