# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_australia.py
Converts GIS data from Australian Renewable Energy Mapping Infrastructure (AREMI) to PowerWatch format.
"""

import xml.etree.ElementTree as ET
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"Australia"
SOURCE_NAME = u"Australian Renewable Energy Mapping Infrastructure"
SOURCE_URL = u"http://services.ga.gov.au/site_3/rest/services/Electricity_Infrastructure/MapServer"
SAVE_CODE = u"AUS"
RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "australia_power_plants.xml")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "australia_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")

# other parameters
API_BASE = "http://services.ga.gov.au/site_3/services/Electricity_Infrastructure/MapServer/WFSServer"
API_CALL = "service=WFS&version=1.1.0&request=GetFeature&typeName=National_Major_Power_Stations"

# optional raw file(s) download
URL = API_BASE + "?" + API_CALL
FILES = {RAW_FILE_NAME:URL}
DOWNLOAD_FILES = pw.download(COUNTRY_NAME, FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# create a dictinary of namespaces
ns = {"gml":"http://www.opengis.net/gml",
    "Electricity_Infrastructure":"http://win-amap-ext03:6080/arcgis/services/Electricity_Infrastructure/MapServer/WFSServer"}

# read data from XML file and parse
count = 1
with open(RAW_FILE_NAME, "rU") as f:
    tree = ET.parse(f)
    root = tree.getroot()
    for station in tree.findall("gml:featureMember", ns):
        plant = station.find("Electricity_Infrastructure:National_Major_Power_Stations", ns)
        name = pw.format_string(plant.find("Electricity_Infrastructure:NAME", ns).text)
        plant_id = int(plant.find("Electricity_Infrastructure:OBJECTID", ns).text)
        try:
            owner = pw.format_string(plant.find("Electricity_Infrastructure:OWNER", ns).text)
        except:
            owner = u"Unknown"
        fuel = pw.standardize_fuel(plant.find("Electricity_Infrastructure:PRIMARYFUELTYPE", ns).text,fuel_thesaurus)
        try:
            capacity = plant.find("Electricity_Infrastructure:GENERATIONMW", ns).text
            capacity = float(capacity)
        except:
            print(u"Error: Can't read capacity for plant {0}.".format(name))
            capacity = 0.0
        coords = plant.find("Electricity_Infrastructure:SHAPE/gml:Point/gml:pos", ns).text.split(" ")
        try:
            latitude = float(coords[0])
            longitude = float(coords[1])
        except:
            latitude, longitude = 0,0

        # # Additional information for future interest
        # operational_status = plant.find('Electricity_Infrastructure:OPERATIONALSTATUS', ns).text)
        # technology = plant.find('Electricity_Infrastructure:GENERATIONTYPE', ns).text)
        # try:
            # subfuel = plant.find('Electricity_Infrastructure:PRIMARYSUBFUELTYPE', ns).text
        # except:
            # subfuel = fuel

        # date_updated format after split: YYYY-MM-DD
        try:
            year_updated = int(plant.find("Electricity_Infrastructure:REVISED", ns).text.split("T")[0][0:4])
        except:
            year_updated = None

        # assign ID number
        idnr = pw.make_id(SAVE_CODE,count)
        new_location = pw.LocationObject("",latitude,longitude)
        new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=COUNTRY_NAME,
            plant_location=new_location,plant_fuel=fuel,plant_capacity=capacity,
            plant_source=SOURCE,plant_cap_year=year_updated,plant_source_url=SOURCE_URL)
        plants_dictionary[idnr] = new_plant
        count += 1

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
