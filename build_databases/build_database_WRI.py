# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_WRI.py
Download power plant data from WRI Fusion Tables and convert to Power Watch format.
Data Source: World Resources Institute (manually assembled from multiple sources)
Additional information: https://github.com/wri/powerwatch
Issues: Requires an API key to retrieve data from Fusion Tables.
"""

import argparse
import csv
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"GLOBAL"
SOURCE_NAME = u"WRI"
SAVE_CODE = u"WRI"
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "wri_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
RAW_FILE_DIRECTORY = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE)
API_KEY_FILE = pw.make_file_path(fileType = "resource", subFolder = "api_keys", filename = "fusion_tables_api_key.txt")

# other parameters as needed
URL_BASE = "https://www.googleapis.com/fusiontables/v2/query?alt=csv&sql=SELECT * FROM "

# set up country dictionary (need this for fusion table keys)
country_dictionary = pw.make_country_dictionary()

# get API key
with open(API_KEY_FILE, 'r') as f:
    API_KEY = f.readline()
FILES = {}
for country_name, country_info in country_dictionary.iteritems():
    if country_info.fusion_table_id:
        RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = country_name + ".csv")
        URL = URL_BASE + country_info.fusion_table_id + "&key=" + API_KEY
        FILES[RAW_FILE_NAME] = URL
# optional raw file download
DOWNLOAD_FILES = pw.download(SOURCE_NAME, FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# specify column names used in raw file
COLNAMES = ["PowerWatch ID", "Name", "Fuel", "Capacity (MW)", "Location", "Plant type", "Commissioning Year",
                "Units", "Owner", "Annual Generation (GWh)", "Source", "URL", "Country", "Latitude",
                "Longitude"]

for afile in os.listdir(RAW_FILE_DIRECTORY):
    if afile.endswith(".csv"):
        country = afile.replace(".csv","")
        with open(os.path.join(RAW_FILE_DIRECTORY,afile),'rU') as f:
            print("Opened {0}".format(afile))
            datareader = csv.reader(f)
            headers = datareader.next()
            id_col = headers.index(COLNAMES[0])
            name_col = headers.index(COLNAMES[1])
            fuel_col = headers.index(COLNAMES[2])
            capacity_col = headers.index(COLNAMES[3])
            location_col = headers.index(COLNAMES[4])
            commissioning_year_col = headers.index(COLNAMES[6])
            owner_col = headers.index(COLNAMES[8])
            generation_col = headers.index(COLNAMES[9])
            source_col = headers.index(COLNAMES[10])
            url_col = headers.index(COLNAMES[11])
            country_col = headers.index(COLNAMES[12])
            latitude_col = headers.index(COLNAMES[13])
            longitude_col = headers.index(COLNAMES[14])

            # read each row in the file
            for row in datareader:
                try:
                    name = pw.format_string(row[name_col])
                    if not name:        # ignore accidental blank lines
                        continue
                except:
                    print(u"-Error: Can't read plant name.")
                    continue                       # must have plant name - don't read plant if not
                try:
                    idnr = str(row[id_col])
                    if not idnr:  # must have plant ID - don't read plant if not
                        print(u"-Error: Null ID for plant {0}.".format(name))
                        continue
                except:
                    print(u"-Error: Can't read ID for plant {0}.".format(name))
                    continue                        # must have plant ID - don't read plant if not
                try:
                    capacity = float(pw.format_string(row[capacity_col].replace(",","")))   # note: may need to convert to MW
                except:
                    print(u"-Error: Can't read capacity for plant {0}; value: {1}".format(name,row[capacity_col]))
                try:
                    fuel = pw.standardize_fuel(row[fuel_col],fuel_thesaurus)
                except:
                    print(u"-Error: Can't read fuel type for plant {0}.".format(name))
                    fuel = pw.NO_DATA_SET
                try:
                    latitude = float(row[latitude_col])
                    longitude = float(row[longitude_col])
                except:
                    latitude, longitude = pw.NO_DATA_NUMERIC, pw.NO_DATA_NUMERIC
                try:
                    location = pw.format_string(row[location_col])
                except:
                    location = pw.NO_DATA_UNICODE
                try:
                    gen_gwh = float(pw.format_string(row[generation_col].replace(",","")))
                    generation = pw.PlantGenerationObject(gen_gwh)
                except:
                    generation = pw.NO_DATA_OTHER
                try:
                    owner = pw.format_string(row[owner_col])
                except:
                    owner = pw.NO_DATA_UNICODE
                try:
                    source = pw.format_string(row[source_col])
                except:
                    print(u"-Error: Can't read source for plant {0}.".format(name))
                    source = pw.NO_DATA_UNICODE
                try:
                    url = pw.format_string(row[url_col])
                except:
                    print(u"-Error: Can't read URL for plant {0}.".format(name))
                    url = pw.NO_DATA_UNICODE
                try:
                    commissioning_year_string = row[commissioning_year_col].replace('"','')
                    if not commissioning_year_string:
                        commissioning_year = pw.NO_DATA_NUMERIC
                    elif (u"-" in commissioning_year_string) or (u"-" in commissioning_year_string) or (u"," in commissioning_year_string):       # different hyphen characters?
                        commissioning_year_1 = float(commissioning_year_string[0:3])     
                        commissioning_year_2 = float(commissioning_year_string[-4:-1])
                        commissioning_year = 0.5*(commissioning_year_1+commissioning_year_2) # todo: need a better method
                    else:
                        commissioning_year = float(commissioning_year_string)
                    if (commissioning_year < 1900) or (commissioning_year > 2020):      # sanity check
                        commissioning_year = pw.NO_DATA_NUMERIC
                except:
                    print(u"-Error: Can't read commissioning year for plant {0}.".format(name))
                    commissioning_year = pw.NO_DATA_NUMERIC

                # assign ID number
                idnr_full = pw.make_id(SAVE_CODE, int(idnr))

                # check if this ID is already in the dictionary - if so, this is a unit
                if idnr_full in plants_dictionary.keys():
                    # update plant
                    existing_plant = plants_dictionary[idnr_full]
                    existing_plant.capacity += capacity
                    existing_plant.fuel.update(fuel)
                    # append generation object - may want to sum generation instead?
                    if generation:
                        existing_plant.generation.append(generation)
                    # if lat/long for this unit, overwrite previous data - may want to change this
                    if latitude and longitude:
                        new_location = pw.LocationObject(location,latitude,longitude)
                        existing_plant.location = new_location

                    # unclear how to handle owner, source, url, commissioning year

                else:
                    new_location = pw.LocationObject(location,latitude,longitude)
                    new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
                        plant_location=new_location,plant_fuel=fuel,plant_capacity=capacity,
                        plant_owner = owner, plant_generation = generation,
                        plant_source=source,plant_source_url=url,
                        plant_commissioning_year=commissioning_year)
                    plants_dictionary[idnr] = new_plant

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
