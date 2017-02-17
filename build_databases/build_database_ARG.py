# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_argentina.py
Get power plant data from Argentina and convert to PowerWatch format.
Data Source: Ministerio de Energia y Mineria, Argentina
Date Portal: http://datos.minem.gob.ar/index.php
Additional information: http://datos.minem.gob.ar/api/search/dataset?q=centrales
Additional information: http://datos.minem.gob.ar/api/rest/dataset/
Additional information: https://www.minem.gob.ar/www/706/24621/articulo/noticias/1237/aranguren-e-ibarra-presentaron-el-portal-de-datos-abiertos-del-ministerio-de-energia-y-mineria.html
"""

import csv
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"Argentina"
SOURCE_NAME = u"Ministerio de Energía y Minería (Argentina)"
SOURCE_URL = u"http://datos.minem.gob.ar/#groups_cats=.generaci%C3%B3n-energ%C3%ADa-el%C3%A9ctricageneraci%C3%B3n-energ%C3%ADa-el%C3%A9ctrica.generaci%C3%B3n-energ%C3%ADa-el%C3%A9ctrica."
SAVE_CODE = u"ARG"
RAW_FILE_NAME = pw.make_file_path(fileType="raw", subFolder=SAVE_CODE, filename="FILENAME")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "argentina_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
YEAR_ACCESSED = 2016

# other parameters
DATASETS = [{"name":"general",
             "URL": "http://datos.minem.gob.ar/reportes/geo_csv/electrica_generacion_visor_centrales.csv",
             "fuel": "Various",
             "RAW_FILE_NAME": RAW_FILE_NAME.replace("FILENAME", "argentina_power_plants_general.csv")},
            {"name":"biomass",
             "URL": "http://datos.minem.gob.ar/reportes/geo_csv/electrica_generacion_centrales_biomasa.csv",
             "fuel":"Biomass",
             "RAW_FILE_NAME": RAW_FILE_NAME.replace("FILENAME", "argentina_power_plants_biomass.csv")}]

# parse caracteris to get fuel type, return fuel list
def getFuelType(caracteris):
    fuels = set([])
    if not caracteris:
        return [u"Unknown"]
    else:
        try:
            generators = caracteris.split("<br>")[1:]
            for generator in generators:
                features = generator.split(" | ")
                fuel = features[1].split(": ")[1]
                fuel = pw.standardize_fuel(fuel,fuel_thesaurus)
                fuels.update(fuel)
        except:
            fuels = set([])
        return fuels

# optional raw file(s) download
FILES = {}
for dataset in DATASETS:
    FILES[dataset["RAW_FILE_NAME"]] = dataset["URL"]
DOWNLOAD_FILES = pw.download(COUNTRY_NAME, FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# read data from csv and parse
country = COUNTRY_NAME
count = 1
for dataset in DATASETS:
    dataset_CSV = dataset[RAW_FILE_NAME]
    with open(dataset_CSV, "rbU") as fh:
        datareader = csv.reader(fh)
        headers = datareader.next()
        name_col = headers.index(u"central)
        geojson_col = headers.index(u"geojson")
        if dataset["name"] == "general":
            owner_col = headers.index(u"empresa")
            capacity_col = headers.index(u"potenciainstaladamv")
            generators_col = headers.index(u"caracteristicas")
        elif dataset["name"] == "biomass":
            capacity_col = headers.index(u"potenciainsmw")
        for row in datareader:
            try:
                name = pw.format_string(row[name_col])
            except:
                print(u"Error: Can't read plant name.")
                continue
            try:
                capacity = float(row[capacity_col])
            except:
                print(u"Error: Can't read capacity for plant {0}.".format(name))
                capacity = 0.0
            try:
                owner = pw.format_string(row[owner_col])
            except:
                owner = u"Unknown"
            try:
                if dataset["name"] == "general":
                    generators = row[generators_col]
                    fuels = getFuelType(generators)
                elif dataset["name"] == "biomass":
                    fuels = set([u"Biomass"])
            except:
                fuels = set([u"Other"])
            try:
                coords = row[geojson_col].split(",", 1)[1].split(":[")[1].split("]")[0]
                coords = coords.split(",")
                latitude = float(coords[1])
                longitude = float(coords[0])
            except:
                latitude, longitude = 0.0, 0.0

            # assign ID number, make PowerPlant object, add to dictionary
            idnr = pw.make_id(SAVE_CODE,count)
            new_location = pw.LocationObject(u"",latitude,longitude)
            new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_owner=owner,plant_fuel=fuels,
                plant_country=country,plant_location=new_location,plant_capacity=capacity,plant_cap_year=YEAR_ACCESSED,
                plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL)
            plants_dictionary[idnr] = new_plant
            count += 1

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
