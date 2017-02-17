# This Python file uses the following encoding: utf-8
"""
PowerWatch
build_database_SourceWatch.py
Get power plant data from SourceWatch (for China coal) and convert to Power Watch format.
Data Source: SourceWatch
Additional information: http://www.sourcewatch.org/index.php/SourceWatch
Issues:
"""

import argparse
import sys, os

import json
import wikimarkup
import pandas as pd
from pyquery import PyQuery

sys.path.insert(0, os.pardir)
import powerwatch as pw

# params
COUNTRY_NAME = u"China" 		# We are only gathering China coal data from this source
SOURCE_NAME = u"SourceWatch"
SAVE_CODE = u"SRCWT"
RAW_FILE_NAME = pw.make_file_path(fileType = "raw", subFolder = SAVE_CODE, filename = "SourceWatch_China_coal_database.json")
CSV_FILE_NAME = pw.make_file_path(fileType = "src_csv", filename = "sourcewatch_database.csv")
SAVE_DIRECTORY = pw.make_file_path(fileType = "src_bin")
SOURCE_URL = u"http://www.sourcewatch.org/index.php/Category:Existing_coal_plants_in_China"

# other params
URL_BASE = "http://www.sourcewatch.org/api.php?"
URL_END = "action=query&titles=Category:Existing_coal_plants_in_China&prop=revisions"\
	+"&rvprop=content&format=json"

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

# read in plants
print(u"Reading in plants...")
with open(RAW_FILE_NAME,'r') as f:
	data = json.load(f)

# select main content of page
wiki = data['query']['pages']['85380']['revisions'][0]['*']

# get plants with location from map (first part of raw file)
plant_filename = 'http://www.sourcewatch.org/index.php/Category:Existing_coal_plants_in_China'
count = 0
for line in wiki.split('\n'):
	if '~[[' in line:
		count += 1
		idnr = pw.make_id(SAVE_CODE, count)
		plant = line.translate({ord(k):None for k in u'[];'}).split('~')
		name = pw.format_string(plant[1], encoding = None)
		##
		if name == u"Unknown":
			print("-Error: Name problem with {0}".format(idnr) + "at {0}".format(plant[0].split(',')))
		##
		coordinates = plant[0].split(',')
		lat = coordinates[0]
		lng = coordinates[1]
		latitude_number = float(lat)
		longitude_number = float(lng)
		new_location = pw.LocationObject(description=u"",
			latitude=latitude_number, longitude=longitude_number)
		new_plant = pw.PowerPlant(idnr, name, plant_country = COUNTRY_NAME,
			plant_location = new_location, plant_fuel = set([u'Coal']),
			plant_source = SOURCE_NAME, plant_source_url=SOURCE_URL,
			plant_cap_year=2017,plant_gen_year=2017,plant_generation=0)
		plants_dictionary[idnr] = new_plant

# use wikimarkup to detect the main table and transform to html code
html = str(PyQuery(wikimarkup.parse(wiki)))

# read html code into pandas dataframe
frames = pd.read_html(html, header = 0)
df = frames[0]

# make changes to Units column to include only the plant name, not the unit
for i, unit in enumerate(frames[0]['Unit']):
	df.set_value(i, 'Unit', unit.strip('[]').split('|')[0])

for plant in plants_dictionary.values():
	plant.capacity = df.groupby(['Unit']).sum().loc[plant.name].values[0]
	plant.nat_lang = df.loc[df['Unit'] == plant.name, 'Chinese Name'].values[0]
	# print list(set(df.loc[df['Unit'] == plant.name, 'Sponsor'].values))
	owner = list(set(df.loc[df['Unit'] == plant.name, 'Sponsor'].values))
	if len(owner) == 1:
		plant.owner = pw.format_string(owner[0])
	else:
		plant.owner = pw.format_string(owner[0]) + ' and ' + pw.format_string(owner[1])
	# plant.age is currently the age of the oldest unit of the plant
	#plant.year_built = df.loc[df['Unit'] == plant.name, 'Status/Year'].values[0]
	plant.location.description = df.loc[df['Unit'] == plant.name, 'Location'].values[0]

# report on number of plants included
print("Loaded {0} plants to database.".format(len(plants_dictionary)))

# write database to csv format
pw.write_csv_file(plants_dictionary,CSV_FILE_NAME)

# pickle database
pw.save_database(plants_dictionary,SAVE_CODE,SAVE_DIRECTORY)
print("Pickled database to {0}".format(SAVE_DIRECTORY))
