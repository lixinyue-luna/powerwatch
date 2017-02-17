# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_CARMA.py
Get power plant data from CARMA and convert to Power Watch format.
Data Source: CARMA
Additional information: CARAM data api: http://carma.org/api/
Notes:
- The field "energy_2009" is the generation in MWh for 2009. Divide by 1000 to get GWh.
Issues:
- Need to implement online data download. Currently retrieves data in JSON; need to conver to CSV
or rewrite parser. Also, file is very large so bulk download is slow.
"""

import csv
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"GLOBAL"
SOURCE_NAME = u"CARMA"
SOURCE_URL = "http://carma.org/"
SAVE_CODE = u"CARMA"
RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "CARMA_all_plants.csv")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "carma_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
YEAR_UPDATED = 2009

# optional raw file(s) download
URL = "http://carma.org/javascript/ajax-lister.php?type=plant&sort=carbon_present%20DESC&page=1&time=present&m1=world&m2=plant&m3=&m4=&export=make"
FILES = {RAW_FILE_NAME: URL}
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
COLNAMES = ["name", "country", "plant_id", "company", "latitude", "longitude", "energy_2009"]

# read file line-by-line
with open(RAW_FILE_NAME,'rU') as f:
    datareader = csv.reader(f)
    warning = datareader.next()
    headers = [x.lower() for x in datareader.next()]
    name_col = headers.index(COLNAMES[0])
    country_col = headers.index(COLNAMES[1])
    plant_id_col = headers.index(COLNAMES[2])
    company_col = headers.index(COLNAMES[3])
    latitude_col = headers.index(COLNAMES[4])
    longitude_col = headers.index(COLNAMES[5])
    generation_col = headers.index(COLNAMES[6])

    # read each row in the file
    count = 1
    capacity = 0   # no capacity data in CARMA
    fuel = u"Unknown"   # no fuel data in CARMA

    for row in datareader:
        try:
            name = pw.format_string(row[name_col])
        except:
            print(u"Error: Can't read plant name.")
            continue                       # must have plant name - don't read plant if not
        try:
        	idnr = int(row[plant_id_col])
        except:
        	print(u"Error: Can't read ID for plant {0}.".format(name))
        	continue
        try:
            latitude = float(row[latitude_col])
            longitude = float(row[longitude_col])
        except:
            latitude, longitude = 0.0, 0.0
        try:
        	owner = pw.format_string(row[company_col])
        except:
        	print(u"Error: Can't read owner for plant {0}.".format(name))
        	owner = u"Unknown"
        try:
        	country = pw.standardize_country(row[country_col],country_thesaurus)
        except:
        	print("Error: Can't read country for plant {0}.".format(name))
        	country = u"Unknown"
        try:
            generation_GWh = float(row[generation_col]) / 1000
        except:
            print("Error: Can't read generation for plant {0}".format(name))
            generation_GWh = 0.0

        # assign ID number
        idnr = pw.make_id(SAVE_CODE,idnr)
        new_location = pw.LocationObject("",latitude,longitude)
        new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
            plant_location=new_location,plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL,
            plant_owner=owner,plant_generation=generation_GWh,plant_gen_year=YEAR_UPDATED)
        plants_dictionary[idnr] = new_plant
        count += 1

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)
#
# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
