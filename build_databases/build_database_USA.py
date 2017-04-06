"""
PowerWatch
build_database_USA.py
Converts plant-level data from EIA-860 and EIA-923 to PowerWatch format.
"""

import xlrd
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"United States of America"
SAVE_CODE  = u"USA"
RAW_FILE_NAME_860_2 = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "2___Plant_Y2015.xlsx")
RAW_FILE_NAME_860_3 = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "3_1_Generator_Y2015.xlsx")
RAW_FILE_NAME_923_2 = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "EIA923_Schedules_2_3_4_5_M_12_2015_Final_Revision.xlsx")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "usa_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
SOURCE = u"U.S. Energy Information Administration"
SOURCE_URL = u"http://www.eia.gov/electricity/data/browser/"
YEAR = 2015

COLS_860_2 = {'name':3, 'idnr':2, 'owner':1, 'lat':9, 'lng':10}
COLS_860_3 = {'idnr':2, 'capacity':15, 'fuel_type':[33,34,35,36]}
COLS_923_2 = {'idnr':0, 'generation':95}
TAB_NAME_860_2 = "Plant"
TAB_NAME_860_3 = "Operable"
TAB_NAME_923_2 = "Page 1 Generation and Fuel Data"


# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# Open workbooks
print("Loading workbooks...")
print("Loading Form 923-2")
wb1 = xlrd.open_workbook(RAW_FILE_NAME_923_2)
ws1 = wb1.sheet_by_name(TAB_NAME_923_2)
print("Loading Form 860-2")
wb2 = xlrd.open_workbook(RAW_FILE_NAME_860_2)
ws2 = wb2.sheet_by_name(TAB_NAME_860_2)
print("Loading Form 860-3")
wb3 = xlrd.open_workbook(RAW_FILE_NAME_860_3)
ws3 = wb3.sheet_by_name(TAB_NAME_860_3)

# read in plants from File 2 of EIA-860
print("Reading in plants...")
plants_dictionary = {}
for row_id in range(2, ws2.nrows):
    rv = ws2.row_values(row_id) # row value
    name = pw.format_string(rv[COLS_860_2['name']])
    idnr = pw.make_id(SAVE_CODE,int(rv[COLS_860_2['idnr']]))
    capacity = 0.0
    generation = pw.PlantGenerationObject()
    owner = pw.format_string(str(rv[COLS_860_2['owner']]))
    try:
        latitude = float(rv[COLS_860_2['lat']])
    except:
        latitude = pw.NO_DATA_NUMERIC
    try:
        longitude = float(rv[COLS_860_2['lng']])
    except:
        longitude = pw.NO_DATA_NUMERIC
    location = pw.LocationObject(u"",latitude,longitude)
    new_plant = pw.PowerPlant(idnr, name, plant_country = COUNTRY_NAME,
        plant_location = location, plant_owner = owner, plant_capacity = capacity, plant_generation = generation,
        plant_cap_year = YEAR, plant_source = SOURCE, plant_source_url = SOURCE_URL)
    plants_dictionary[idnr] = new_plant

print("...loaded {0} plants.".format(len(plants_dictionary)))

# read in capacities from File 3 of EIA-860
print("Reading in capacities...")
for row_id in range(2, ws3.nrows):
    rv = ws3.row_values(row_id)  # row value
    try:
        idnr = pw.make_id(SAVE_CODE,int(rv[COLS_860_3['idnr']]))
    except:
        continue
    if idnr in plants_dictionary.keys():
        plants_dictionary[idnr].capacity += float(rv[COLS_860_3['capacity']])
        for i in COLS_860_3['fuel_type']:
            try:
                if rv[i] == "None":
                    continue
                fuel_type = pw.standardize_fuel(rv[i], fuel_thesaurus)
                plants_dictionary[idnr].fuel.update(fuel_type)
            except:
                continue
    else:
        print("Can't find plant with ID: {0}".format(idnr))
print("...Added plant capacities.")

# read in generation from File 2 of EIA-923
print("Reading in generation...")
for row_id in range(6, ws1.nrows):
    rv = ws1.row_values(row_id)
    idnr = pw.make_id(SAVE_CODE, int(rv[COLS_923_2['idnr']]))
    if idnr in plants_dictionary.keys():
        if not plants_dictionary[idnr].generation[0]:
            generation = pw.PlantGenerationObject.create(0.0, YEAR, source=SOURCE_URL)
            plants_dictionary[idnr].generation[0] = generation
        plants_dictionary[idnr].generation[0].gwh += float(rv[COLS_923_2['generation']])/1000
    else:
        print("Can't find plant with ID: {0}".format(idnr))
print("...Added plant generations.")
print("...finished.")

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# pickle database
pw.save_database(plants_dictionary, SAVE_CODE, SAVE_DIRECTORY)
print("Pickled database to {0}".format(SAVE_DIRECTORY))
