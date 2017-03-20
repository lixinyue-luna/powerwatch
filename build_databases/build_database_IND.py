# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_IND.py
Get power plant data from India and convert to Power Watch format.
Data Source: Central Electricity Authority
Additional information: [URL]
Issues:
Additional possible sources:
- Capacity, generation and coal consuption data appear to be available via API here: https://data.gov.in/catalog/coal-statement-thermal-power-stations 
- Solar data appear available here: https://data.gov.in/catalog/commissioned-grid-solar-power-projects
- Some data appear to be available here, with subscription: http://www.indiastat.com/power/26/generation/112/stats.aspx
- Outdated power system data are available here: http://www.cercind.org/powerdata.htm
- Annual generation by plant appears to be available here: http://cea.nic.in/reports/monthly/executivesummary/2016/exe_summary-08.pdf
- Might get wind data from CDM
- Might get CSP data from NREL

Further possible data sources:
- Ladakh Renewable Energy Development Agency (map, but all projects appear to be proposed, not completed): http://ladakhenergy.org/projects/map/
- There appear to be almost 30 other such agencies. See https://en.wikipedia.org/wiki/Ministry_of_New_and_Renewable_Energy#State_Nodal_Agencies 
- An old (2011) list of grid-tied solar PV plants: http://mnre.gov.in/file-manager/UserFiles/powerplants_241111.pdf
- This appears to be a list of approved solar parks (although unclear if they're operational): http://www.seci.gov.in/content/innerpage/statewise-solar-parks.php
"""

import csv
import sys, os
from zipfile import ZipFile
import lxml.html as LH
import xlrd

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"India"
SOURCE_NAME = u"Central Electricity Authority and REC Registry of India"
SOURCE_URL = u"http://www.cea.nic.in/,https://www.recregistryindia.nic.in/"
SAVE_CODE = u"IND"
RAW_FILE_NAME_CEA = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "database_11.zip")
RAW_FILE_NAME_CEA_UZ = pw.make_file_path(fileType = "raw", filename = SAVE_CODE)
RAW_FILE_NAME_REC = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "accredited_rec_generators.html")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "database_IND.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
LOCATION_FILE = pw.make_file_path(fileType = "resource", subFolder = SAVE_CODE, filename = "plant_locations_IND.csv")
TAB_NAME = u"Data"
DATA_YEAR = 2015

# optional raw file(s) download
# True if specified --download, otherwise False
FILES = {RAW_FILE_NAME_CEA:"http://www.cea.nic.in/reports/others/thermal/tpece/cdm_co2/database_11.zip",
            RAW_FILE_NAME_REC:"https://www.recregistryindia.nic.in/index.php/general/publics/accredited_regens"} # dictionary of saving directories and corresponding urls
DOWNLOAD_FILES = pw.download(u'CEA and RECS', FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# specify column names used in raw file
COLNAMES = [u"S_NO", u"NAME", u"UNIT_NO", u"DT_ COMM", u"CAPACITY MW AS ON 31/03/2015", 
                u"TYPE", u"FUEL 1", u"FUEL 2", u"2014-15\n\nNet \nGeneration \nGWh"]

# unzip, load and process CEA file
with ZipFile(RAW_FILE_NAME_CEA,'r') as myzip:
    fn = myzip.namelist()[0]
    f = myzip.extract(fn,RAW_FILE_NAME_CEA_UZ)
    book = xlrd.open_workbook(f)
    sheet = book.sheet_by_name(TAB_NAME)

    rv = sheet.row_values(0)
    id_col = rv.index(COLNAMES[0])
    name_col = rv.index(COLNAMES[1])
    unit_col = rv.index(COLNAMES[2])
    year_col = rv.index(COLNAMES[3])
    capacity_col = rv.index(COLNAMES[4])
    type_col = rv.index(COLNAMES[5])
    fuel1_col = rv.index(COLNAMES[6])
    fuel2_col = rv.index(COLNAMES[7])
    generation_col = rv.index(COLNAMES[8])

    for i in range(1,sheet.nrows):

        # read in row
        rv = sheet.row_values(i)

        if rv[unit_col] != 0.0:
            continue                       # Unit "0" is used for entire plant, so only read this line

        try:
            name = pw.format_string(rv[name_col])
            if not name:
                continue        # don't read rows that lack a plant name (footnotes, etc)
        except:
            print(u"-Error: Can't read plant name for plant on row {0}.".format(i))
            continue
    
        try:
            id_val = int(rv[id_col])
            if not id_val:
                continue        # don't read rows that lack an ID (footnotes, etc)
        except:
            print(u"-Error: Can't read ID for plant on row {0}.".format(i))
            continue

        try:
            capacity = float(rv[capacity_col])
        except:
            try:
                capacity = eval(rv[capacity_col])
            except:
                print("-Error: Can't read capacity for plant {0}".format(name))
                capacity = pw.NO_DATA_NUMERIC

        try:
            if rv[generation_col] == u'-':
                generation = 0.0
            else:
                generation = float(rv[generation_col])
        except:
            print("-Error: Can't read genertaion for plant {0}".format(name))
            generation = pw.NO_DATA_NUMERIC

        try:
            plant_type = pw.format_string(rv[type_col])
            if plant_type == u"HYDRO":
                fuel = pw.standardize_fuel(plant_type,fuel_thesaurus)
            elif plant_type == u"NUCLEAR":
                fuel = pw.standardize_fuel(plant_type,fuel_thesaurus)
            elif plant_type == u"THERMAL":
                fuel = pw.standardize_fuel(rv[fuel1_col],fuel_thesaurus)
                if rv[fuel2_col]:
                    fuel2 = pw.standardize_fuel(rv[fuel2_col],fuel_thesaurus)
                    fuel = fuel.union(fuel2)
            else:
                print("Can't identify plant type {0}".format(plant_type))
        except:
            print(u"Can't identify plant type for plant {0}".format(name))


        latitude = 0.0
        longitude = 0.0

        # assign ID number
        idnr = pw.make_id(SAVE_CODE,id_val)
        new_location = pw.LocationObject("",latitude,longitude)
        new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=COUNTRY_NAME,
            plant_location=new_location,plant_fuel=fuel,
            plant_capacity=capacity,plant_cap_year=DATA_YEAR,
            plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL,
            plant_generation=generation,plant_gen_year=DATA_YEAR)
        plants_dictionary[idnr] = new_plant

# load and process RECS file
tree = LH.parse(RAW_FILE_NAME_CEA)
#print([td.text_content() for td in tree.xpath('//td')])

#ns = {"kml":"http://www.opengis.net/kml/2.2"}   # namespace
#parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
#tree = etree.parse(RAW_FILE_NAME_REC, parser)
#rows = iter(table)
#for row in rows:
#    print row

#    root = tree.getroot()
#    for child in root[0]:
#        if u"Folder" in child.tag:

# report on plants read from file
print(u"Loaded {0} plants to database.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
