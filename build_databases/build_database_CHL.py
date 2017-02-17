# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_chile.py
Get power plant data from Chile and convert to Power Watch format.
Data Source: Comision Nacional de Energia, Chile
Additional information: http://energiaabierta.cl/electricidad/
"""

import csv
import locale
import utm
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"Chile"
SOURCE_NAME = u"Chile"
SAVE_CODE = u"CHL"
SOURCE = u"Energía Abierta (Chile)"
SOURCE_URL = u"http://energiaabierta.cl/electricidad/"
YEAR_POSTED = 2016  # Year of data posted on line
RAW_FILE_NAME = pw.make_file_path(fileType = 'raw', subFolder = SAVE_CODE, filename = 'FILENAME')
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "chile_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")

# other parameters
API_KEY = "eac92f8ccb5a0a408a5985f2031b4f3de84d876d"
API_BASE = "http://cne.cloudapi.junar.com/api/v2/datastreams/DATASET_NAME/data.csv/"
URL_BASE = API_BASE + "?" + "auth_key=" + API_KEY
DATASETS = [{"name":"CENTR-HIDRO","fuel":"Hydro","RAW_FILE_NAME":"chile_power_plants_hydro.csv"},
            {"name":"CENTR-SOLAR","fuel":"Solar","RAW_FILE_NAME":"chile_power_plants_solar.csv"},
            {"name":"CENTR-DE-BIOMA","fuel":"Other","RAW_FILE_NAME":"chile_power_plants_biomass.csv"},
            {"name":"CENTR-EOLIC","fuel":"Wind","RAW_FILE_NAME":"chile_power_plants_wind.csv"},
            {"name":"CENTR-TERMO","fuel":"Various","RAW_FILE_NAME":"chile_power_plants_thermal.csv"}]
COLNAMES = ["propietario","potencia mw","coordenada este","coordenada norte","uso","nombre","combustible"]

# set locale to Spain (Chile is not usually available in locales)
locale.setlocale(locale.LC_ALL,"es_ES")

# TODO: check back in the future to see if the Agency provides location inforamtion in csv files or not
# Disable download for now. The Agency removed location information in some datasets. Use locally saved file instead.
# # optional raw file(s) download
# FILES = {}
# for dataset in DATASETS:
#     RAW_FILE_NAME_this = RAW_FILE_NAME.replace("FILENAME", dataset["RAW_FILE_NAME"])
#     URL = URL_BASE.replace("DATASET_NAME",dataset["name"])
#     FILES[RAW_FILE_NAME_this] = URL
# DOWNLOAD_FILES = pw.download(COUNTRY_NAME, FILES)

print(u"Using {0} file saved locally.").format(COUNTRY_NAME)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# read data from csv and parse
country = SOURCE_NAME
count = 1
for dataset in DATASETS:
    dataset_filename = pw.make_file_path(fileType="raw", subFolder=SAVE_CODE, filename=dataset["RAW_FILE_NAME"])
    with open(dataset_filename, "rbU") as f:
        datareader = csv.reader(f)
        headers = [x.lower() for x in datareader.next()]
        #owner_col = headers.index(COLNAMES[0])
        capacity_col = headers.index(COLNAMES[1])
        coord_east_col = headers.index(COLNAMES[2])
        coord_north_col = headers.index(COLNAMES[3])
        utm_zone_col = headers.index(COLNAMES[4])
        name_col = headers.index(COLNAMES[5])
        if dataset["fuel"] is not "Various":
            fuel_type = pw.standardize_fuel(dataset["fuel"], fuel_thesaurus)
        else:
            fuel_col = headers.index(COLNAMES[6])

        # read each row in the file
        for row in datareader:
            try:
                name = pw.format_string(row[name_col])
            except:
                print(u"Error: Can't read plant name.")
                continue              # must have plant name - don't read plant if not

            if dataset["fuel"] is "Various":
                fuel_type = pw.standardize_fuel(row[fuel_col],fuel_thesaurus)
                #fuel_type_list = row[fuel_col].split("/")
                #fuel_type = [pw.standardize_fuel(ft,fuel_thesaurus) for ft in fuel_type_list]

            try:
                capacity = locale.atof(row[capacity_col])
            except:
                capacity = 0.0
                print("Problem reading capacity for plant {0}; value is {1}".format(name,row[capacity_col]))

            coord_east = locale.atof(row[coord_east_col])
            coord_north = locale.atof(row[coord_north_col])
            utm_zone = int(row[utm_zone_col])
            try:
                (latitude,longitude) = utm.to_latlon(coord_east,coord_north,utm_zone,northern=False)
            except:
                print("Problem: Easting: {0}, Northing: {1} for plant {2}".format(coord_east,coord_north,name))

            # assign ID number, make PowerPlant object, add to dictionary
            idnr = pw.make_id(SAVE_CODE,count)
            new_location = pw.LocationObject(u"",latitude,longitude)
            new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
                plant_location=new_location,plant_fuel=fuel_type,plant_capacity=capacity,
                plant_source=SOURCE,plant_source_url=SOURCE_URL,plant_cap_year=YEAR_POSTED)
            plants_dictionary[idnr] = new_plant
            count += 1

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
