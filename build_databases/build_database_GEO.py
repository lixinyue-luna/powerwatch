# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_GEO.py
Get power plant data from GEO and convert to Power Watch format.
Data Source: Global Energy Observatory
Additional information: GEO information is at http://globalenergyobservatory.org/ .
Data downloaded via https://morph.io/coroa/global_energy_observatory_power_plants .
<<<<<<< Updated upstream
Includes code from @cbdavis GEO_to_ElasticSearch.py .
Notes:
- Use GEO's own ID number to enable concordance file to match. Don't convert to PW format here.
Issues:
- GEO includes up to 16 owners in fields called 'ownerN' (N=1 to 16). We only read owner1 for now.
- Unclear how to define reporting year for capacity and generation.
- Unclear how "expected annual generation" and "average annual generation" are different,
or which one to use.
=======
Includes code from @cbdavis GEO_to_ElasticSearch.py .
>>>>>>> Stashed changes
"""

import sqlite3
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"GLOBAL"
SOURCE_NAME = u"GEO"
SAVE_CODE = u"GEODB"  # don't use 'GEO' to avoid conflict with country of Georgia
RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "geo-database.db")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "geodb_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
SOURCE_URL = "http://globalenergyobservatory.org"
URL_BASE = "https://morph.io/coroa/global_energy_observatory_power_plants"
URL_END = "/data.sqlite?key=RopNCJ6LtIx9%2Bdp1r%2BQV"

# optional raw file(s) download
URL = URL_BASE + URL_END
FILES = {RAW_FILE_NAME:URL}
DOWNLOAD_FILES = pw.download(SOURCE_NAME, FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from database
conn = sqlite3.connect(RAW_FILE_NAME)
conn.text_factory = str
c = conn.cursor()
c.execute("SELECT * FROM powerplants")
colnames = list(map(lambda x: x[0].lower(), c.description))

# extract powerplant information from file(s)
print(u"Reading in plants...")

# find columns for variables
name_col        = colnames.index("name")
fuel_col        = colnames.index("type")
country_col     = colnames.index("country")
id_col          = colnames.index("geo_assigned_identification_number")
capacity_col    = colnames.index("design_capacity_mwe_nbr")
owner_col       = colnames.index("owners1")
latitude_col    = colnames.index("latitude_start")
longitude_col   = colnames.index("longitude_start")
location_col    = colnames.index("location")
owner_col       = colnames.index("owners1")
generation_col  = colnames.index("expected_annual_generation_gwh_nbr")
generation_col2 = colnames.index("average_annual_generation_rng1_nbr_gwh")
source          = SOURCE_NAME

# extract data
rows = c.fetchall()
conn.close()

for row in rows:
    try:
        name = pw.format_string(row[name_col])
    except:
        print(u"-Error: Can't read plant name.")
        continue                       # must have plant name - don't read plant if not
    try:
        idnr = int(row[id_col])
    except:
        print(u"-Error: Can't read plant ID: {0}".format(row[id_col]))
        continue                        # must have ID number
    try:
        capacity = float(row[capacity_col])
    except:
        capacity = 0.0
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
        owner = pw.format_string(row[owner_col])
    except:
        print(u"-Error: Can't read owner for plant {0}.".format(name))
        owner = u"Unknown"
    try:
        generation = float(row[generation_col])
    except:
        try:
            generation = float(row[generation_col2])
        except:
            #print(u"-Error: Can't read generation for plant {0}.".format(name))
            generation = 0.0
    try:
        country = pw.standardize_country(row[country_col],country_thesaurus)
    except:
        print(u"-Error: Can't read country for plant {0}.".format(name))
        country = u"Unknown"

    owner = pw.format_string(row[owner_col])
    location = pw.format_string(row[location_col])

    # assign ID number
    idnr = pw.make_id(SAVE_CODE,idnr)
    new_location = pw.LocationObject(location,latitude,longitude)
    new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
        plant_location=new_location,plant_fuel=fuel,plant_capacity=capacity,
        plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL,
        plant_generation=generation,plant_gen_year=2017,plant_cap_year=2017)
    plants_dictionary[idnr] = new_plant

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
