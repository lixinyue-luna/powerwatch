# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_EPTR.py
Get power plant data from EPTR and convert to Power Watch format.
"""

import csv
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"GLOBAL"
SOURCE_NAME = u"EPTR"
SOURCE_URL = "http://prtr.ec.europa.eu/"
SAVE_CODE = u"EPTR"
RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, 
    filename = "EPTR-plants.csv")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", 
    filename = "EPTR_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
YEAR_UPDATED = 2014

# optional raw file(s) download
URL = ""
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
COLNAMES = ["facilityname", "countryname", "facilityreportid", 
    "parentcompanyname", "lat", "long"]

# read file line-by-line
with open(RAW_FILE_NAME,'rU') as f:
    datareader = csv.reader(f)
    # warning = datareader.next()
    headers = [x.lower() for x in datareader.next()]
    name_col = headers.index(COLNAMES[0])
    country_col = headers.index(COLNAMES[1])
    plant_id_col = headers.index(COLNAMES[2])
    company_col = headers.index(COLNAMES[3])
    latitude_col = headers.index(COLNAMES[4])
    longitude_col = headers.index(COLNAMES[5])
    # generation_col = headers.index(COLNAMES[6])

    # read each row in the file
    count = 1
    capacity = 0   # no capacity data in EPTR
    fuel = u"Unknown"   # no fuel data in EPTR

    for row in datareader:
        try:
            name = u"{}".format(row[name_col])
            # name = pw.format_string(row[name_col], encoding = 'utf-8')
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
        # try:
        #     generation_GWh = float(row[generation_col]) / 1000
        # except:
        #     print("Error: Can't read generation for plant {0}".format(name))
        #     generation_GWh = 0.0

        # assign ID number
        idnr = pw.make_id(SAVE_CODE,idnr)
        new_location = pw.LocationObject("",latitude,longitude)
        new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
            plant_location=new_location,plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL,
            plant_owner=owner)
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
