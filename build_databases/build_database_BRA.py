# This Python file uses the following encoding: utf-8
"""
PowerWatch
built_database_brazil.py
Get power plant data from Chile and convert to Power Watch format.
Data Source: Agência Nacional de Energia Elétrica, Brazil
Additional information: http://sigel.aneel.gov.br/kmz.html
Notes:
- ANEEL server initially provides KML with network links. To retriev all data, must
provide bbox of entire country with HTTP GET request.
Issues:
- Clarify fuel types for Undi-Electrica and Termoelectrica
- Clarify status terms
"""

from zipfile import ZipFile
from lxml import etree, html
import sys, os

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"Brazil"
SOURCE_NAME = u"Agência Nacional de Energia Elétrica (Brazil)"
SOURCE_URL = u"http://sigel.aneel.gov.br/kmz.html"
SAVE_CODE = u"BRA"
RAW_FILE_NAME = pw.make_file_path(fileType="raw",subFolder=SAVE_CODE, filename="FILENAME.zip")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "brazil_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
CAPACITY_CONVERSION_TO_MW = 0.001       # capacity values are given in kW in the raw data

# other parameters
DATASETS = {0: {"name":"UHE","fuel":"Hydro"}, 1: {"name":"PCH","fuel":"Hydro"},
            2: {"name":"CGH","fuel":"Hydro"}, 3: {"name":"EOL","fuel":"Wind"},
            4: {"name":"UTE","fuel":"Coal"}, 5: {"name":"UTN","fuel":"Nuclear"},
            6: {"name":"CGU","fuel":"Other"}, 7: {"name":"UFV","fuel":"Solar"} }

URL_BASE = u"http://sigel.aneel.gov.br/arcgis/services/SIGEL/ExportKMZ/MapServer/KmlServer?Composite=false&LayerIDs=ID_HERE&BBOX=-75.0,-34.0,-30.0,6.0"

def checkName(owner):
    # format plant owner's name
    if "\n" in owner:
        return pw.NO_DATA_UNICODE
    return owner

# optional raw file(s) download
FILES = {}
for fuel_code,dataset in DATASETS.iteritems():
    RAW_FILE_NAME_this = RAW_FILE_NAME.replace("FILENAME", dataset["name"])
    URL = URL_BASE.replace("ID_HERE",str(fuel_code))
    FILES[RAW_FILE_NAME_this] = URL
DOWNLOAD_FILES = pw.download(COUNTRY_NAME, FILES)

# set up fuel type thesaurus
fuel_thesaurus = pw.make_fuel_thesaurus()

# create dictionary for power plant objects
plants_dictionary = {}

# extract powerplant information from file(s)
print(u"Reading in plants...")

# read and parse KMZ files
ns = {"kml":"http://www.opengis.net/kml/2.2"}   # namespace
parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
for fuel_code,dataset in DATASETS.iteritems():
    zipfile = pw.make_file_path(fileType="raw",subFolder=SAVE_CODE,filename=dataset["name"]+".zip")
    kmz_file = ZipFile(zipfile,"r")
    kml_file = kmz_file.open("doc.kml","rU")
    tree = etree.parse(kml_file, parser)
    root = tree.getroot()
    for child in root[0]:
        if u"Folder" in child.tag:
            idval = int(child.attrib[u"id"].strip(u"FeatureLayer"))
            if idval in DATASETS.keys():
                shift = 0
                if idval in [0,3]:
                    shift = 1
                placemarks = child.findall(u"kml:Placemark", ns)
                #print('Found {0} placemarks for fuel code {1}'.format(len(placemarks),fuel_code))
                for pm in placemarks:
                    plant_id = int(pm.get("id").split("_")[1])
                    description = pm.find("kml:description", ns).text # html content
                    content = html.fromstring(description)
                    rows = content.findall("body/table")[1+shift].findall("tr")[1].find("td").find("table").findall("tr")
                    status = u"N/A"
                    year_updated = None
                    fuel = pw.standardize_fuel(dataset["fuel"], fuel_thesaurus)      # default fuel
                    for row in rows:
                        left = row.findall("td")[0].text
                        right = row.findall("td")[1].text
                        if left == u"Nome":
                            name = pw.format_string(right,None)
                            if name == u"Unknown":
                                print("Unicode problem with {0}".format(plant_id))
                                tmp_name = name
                                parts = tmp_name.split("\n")
                                if len(parts) > 1 and parts[0] == parts[-1]:
                                    name = parts[-1]
                        elif left in [u"Potência Outorgada (kW)", u"Potência (KW)"]:
                            try:
                                capacity = float(right) * CAPACITY_CONVERSION_TO_MW
                            except:
                                capacity = 0
                        elif left == u"Proprietário":
                            owner = pw.format_string(checkName(right),None)
                        elif left == u"Classificação do Combustível":
                            fuel = pw.format_string(right, None)
                            fuel = pw.standardize_fuel(fuel, fuel_thesaurus)
                        elif left == u"Estágio":
                            status = checkName(right)
                        elif left == u"Data de Atualização":
                            date_updated = checkName(right) # result in format MM/DD/YYYY HH:MM:SS AM/PM
                            year_updated = date_updated.split("/")[-1].split(" ")[0]

                # remove non-operating plants
                    if status != u"Operação":
                        if status == u"Construção não iniciada" and year_updated == None:
                            pass
                        else:
                            continue

                    coordinates = pm.find("kml:Point/kml:coordinates", ns).text.split(",") #[lng, lat, height]
                    try:
                        longitude = float(coordinates[0])
                        latitude = float(coordinates[1])
                    except:
                        latitude,longitude = pw.NO_DATA_NUMERIC,pw.NO_DATA_NUMERIC

                    # assign ID number
                    idnr = pw.make_id(SAVE_CODE,plant_id)
                    new_location = pw.LocationObject(pw.NO_DATA_UNICODE,latitude,longitude)
                    new_plant = pw.PowerPlant(plant_idnr=idnr,plant_name=name,plant_country=COUNTRY_NAME,
                        plant_location=new_location,plant_fuel=fuel,plant_capacity=capacity,
                        plant_source=SOURCE_NAME,plant_source_url=SOURCE_URL,plant_cap_year=year_updated)
                    plants_dictionary[idnr] = new_plant

# report on plants read from file
print(u"...read {0} plants.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# save database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print(u"Pickled database to {0}".format(SAVE_DIRECTORY))
