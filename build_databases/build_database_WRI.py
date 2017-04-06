# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_WRI.py
Download power plant data from WRI Fusion Tables and convert to Power Watch format.
Data Source: World Resources Institute (manually assembled from multiple sources)
Additional information: https://github.com/Arjay7891/WRI-Powerplant
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
COLNAMES = ["PowerWatch ID", "Name", "Fuel", "Capacity (MW)", "Location", "Plant type", "Age",
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
                    fuel = set([])
                try:
                    latitude = float(row[latitude_col])
                    longitude = float(row[longitude_col])
                except:
                    latitude, longitude = 0.0, 0.0
                try:
                    location = pw.format_string(row[location_col])
                except:
                    location = u""
                try:
                    gen_gwh = float(pw.format_string(row[generation_col].replace(",","")))
                    generation = pw.PlantGenerationObject(gen_gwh)
                except:
                    generation = pw.PlantGenerationObject()
                try:
                    owner = pw.format_string(row[owner_col])
                except:
                    owner = u"Unknown"
                try:
                    source = pw.format_string(row[source_col])
                except:
                    print(u"-Error: Can't read source for plant {0}.".format(name))
                    source = u"Unknown"
                try:
                    url = pw.format_string(row[url_col])
                except:
                    print(u"-Error: Can't read URL for plant {0}.".format(name))
                    url = u"Unknown"

                # assign ID number
                idnr = pw.make_id(SAVE_CODE, int(idnr))
                new_location = pw.LocationObject(location,latitude,longitude)
                new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
                    plant_location=new_location,plant_fuel=fuel,plant_capacity=capacity,
                    plant_owner = owner, plant_generation = generation,
                    plant_source=source,plant_source_url=url)
                plants_dictionary[idnr] = new_plant

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
