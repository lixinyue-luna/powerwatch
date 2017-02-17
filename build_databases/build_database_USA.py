"""
PowerWatch
build_database_USA.py
Converts plant-level data from EIA-860 to PowerWatch format.
"""

import xlrd
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"United States of America"
SAVE_CODE  = u"USA"
RAW_FILE_NAME_2 = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "2___Plant_Y2014_Data_Early_Release.xlsx")
RAW_FILE_NAME_3 = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "3_1_Generator_Y2014_Data_Early_Release.xlsx")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "usa_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
SOURCE = u"U.S. Energy Information Administration"
SOURCE_URL_860 = u"http://www.eia.gov/electricity/data/eia860/"
YEAR_POSTED = 2014

COLS_2 = {'name':4, 'idnr':3, 'owner':2, 'lat':10, 'lng':11}
COLS_3 = {'idnr':3, 'capacity':15, 'fuel_type':[33,34,35,36,37,38]}
TAB_NAME_2 = "Plant"
TAB_NAME_3 = "Operable"

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# Open workbooks
print("Loading workbooks...")
wb2 = xlrd.open_workbook(RAW_FILE_NAME_2)
ws2 = wb2.sheet_by_name(TAB_NAME_2)
wb3 = xlrd.open_workbook(RAW_FILE_NAME_3)
ws3 = wb3.sheet_by_name(TAB_NAME_3)

# read in plants from File 2 of EIA-860
print("Reading in plants...")
plants_dictionary = {}
for row_id in range(3, ws2.nrows):
    rv = ws2.row_values(row_id) # row value
    name = pw.format_string(rv[COLS_2['name']])
    idnr = pw.make_id(SAVE_CODE,int(rv[COLS_2['idnr']]))
    capacity = 0.0
    owner = pw.format_string(str(rv[COLS_2['owner']]))
    try:
        latitude = float(rv[COLS_2['lat']])
    except:
        latitude = 0.0
    try:
        longitude = float(rv[COLS_2['lng']])
    except:
        longitude = 0.0
    location = pw.LocationObject(u"",latitude,longitude)
    new_plant = pw.PowerPlant(idnr, name, plant_country = COUNTRY_NAME,
        plant_location = location, plant_owner = owner, plant_capacity = capacity,
        plant_cap_year = YEAR_POSTED, plant_source = SOURCE, plant_source_url = SOURCE_URL_860)
    plants_dictionary[idnr] = new_plant

print("...loaded {0} plants.".format(len(plants_dictionary)))

# read in capacities from File 3 of EIA-860
print("Reading in capacities...")
for row_id in range(3, ws3.nrows):
    rv = ws3.row_values(row_id)  # row value
    idnr = pw.make_id(SAVE_CODE,int(rv[COLS_3['idnr']]))
    if idnr in plants_dictionary.keys():
        plants_dictionary[idnr].capacity += float(rv[COLS_3['capacity']])
        for i in COLS_3['fuel_type']:
            try:
                if rv[i] == "None": continue
                fuel_type = pw.standardize_fuel(rv[i], fuel_thesaurus)
                plants_dictionary[idnr].fuel.update(fuel_type)
            except:
                continue
    else:
        print("Can't find plant with ID: {0}".format(idnr))
print("...finished.")

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# pickle database
pw.save_database(plants_dictionary, SAVE_CODE, SAVE_DIRECTORY)
print("Pickled database to {0}".format(SAVE_DIRECTORY))
