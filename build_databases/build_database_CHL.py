# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_chile.py
Get power plant data from Chile and convert to Power Watch format.
Data Source: Comision Nacional de Energia, Chile
Additional information: http://energiaabierta.cl/electricidad/
Location data derived from http://datos.energiaabierta.cl/rest/datastreams/107253/data.csv
Issues:
- Data includes "estado" (status); should eventually filter on operational plants, 
although currently all listed plants are operational
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
LOCATION_FILE_NAME = pw.make_file_path(fileType="resource",subFolder=SAVE_CODE,filename='chile_power_plants_locations.csv')

# other parameters
URL_BASE = "http://datos.energiaabierta.cl/rest/datastreams/NUMBER/data.csv"

COLNAMES1 = ["gid","nombre","propietario","combustible","potencia mw",
                "fecha operación","coordenada este","coordenada norte"]
COLNAMES2 = COLNAMES1.replace("combustible","combustibl")    # account for typo in column heading
COLNAMES3 = ["gid","nombre","propiedad","combustibl","potencia mw","fecha operación"]

DATASETS = [{"number":"215392","fuel":"Thermal","RAW_FILE_NAME":"chile_power_plants_thermal.csv","COLS":COLNAMES1},
            {"number":"215386","fuel":"Hydro","RAW_FILE_NAME":"chile_power_plants_hydro.csv","COLS":COLNAMES2},
            {"number":"215384","fuel":"Wind","RAW_FILE_NAME":"chile_power_plants_wind.csv"},
            {"number":"215381","fuel":"Biomass","RAW_FILE_NAME":"chile_power_plants_biomass.csv"},
            
            {"number":"215391","fuel":"Solar","RAW_FILE_NAME":"chile_power_plants_solar.csv"}]

# set locale to Spain (Chile is not usually available in locales)
locale.setlocale(locale.LC_ALL,"es_ES")

# download if specified
FILES = {}
for dataset in DATASETS:
     RAW_FILE_NAME_this = RAW_FILE_NAME.replace("FILENAME", dataset["RAW_FILE_NAME"])
     URL = URL_BASE.replace("NUMBER",dataset["number"])
     FILES[RAW_FILE_NAME_this] = URL
DOWNLOAD_FILES = pw.download("Chile power plant data", FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# set up country name thesaurus
country_thesaurus = pw.make_country_names_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")
country = SOURCE_NAME

# first read location file; name: 0; latitude: 1; longitude: 2
plant_locations = {}
#with open(LOCATION_FILENAME,"rbU") as f:
with open(LOCATION_FILE_NAME,'rbu') as f:
    datareader = csv.reader(f)
    headers = [x.lower() for x in datareader.next()]
    for row in datareader:
        name = pw.format_string(row[0])
        latitude = float(row[1])
        longitude = float(row[2])
        #name_latin_lower = replace_with_latin_equivalent(name).lower()
        plant_locations[name] = [latitude,longitude]


# read plant files
thermal_filename = pw.make_file_path(fileType="raw", subFolder=SAVE_CODE, filename="chile_power_plants_thermal.csv")
with open(thermal_filename,'rbU') as f:
    datareader = csv.reader(f)
    headers = [x.lower() for x in datareader.next()]
    id_col = headers.index(COLNAMES1[0])
    name_col = headers.index(COLNAMES1[1])
    owner_col = headers.index(COLNAMES1[2])
    fuel_col = headers.index(COLNAMES1[3])
    capacity_col = headers.index(COLNAMES1[4])
    date_col = headers.index(COLNAMES1[5])
    easting_col = headers.index(COLNAMES1[6])
    northing_col = headers.index(COLNAMES1[7])

    # idea: read into dict using csv read dict; then use .get with default for failure to find key



for dataset in DATASETS:
    dataset_filename = pw.make_file_path(fileType="raw", subFolder=SAVE_CODE, filename=dataset["RAW_FILE_NAME"])
    with open(dataset_filename, "rbU") as f:
        datareader = csv.reader(f)
        headers = [x.lower().strip() for x in datareader.next()]
        id_col = headers.index(COLNAMES[0])
        capacity_col = headers.index(COLNAMES[4])

        if dataset["fuel"] is not "Biomass":
            name_col = headers.index(COLNAMES[1])
        else:
            name_col = headers.index("comuna")

        # todo: handle solar file (no ownership info)
        """
        if dataset["fuel"] is not "Wind":
            owner_col = headers.index(COLNAMES[2])
        else:
            owner_col = headers.index("propiedad")
        """

        if dataset["fuel"] is not "Thermal":
            fuel_type = pw.standardize_fuel(dataset["fuel"], fuel_thesaurus)
        else:
            fuel_col = headers.index(COLNAMES[3])

        # read each row in the file
        for row in datareader:

            try:
                idval = int(row[id_col])
            except:
                print("-Error: Can't read ID")
                continue

            try:
                name = pw.format_string(row[name_col])
            except:
                print(u"-Error: Can't read plant name for ID {0}".format(idval))
                continue              

            if dataset["fuel"] is "Thermal":
                fuel_type = pw.standardize_fuel(row[fuel_col],fuel_thesaurus)

            try:
                capacity = locale.atof(row[capacity_col])
            except:
                capacity = pw.NO_DATA_NUMERIC
                print("-Error: Can't read capacity for plant {0}; value is {1}".format(name,row[capacity_col]))

            try:
                #name_latin_lower = replace_with_latin_equivalent(name).lower()
                if name in plant_locations.keys():
                    latitude,longitude = plant_locations[name]
                else:
                    #print("-Error: No lat/long for plant {0}, fuel {1}".format(name,fuel_type))
                    latitude,longitude = pw.NO_DATA_NUMERIC,pw.NO_DATA_NUMERIC
            except:
                print("-Error: Can't test lat/long for plant {0}".format(idval))
                latitude,longitude = pw.NO_DATA_NUMERIC,pw.NO_DATA_NUMERIC

            # assign ID number, make PowerPlant object, add to dictionary
            idnr = pw.make_id(SAVE_CODE,idval)
            new_location = pw.LocationObject(pw.NO_DATA_UNICODE,latitude,longitude)
            new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=country,
                plant_location=new_location,plant_fuel=fuel_type,plant_capacity=capacity,
                plant_source=SOURCE,plant_source_url=SOURCE_URL,plant_cap_year=YEAR_POSTED)
            plants_dictionary[idnr] = new_plant

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
