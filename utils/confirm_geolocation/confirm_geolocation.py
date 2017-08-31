# This Python file uses the following encoding: utf-8
"""
PowerWatch
confirm_geolocation.py
Use google maps reverse geocoding API to test if lat/long coordinates are in the correct country.
Add Google API key as API_KEY.
Searches for plants ranging from PLANT_START to PLANT_STOP in database (in order).
Incorrect country locations are logged in LOG_FILE.
"""

import sys
import os
import csv
import json
import requests
import argparse

sys.path.insert(0, os.path.join(os.pardir,os.pardir))
import powerwatch as pw

# params
ENCODING = 'utf-8'
URL_BASE = "https://maps.googleapis.com/maps/api/geocode/json?"
API_KEY = 'ADD KEY HERE'
LOG_FILE = "geolocation_errors.csv"
PLANT_START = 0
PLANT_STOP = 5000

# synomyms for countries used by Google that differ from Power Watch standard (incomplete list)
country_synonyms = {	'United States':'United States of America',
						'Czechia':'Czech Republic',
						'Syria':'Syrian Arab Republic',
						'Martinique':'France',
						'Guadeloupe':'France',
						'Reunion':'France',
						'The Gambia':'Gambia',
						'Myanmar (Burma)':'Myanmar'
					}

# parse args
parser = argparse.ArgumentParser()
parser.add_argument("powerplant_database", help = "name of power plant csv file")
args = parser.parse_args()

# open powerplant csv file
plants = {}
with open(args.powerplant_database,'rU') as f:
	datareader = csv.reader(f)
	headers1 = datareader.next()
	headers2 = datareader.next()
	for row in datareader:
		idval = row[1]
		country = row[4]
		try:
			latitude = float(row[8])
			longitude = float(row[9])
		except:
			continue
		plants[idval] = {'country':country,'latitude':latitude,'longitude':longitude}

# check coordinates
print("Checking plants...")
plant_count = 0
bad_geolocations = []

f = open(LOG_FILE,'a')
f.write('idval,latitude,longitude,pw_country,google_country\n')

for idval,plant in plants.iteritems():

	# only check plants in the start/stop range
	if plant_count < PLANT_START:
		plant_count += 1
		continue
	if plant_count > PLANT_STOP:
		break

	if plant_count % 50 == 0:
		print("...checked {0} plants...".format(plant_count))
	plant_count += 1
	country_powerwatch = plant['country']
	latitude = plant['latitude']
	longitude = plant['longitude']

	# build url and sent request
	URL = URL_BASE + "latlng={0},{1}".format(latitude,longitude) 
	URL = URL + "&key={0}".format(API_KEY)
	try:
		res = requests.get(URL)
		j = json.loads(res.text)
		address_components = j['results'][0]['address_components']
		for component in address_components:
			country_google = ''
			if "country" in component['types']:
				country_google = component['long_name']
				break
		if not country_google:
			# problem case
			print("Plant {0}: PW country: {1}; Google country not found.".format(idval,country_powerwatch))
			bad_geolocations.append(idval)
			f.write('{0},{1},{2},{3},not found\n'.format(idval,latitude,longitude,country_powerwatch))
		if country_powerwatch != country_google:
			# problem case unless it's a synonym
			if country_google in country_synonyms.keys():
				if country_synonyms[country_google] == country_powerwatch:
					continue
			print("Plant {0}: PW country: {1}; Google country: {2}".format(idval,country_powerwatch,country_google))
			bad_geolocations.append(idval)
			f.write('{0},{1},{2},{3},{4}\n'.format(idval,latitude,longitude,country_powerwatch,country_google))
	except:
		print("Error with plant {0}, counting as an error.".format(idval))
		try:
			f.write('{0},{1},{2},{3},unknown\n'.format(idval,latitude,longitude,country_powerwatch))
		except:
			print("...unable to save to log.")

# close log file
f.close()

# report location errors
print("Bad geolocations:")
for idval in bad_geolocations:
	print(idval)

print("Finished.")
