# This Python file uses the following encoding: utf-8
"""
PowerWatch
A library to support open-source power sector data.
"""

import datetime
import argparse
import requests
#import geocoder	#TODO: use geocoder to determine if the location of a power plant is in corresponding country boarder
import pickle
import csv
import sys
import os
import sqlite3
import re

### PARAMS ###
# Folder directories
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR = os.path.join(ROOT_DIR, "raw_source_files")
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
SOURCE_DB_BIN_DIR = os.path.join(ROOT_DIR, "source_databases")
SOURCE_DB_CSV_DIR = os.path.join(ROOT_DIR, "source_databases_csv")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output_database")
DIRs = {"raw": RAW_DIR, "resource": RESOURCES_DIR, "src_bin": SOURCE_DB_BIN_DIR,
		"src_csv": SOURCE_DB_CSV_DIR, "root": ROOT_DIR, "output": OUTPUT_DIR}

# Resource files
FUEL_THESAURUS_DIR				= os.path.join(RESOURCES_DIR, "fuel_type_thesaurus")
HEADER_NAMES_THESAURUS_FILE		= os.path.join(RESOURCES_DIR, "header_names_thesaurus.csv")
COUNTRY_NAMES_THESAURUS_FILE	= os.path.join(RESOURCES_DIR, "country_names_thesaurus.csv")
COUNTRY_INFORMATION_FILE		= os.path.join(RESOURCES_DIR, "country_information.csv")
MASTER_PLANT_CONCORDANCE_FILE	= os.path.join(RESOURCES_DIR, "master_plant_concordance.csv")
SOURCE_THESAURUS_FILE			= os.path.join(RESOURCES_DIR, "sources_thesaurus.csv")

# Encoding
UNICODE_ENCODING = "utf-8"
NO_DATA_UNICODE = u""	# used to indicate no data for a Unicode-type attribute in the PowerPlant class
NO_DATA_NUMERIC = None	# used to indicate no data for a numeric-type attribute in the PowerPlant class
NO_DATA_OTHER = None	# used to indicate no data for object- or list-type attribute in the PowerPlant class
NO_DATA_SET = set([])	# used to indicate no data for set-type attribute in the PowerPlant class

### CLASS DEFINITIONS ###

class PowerPlant(object):
	"""Class representing a power plant."""
	def __init__(self, plant_idnr, plant_name, plant_country,
		plant_owner = NO_DATA_UNICODE, plant_nat_lang = NO_DATA_UNICODE,
		plant_capacity = NO_DATA_NUMERIC, plant_cap_year = NO_DATA_NUMERIC,
		plant_source = NO_DATA_OTHER, plant_source_url = NO_DATA_UNICODE,
		plant_location = NO_DATA_OTHER, plant_coord_source = NO_DATA_UNICODE,
		plant_fuel = NO_DATA_SET, plant_generation = NO_DATA_OTHER,
		plant_commissioning_year = NO_DATA_NUMERIC,
		plant_estimated_generation_gwh = NO_DATA_NUMERIC
		):

		# check and set data for attributes that should be unicode
		unicode_attributes = {'idnr':plant_idnr, 'name':plant_name, 'country':plant_country, 'owner':plant_owner, 'nat_lang':plant_nat_lang, 'url':plant_source_url, 'coord_source':plant_coord_source}

		for attribute,input_parameter in unicode_attributes.iteritems():
			if input_parameter is NO_DATA_UNICODE:
				setattr(self,attribute,NO_DATA_UNICODE)
			else:
				if type(input_parameter) is unicode:
					setattr(self,attribute,input_parameter)
				else:
					try:
						setattr(self,attribute,input_parameter.decode(UNICODE_ENCODING))
					except:
						print("Error trying to create plant with parameter {0} for attribute {1}.".format(input_parameter,attribute))
						setattr(self,attribute,NO_DATA_UNICODE)

		# check and set data for attributes that should be numeric
		numeric_attributes = {'capacity':plant_capacity, 'cap_year':plant_cap_year, 'commissioning_year':plant_commissioning_year, 'estimated_generation_gwh':plant_estimated_generation_gwh}
		for attribute,input_parameter in numeric_attributes.iteritems():
			if input_parameter is NO_DATA_NUMERIC:
				setattr(self,attribute,NO_DATA_NUMERIC)
			else:
				if type(input_parameter) is float or type(input_parameter) is int:
					setattr(self,attribute,input_parameter)
				else:
					try:
						setattr(self,attribute,float(input_parameter))	# NOTE: sub-optimal; may want to throw an error here instead
					except:
						print("Error trying to create plant with parameter {0} for attribute {1}.".format(input_parameter,attribute))

		# check and set data for attributes that should be lists
		list_attributes = {'generation': plant_generation}
		for attribute, input_parameter in list_attributes.iteritems():
			if attribute == 'generation' and input_parameter is NO_DATA_OTHER:
				#setattr(self, attribute, [PlantGenerationObject()])
				setattr(self, attribute, NO_DATA_OTHER)
			elif attribute == 'generation' and type(input_parameter) is PlantGenerationObject:
				setattr(self, attribute, [input_parameter])
			else: # assume list/tuple of PlantGenerationObject
				setattr(self, attribute, list(input_parameter))

		# check and set fuel types
		# TODO: check that fuels are valid standardized fuels
		if not plant_fuel:
			setattr(self,'fuel',NO_DATA_SET.copy())
		elif type(plant_fuel) is unicode:
			setattr(self,'fuel',set([plant_fuel]))
		elif type(plant_fuel) is str:
			setattr(self,'fuel',set([plant_fuel.decode(UNICODE_ENCODING)]))
		elif type(plant_fuel) is list:
			setattr(self,'fuel',set(plant_fuel))
		elif type(plant_fuel) is set:
			setattr(self,'fuel',plant_fuel)
		else:
			print("Error trying to create plant with fuel of type {0}.".format(plant_fuel))
			setattr(self,'fuel',NO_DATA_SET.copy())

		# set data for other attributes
		object_attributes = {'source': plant_source, 'location': plant_location}
		for attribute, input_parameter in object_attributes.iteritems():
			if attribute == 'source' and type(input_parameter) is not SourceObject:
				if type(input_parameter) is str:
					setattr(self, attribute, format_string(input_parameter))
				elif type(input_parameter) is unicode:
					setattr(self, attribute, format_string(input_parameter, encoding = None))
				else:
					setattr(self, attribute, NO_DATA_UNICODE)
			elif attribute == 'location' and type(input_parameter) is not LocationObject:
				setattr(self, attribute, LocationObject())
			else:  # everything OK
				setattr(self, attribute, input_parameter)


	def __repr__(self):
		"""Representation of the PowerPlant."""
		return 'PowerPlant: ' + str(self.idnr)

	def __str__(self):
		"""String representation of the PowerPlant."""
		try:
			s = ['{',
				'  id: ' + str(self.idnr),
				'  name: ' + str(self.name),
				'  fuel: ' + str(self.fuel),
				'  owner: ' + str(self.owner),
				'  capacity: ' + str(self.capacity),
				'  has_location: ' + str(bool(self.location)),
				'}']
			return '\n'.join(s)
		except:
			return self.__repr__()

class MasterPlant(object):
	def __init__(self, master_idnr, matches):
		"""Plant identifier in cases of unit-level data, not plant-level."""
		self.idnr			= master_idnr
		self.matches		= matches

class SourceObject(object):
	def __init__(self, name, priority, country,
				url = NO_DATA_UNICODE, year = NO_DATA_NUMERIC):
		"""
		Class holding information about where powerplant data comes from.

		Parameters
		----------
		name : str
			Entity/ministry/department/report/dataset providing the data.
		priority : int
			Tier (1-5) of source updatability and format.
		country : str
			Country/region/scope of data source.
		url : str
			URL where data can be repeatably accessed.
		year : int
			Time when data was collected/released.
		"""
		self.name			= name
		self.country		= country
		self.priority		= priority
		self.url			= url
		self.year			= year


class CountryObject(object):
	def __init__(self, primary_name, iso_code, iso_code2, geo_name, carma_name, iea_name, has_api, use_geo, fusion_table_id):
		"""
		Class holding information on a specific country.

		Parameters
		----------
		primary_name : str
			Human-readable name.
		iso_code : str
			3-character ISO name.
		iso_code2 : str
			2-character ISO name.
		geo_name : str
			Name used by the Global Energy Observatory (GEO) database.
		carma_name : str
			Name used by the CARMA database.
		iea_name: str
			Name used by the IEA statistics website.
		has_api : int
			1 or 0 depending on automatic energy report releases.
		use_geo : int
			1 or 0 depending on whether GEO is the sole source of data.
		fusion_table_id : str
			Alphanumeric id for fusion table where data is stored.

		"""
		self.primary_name	= primary_name
		self.iso_code		= iso_code
		self.iso_code2		= iso_code2
		self.geo_name		= geo_name
		self.carma_name		= carma_name
		self.iea_name		= iea_name
		self.has_api		= has_api
		self.use_geo		= use_geo
		self.fusion_table_id = fusion_table_id


class LocationObject(object):
	def __init__(self,description=u"",latitude=None,longitude=None):
		"""
		Class holding information on the location (lat, lon) of a powerplant.

		Parameters
		----------
		description : unicode
			Note on how the location has been identified.
		latitude : float
			WGS84 (EPSG:4326)
		longitude : float
			WGS84 (EPSG:4326)

		"""
		self.description	= description
		self.latitude		= latitude
		self.longitude		= longitude

	def __repr__(self):
		lat = self.latitude
		lon = self.longitude
		desc = self.description
		return 'Location: lat={0}; lon={1}; desc={2}'.format(lat, lon, desc)

	def __nonzero__(self):
		"""Boolean checking."""
		return (self.longitude is not None) and (self.latitude is not None)


class PlantGenerationObject(object):
	def __init__(self, gwh=None, start_date=None, end_date=None, source=None, estimated=False):
		"""
		Class holding information on the generation of a powerplant.

		Parameters
		----------
		gwh : float
			Electricity generation in units of GigaWatt Hours.
		start_date : datetime
			Start date for the generation period.
		end_date : datetime
			End date for the generation period.
		source : unicode
			Source (URL/name) that produced the data.
		estimated: boolean
			Whether data is reported value or estimated from a model.

		Raises
		------
		ValueError if `end_date` is before `start_date`.
		TypeError if `start_date` or `end_date` is not a datetime.

		"""
		self.gwh = gwh
		if type(self.gwh) is int:
			self.gwh = float(self.gwh)

		if type(start_date) in [type(None), datetime.date]:
			self.start_date = start_date
		else:
			self.start_date = NO_DATA_OTHER
		if type(end_date) in [type(None), datetime.date]:
			self.end_date = end_date
		else:
			self.end_date = NO_DATA_OTHER

		if type(source) is str:
			setattr(self, 'source', format_string(source))
		elif type(source) is unicode:
			setattr(self, 'source', format_string(source, encoding = None))
		else:
			setattr(self, 'source', NO_DATA_UNICODE)

		if type(self.start_date) != type(self.end_date):
			raise TypeError('start_date and end_date must both be datetime objects or None')

		if self.end_date < self.start_date:
			raise ValueError('end_date must be after start_date')

		if type(estimated) is bool:
			self.estimated = estimated
		else:
			self.estimated = False

	def __repr__(self):
		start = None
		end = None
		if self.start_date:
			start = self.start_date.strftime('%Y-%m-%d')
		if self.end_date:
			end = self.end_date.strftime('%Y-%m-%d')
		return 'PlantGeneration: GWH={0}; start={1}; end={2}'.format(self.gwh, start, end)

	def __str__(self):
		start = None
		end = None
		if self.start_date:
			start = self.start_date.strftime('%Y-%m-%d')
		if self.end_date:
			end = self.end_date.strftime('%Y-%m-%d')
		s = ['{',
			'  GWH: ' + str(self.gwh),
			'  start: ' + str(start),
			'  end: ' + str(end),
			'  source: ' + str(self.source.encode(UNICODE_ENCODING)),
			'}'
			]
		return '\n'.join(s)

	def __nonzero__(self):
		"""Boolean checking."""
		return (self.gwh is not None) \
			and (self.start_date is not None) \
			and (self.end_date is not None)

	@staticmethod
	def create(gwh, year=None, month=None, source=None):
		"""
		Construct a PlantGenerationObject for a certain year or month in year.

		Parameters
		----------
		gwh : float
			Electricty generation in GigaWatt*Hour.
		year : int, optional
			Year the generation data corresponds to.
		month : int, optional
			Month the generation data corresponds to.
		source : str, optional
			Identifying value for the source of the generation data.

		Returns
		-------
		PlantGenerationObject

		"""
		if year is None:
			return PlantGenerationObject(gwh, source=source)
		if year is not None and month is None:
			start = datetime.date(year, 1, 1)
			end = datetime.date(year, 12, 31)
			return PlantGenerationObject(gwh, start, end, source)
		if year is not None and month is not None:
			start = datetime.date(year, month, 1)
			future_month = start.replace(day=28) + datetime.timedelta(days=4)
			end =  future_month - datetime.timedelta(days=future_month.day)
			return PlantGenerationObject(gwh, start, end, source)
		else:  # year is None and month is not None
			return PlantGenerationObject(gwh, source=source)


def annual_generation(gen_list, year):
	"""
	Compute the aggregated annual generation for a certain year.

	Parameters
	----------
	gen_list : list of PlantGenerationObject
		Input generation data.
	year : int
		Year to aggregate data.

	Returns
	-------
	Float if generation data is found in the year, otherwise None.

	"""
	year_start = datetime.date(year, 1, 1)
	year_end = datetime.date(year, 12, 31)
	candidates = []

	if gen_list == None:
		return None

	for gen in gen_list:
		if not gen:
			continue
		if gen.start_date > year_end or gen.end_date < year_start:
			continue
		candidates.append(gen)

	if not candidates:
		return None

	for gen in candidates:
		if (gen.end_date - gen.start_date).days in [364, 365]:
			return gen.gwh

	return None


### ARGUMENT PARSER ###

def build_arg_parser():
	"""Parse command-line system arguments."""
	parser = argparse.ArgumentParser()
	parser.add_argument("--download", help = "download raw files", action="store_true")
	return parser.parse_args()

def download(db_name = '', file_savedir_url = {}, post_data = {}):
	"""
	Fetch and download a database from an online source.
	TO-DO: Trap timeout or other errors.

	Parameters
	----------
	db_name : str
		Identifying name for the database to be downloaded.
	file_savedir_url : dict of {str: str}
		Dict with local filepaths as keys and URL as values.
	post_data: dict of {str: str}
		Dict with params and values for POST request.
		If not specified, use GET.
		TO-DO: Extend to allow different values for each entry in file_savedir_url.

	Returns
	-------
	rc : bool
		True: If no download requested OR download requested and successful.
		False: If download requested but no database name provided OR download 
			requested but failed.
	"""

	if not build_arg_parser().download:
		print(u"Using raw data file(s) saved locally.")
		return True

	if db_name == '':
		# Incorrect behavior, since db name should be specified, so return False.
		print(u"Error: Download requested but no database name specified.")
		return False

	print(u"Downloading {0} database...").format(db_name)
	try:
		for savedir, url in file_savedir_url.iteritems():
			if post_data:
				response = requests.post(url,post_data)
			else:
				response = requests.get(url)
			with open(savedir, 'w') as f:
				f.write(response.content)
		print(u"...done.")
		return True
	except:
		print(u"Error: Failed to download one or more files.")
		return False


### FILE PATHS ###

def make_file_path(fileType = "root", subFolder = "", filename = ""):
	"""
	Construct a file path, creating the nested directories as needed.

	Parameters
	----------
	fileType : str
		Shortcut phrase for project directories. e.g. 'output', 'resource'
	subFolder : str
		Directory name (possibly nested) within `fileType` directory.
	filename : str
		File basename to append to directory path on returned filepath.

	Raises
	-----
	ValueError if fileType is invalid (not in `DIRs`).
	"""
	# if path doesn't exist, create it
	for key, path in DIRs.items():
		if not os.path.exists(path):
			os.mkdir(path)
	# find/create directory and return path
	try:
		dst = DIRs[fileType]	# get root folder
	except:
		raise ValueError('Invalid directory shortcut phrase <{0}>'.format(fileType))
	if subFolder:
		subFolder_path = os.path.normpath(os.path.join(dst, subFolder))
		if not os.path.exists(subFolder_path):
			os.mkdir(subFolder_path)
	return os.path.normpath(os.path.join(dst, subFolder, filename))

### SOURCES ###

def make_source_thesaurus(source_thesaurus = SOURCE_THESAURUS_FILE):
	"""
	Get dict mapping country name to `SourceObject` for the country.

	Parameters
	----------
	source_thesaurus : str
		Filepath for the source thesaurus data.

	Returns
	-------
	Dict of {"Country": SourceObject} pairs.
	"""
	with open(source_thesaurus, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		source_thesaurus = {}
		for row in csvreader:
			source_name = row[0].decode(UNICODE_ENCODING)
			source_country = row[1].decode(UNICODE_ENCODING)
			source_url = row[2].decode(UNICODE_ENCODING)
			source_priority = row[3].decode(UNICODE_ENCODING)
			# TODO: get year info from other other file (download from Google Drive)
			source_thesaurus[source_name] = SourceObject(name = source_name,
				country = source_country, priority = source_priority,
				url = source_url)
		return source_thesaurus

### FUEL TYPES ###
def make_fuel_thesaurus(fuel_type_thesaurus=FUEL_THESAURUS_DIR):
	"""
	Get dict mapping standard fuel names to a list of alias values.

	Parameters
	----------
	fuel_type_thesaurus : str
		Filepath to the fuel thesaurus.

	Returns
	-------
	Dict of {"primary fuel name": ['alt_name0', 'alt_name1', ...]}

	"""
	fuel_thesaurus_files = os.listdir(fuel_type_thesaurus)
	fuel_thesaurus = {}
	for fuel_file in fuel_thesaurus_files:
		with open(os.path.join(fuel_type_thesaurus, fuel_file), 'rbU') as fin:
			standard_name = fin.readline().decode(UNICODE_ENCODING).rstrip()
			#aliases = [x.decode('utf-8').lower().rstrip() for x in fin.readlines()]
			aliases = [x.decode(UNICODE_ENCODING).rstrip() for x in fin.readlines()]
			#fuel_thesaurus[standard_name] = [standard_name.lower()]
			fuel_thesaurus[standard_name] = [standard_name]
			fuel_thesaurus[standard_name].extend(aliases)
	return fuel_thesaurus

def standardize_fuel(fuel_instance, fuel_thesaurus):
	"""
	Get set of primary fuel names from string of alternate names.

	Parameters
	----------
	fuel_instance : str
		Non-standard fuel names separated by '/' (e.g. bitumen/sun/uranium).
	fuel_thesaurus : dict
		Dict returned from `make_fuel_thesaurus()`.

	Returns
	-------
	fuel_set : set
		Minimum set of primary fuel names corresponding to the input string.
		Returns `NO_DATA_SET` if a fuel type cannot be identified.

	"""

	delimiter_pattern = '/| y |,| and '

	if isinstance(fuel_instance,str):
		fuel_instance_u = fuel_instance.decode(UNICODE_ENCODING)
	elif isinstance(fuel_instance,unicode):
		fuel_instance_u = fuel_instance

	#fuel_instance_list = fuel_instance_u.split("/"," y ")
	fuel_instance_list = re.split(delimiter_pattern,fuel_instance)
	fuel_instance_list_clean = [f.strip() for f in fuel_instance_list]
	fuel_set = NO_DATA_SET.copy()
	for fuel in fuel_instance_list_clean:
		if fuel_instance_u == NO_DATA_UNICODE:
			continue
		identified = False
		for fuel_primary_name, fuel_synonyms in fuel_thesaurus.iteritems():
			if fuel in fuel_synonyms:
				fuel_set.add(fuel_primary_name)
				identified = True
				break
		if not identified:
			print(u"-Error: Couldn't identify fuel type {0}".format(fuel_instance_u))

	return fuel_set

### HEADER NAMES ###

def make_header_names_thesaurus(header_names_thesaurus_file = HEADER_NAMES_THESAURUS_FILE):
	"""
	Get a dict mapping ideal domain-specific phrases to list of alternates.

	Parameters
	----------
	header_names_thesaurus_file : str
		Filepath.

	Returns
	-------
	Dict of {'ideal phrase': ['alt_phrase0', 'alt_phrase1', ...]}.

	"""
	with open(header_names_thesaurus_file, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		header_names_thesaurus = {}
		for row in csvreader:
			header_primary_name = row[0]
			header_names_thesaurus[header_primary_name] = [x.lower().rstrip() for x in filter(None,row)]
		return header_names_thesaurus

### COUNTRY NAMES ###

def make_country_names_thesaurus(country_names_thesaurus_file = COUNTRY_INFORMATION_FILE):
	"""
	Get a dict mapping ideal country names to list of alternates.

	Parameters
	----------
	country_names_thesaurus_file : str
		Filepath.

	Returns
	-------
	Dict of {'country': ['alt_country0', 'alt_country1', ...]}.

	"""
	with open(country_names_thesaurus_file, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		country_names_thesaurus = {}
		for row in csvreader:
			country_primary_name = row[0].decode(UNICODE_ENCODING)
			country_names_thesaurus[country_primary_name] = [row[5].decode(UNICODE_ENCODING),row[6].decode(UNICODE_ENCODING),row[7].decode(UNICODE_ENCODING)]
		return country_names_thesaurus

def make_country_dictionary(country_information_file = COUNTRY_INFORMATION_FILE):
	"""
	Get a dict mapping country name to `CountryObject`.

	Parameters
	----------
	country_information_file : str
		Filepath.

	Returns
	-------
	Dict of {'country': CountryObject}.

	"""
	with open(country_information_file, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		country_dictionary = {}
		for row in csvreader:
			primary_name = row[0].decode(UNICODE_ENCODING)
			country_code = row[1].decode(UNICODE_ENCODING)
			country_code2 = row[2].decode(UNICODE_ENCODING)
			has_api = int(row[3])
			use_geo = int(row[4])
			geo_name = row[5].decode(UNICODE_ENCODING)
			carma_name = row[6].decode(UNICODE_ENCODING)
			iea_name = row[7].decode(UNICODE_ENCODING)
			fusion_table_id = row[8].decode(UNICODE_ENCODING)
			new_country = CountryObject(primary_name,country_code,country_code2,geo_name,carma_name,iea_name,has_api,use_geo,fusion_table_id)
			country_dictionary[primary_name] = new_country
		return country_dictionary

def standardize_country(country_instance, country_thesaurus):
	"""
	Get the standard country name from a non-ideal instance.

	Parameters
	----------
	country_instance : str
		Non-ideal or alternative country name (e.g. 'United States').
	country_thesaurus : dict
		Dict returned by `make_country_names_thesaurus()`.

	Returns
	-------
	country_primary_name : unicode
		Standard country name (e.g. 'United States of America').
		Returns `NO_DATA_UNICODE` if country cannot be identified.

	"""
	country_instance = country_instance.replace(",","")
	# TODO: fix this try-except block
	try:
		for country_primary_name in country_thesaurus:
			if country_instance in country_thesaurus[country_primary_name]:
				return country_primary_name
	except:
		print("Error: Couldn't identify country name {0}".format(country_instance))
		return NO_DATA_UNICODE

	print("Couldn't identify country {0}".format(country_instance))
	return NO_DATA_UNICODE

### COUNTRY BORDERS ###

# def is_in_country(coordinates):
#	try:
#		g = geocoder.google(coordinates, method = 'reverse')
#		print g.country_long
#		return g.country_long
#	except:
#		print "error"
#		return "Unknown"

### ID NUMBERS AND MATCHING ###

def make_id(letter_code,id_number):
	"""
	Make the standard-format id code (country ISO3 followed by 7-digit number).

	Parameters
	----------
	letter_code : str
		3-character ISO code (e.g. USA, BRA, CHN).
	id_number : int
		Number less than 10-million.

	Returns
	-------
	id : unicode
		3-character country code followed by zero-leading 7-character numeral.

	"""
	return u"{:3}{:07d}".format(letter_code, id_number)

def make_plant_concordance(master_plant_condordance_file = MASTER_PLANT_CONCORDANCE_FILE):
	"""
	Get a dict that enables matching between the same plants from multiple databases.
	Parameters
	----------
	master_plant_concordance_file : str
		Filepath for plant concordance.

	Returns
	-------
	Dict mapping WRI-specific ID to a dict of equivalent ids for other databases.

	"""
	# Note: These IDs are 'item source', not plant IDs.
	with open(master_plant_condordance_file, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		plant_concordance = {}
		for row in csvreader:
			wri_id = make_id(u"WRI",int(row[0]))
			geo_id = make_id(u"GEODB", int(row[1])) if row[1] else ""
			carma_id = make_id(u"CARMA", int(row[2])) if row[2] else ""
			osm_id = make_id(u"OSM", int(row[3])) if row[3] else ""
			plant_concordance[wri_id] = {'geo_id':geo_id, 'carma_id':carma_id, 'osm_id':osm_id}
		return plant_concordance

### STRING CLEANING ###

def format_string(value,encoding = UNICODE_ENCODING):
	"""
	Format string to another representation and dissolve problem characters.

	Parameters
	----------
	value : str
		The string to parse and format.
	encoding : str
		Encoding to decode `value` into.

	Returns
	-------
	clean_value : unicode
		`value` stripped of control characters, commas, and trailing whitespace.
		`NO_DATA_UNICODE` if problem with re-encoding.
	"""
	# if encoding=None, don't decode
	try:
		if encoding == None:
			unicode_value = value
		else:
			unicode_value = value.decode(encoding)
		clean_value = unicode_value.replace("\n"," ").replace("\r"," ").replace(","," ").strip()
		# TODO: Find better way to handle substitute characters than this:
		clean_value = clean_value.replace(u"\u001A","")
		return clean_value
	except:
		return NO_DATA_UNICODE

### PARSE DATA RETURNED BY ELASTIC SEARCH ###

#TODO: understand this function
def parse_powerplant_data(json_data,db_source):
	"""
	Parse data returned by Enipedia elastic search API.

	Parameters
	----------
	json_data : dict
		???
	db_source : str
		???

	Returns
	-------
	score : float
		???
	parsed_values : dict
		???

	"""

	# initialize parsed values
	parsed_values = {}
	parsed_values['idnr'] = NO_DATA_NUMERIC
	parsed_values['name'] = NO_DATA_UNICODE
	parsed_values['country'] = NO_DATA_UNICODE
	parsed_values['latitude'] = NO_DATA_NUMERIC
	parsed_values['longitude'] = NO_DATA_NUMERIC
	parsed_values['fuel'] = NO_DATA_UNICODE
	parsed_values['owner'] = NO_DATA_UNICODE
	parsed_values['capacity'] = NO_DATA_NUMERIC

	# values common to all databases
	score = float(json_data['_score'])
	parsed_values['idnr'] = int(json_data['_id'])

	# parse source string, different for each database
	desc = json_data['_source'] # type(desc) = dict
	db_name = db_source.lower()

	if db_name == 'geo':
		db_key_names_strings = {'name':'Name', 'fuel':'Type', 'country':'Country', 'owner':'Owner1'}
		db_key_names_floats = {'latitude':'Latitude_Start', 'longitude':'Longitude_Start', 'capacity':'Design_Capacity_MWe_nbr'}

	#elif db_name == 'osm':
	#	db_key_names_strings = {'name':'name', 'fuel_type':'generator:source'}
	#	db_key_names_floats = {'latitude':'latitude', 'longitude':'longitude'}

	elif db_name == 'carmav3':
		db_key_names_strings = {'name':'name', 'country':'country'}
		db_key_names_floats = {'latitude':'latitude', 'longitude':'longitude'}

	for primary_key,db_key in db_key_names_strings.iteritems():
		if db_key in desc:
			try:
				parsed_values[primary_key] = desc[db_key].replace(","," ")
			except:
				parsed_values[primary_key] = desc[db_key]

	for primary_key,db_key in db_key_names_floats.iteritems():
		if db_key in desc:
			try:
				parsed_values[primary_key] = float(desc[db_key].replace(",",""))
			except:
				parsed_values[primary_key] = desc[db_key]

	return score,parsed_values


### DATE/TIME PARSING ###

def excel_date_as_datetime(excel_date,date_mode=0):
	"""
	Convert Excel date number to python datetime object
	Further info: https://stackoverflow.com/questions/1108428/how-do-i-read-a-date-in-excel-format-in-python

	Parameters
	----------
	excel_date: float
		Float in Excel date format (based on days since January 1, 1900).
	date_mode: int (0,1)
		Date basis for Excel: 0 = 1900 (default), 1 = 1904.
	"""

	return datetime.datetime(1899,12,30) + datetime.timedelta(days=excel_date + date_mode * 1462)


### LOAD/SAVE/WRITE CSV ###

def save_database(plant_dict,filename,savedir=OUTPUT_DIR,datestamp=False):
	"""
	Pickle in-memory database to file.

	Parameters
	----------
	plant_dict : dict
		Dict of {'pw_idnr': PowerPlant} to save.
	filename : str
		Base filename to save the pickle.
	savedir : str, optional
		Directory in which `filename` will be located.
	datestamp : bool, optional
		Whether to add a timestamp to the filename.
	"""
	# pickle database with timestamp
	if datestamp:
		savename = (filename + '-Database-' + datetime.datetime.now().isoformat().replace(":","-")[:-10] + '.bin')
	else:
		savename = (filename + '-Database.bin')
	savepath = os.path.join(savedir,savename)
	with open(savepath, 'wb') as f:
		pickle.dump(plant_dict, f)

def load_database(filename):
	"""Read in pickled database file."""
	with open(filename, 'rb') as f:
		return pickle.load(f)

def write_csv_file(plants_dictionary, csv_filename, dump=False):
	"""
	Write in-memory database into a CSV format.

	Parameters
	----------
	plants_dictionary : dict
		Dict of {'pw_idnr': PowerPlant} to save.
	csv_filename : str
		Filepath for the output CSV.
	dump : bool, default False
		Whether this is a full-dump or a cleaned database.

	"""

	def _dict_row(powerplant):
		ret = {}
		ret['name'] = powerplant.name.encode(UNICODE_ENCODING)
		ret['pw_idnr'] = powerplant.idnr.encode(UNICODE_ENCODING)
		ret['capacity_mw'] = powerplant.capacity
		ret['year_of_capacity_data'] = powerplant.cap_year
		ret['country'] = powerplant.country.encode(UNICODE_ENCODING)
		ret['owner'] = powerplant.owner.encode(UNICODE_ENCODING)
		ret['source'] = powerplant.source
		if ret['source'] is not None:
			ret['source'] = ret['source'].encode(UNICODE_ENCODING)
		ret['url'] = powerplant.url.encode(UNICODE_ENCODING)
		ret['latitude'] = powerplant.location.latitude
		ret['longitude'] = powerplant.location.longitude
		ret['commissioning_year'] = powerplant.commissioning_year
		for i, fuel in enumerate(powerplant.fuel):
			if i == 4:
				break
			ret['fuel{0}'.format(i + 1)] = fuel
		for year in range(2012, 2017):
			gwh = annual_generation(powerplant.generation, year)
			ret['generation_gwh_{0}'.format(year)] = gwh
		ret['estimated_generation_gwh'] = powerplant.estimated_generation_gwh
		return ret

	fieldnames = [
		"name",
		"pw_idnr",
		"capacity_mw",
		"year_of_capacity_data",
		"country",
		"owner",
		"source",
		"url",
		"latitude",
		"longitude",
		"commissioning_year",
		"fuel1",
		"fuel2",
		"fuel3",
		"fuel4",
		"generation_gwh_2012",
		"generation_gwh_2013",
		"generation_gwh_2014",
		"generation_gwh_2015",
		"generation_gwh_2016",
		"estimated_generation_gwh"
	]


	if dump:
		fieldnames.insert(2, 'in_pw')

	# TODO: get csv_file abs path
	with open(csv_filename, 'wb') as fout:
		warning_text = "NOTE: This Power Watch database of power plants is currently in draft status and not yet published. Please do not reference or cite the data as basis for research or publications until the data is officially published.\n"
		fout.write(warning_text)

		writer = csv.DictWriter(fout, fieldnames=fieldnames)
		writer.writeheader()

		keys = plants_dictionary.keys()
		sort_key = lambda x: (plants_dictionary[x].country,  plants_dictionary[x].name)

		sorted_keys = sorted(keys, key=sort_key)
		for k in sorted_keys:
			try:
				drow = _dict_row(plants_dictionary[k])
				writer.writerow(drow)
			except:
				print(u"Unicode error with plant {0}".format(plants_dictionary[k].idnr))


def read_csv_file_to_dict(filename):
	"""
	Read saved CSV database into nested dict with pw_idnr as key.

	Parameters
	----------
	filename : str
		Filepath for the CSV to read.

	Returns
	-------
	pdb : dict
		Dictionary with pw_idnr for keys and dictionary
	"""
	with open(filename, 'rbU') as fin:
		fin.readline()	# skip BETA warning statement
		reader = csv.DictReader(fin)
		pdb = {}  # returned object
		# counters for
		for row in reader:
			row = {k: format_string(v) for k, v in row.items()}
			row['capacity_mw'] = float(row['capacity_mw'])
			try:
				row['latitude'] = float(row['latitude'])
				row['longitude'] = float(row['longitude'])
			except:
				row['latitude'] = None
				row['longitude'] = None
			try:
				row['commissioning_year'] = float(row['commissioning_year'])
			except:
				row['commissioning_year'] = None
			try:
				row['year_of_capacity_data'] = int(row['year_of_capacity_data'])
			except:
				row['year_of_capacity_data'] = None
			# check if fuels are empty strings
			if not row['fuel1']:
				row['fuel1'] = None
			if not row['fuel2']:
				row['fuel2'] = None
			if not row['fuel3']:
				row['fuel3'] = None
			if not row['fuel4']:
				row['fuel4'] = None
			# check if annual generation data are empty
			if not row['generation_gwh_2012']:
				row['generation_gwh_2012'] = None
			if not row['generation_gwh_2013']:
				row['generation_gwh_2013'] = None
			if not row['generation_gwh_2014']:
				row['generation_gwh_2014'] = None
			if not row['generation_gwh_2015']:
				row['generation_gwh_2015'] = None
			if not row['generation_gwh_2016']:
				row['generation_gwh_2016'] = None
			if not row['estimated_generation_gwh']:
				row['estimated_generation_gwh'] = None
			# add row to output dict
			pdb[row['pw_idnr']] = row
		return pdb


def write_sqlite_file(plants_dict, filename, return_connection=False):
	"""
	Write database into sqlite format from nested dict.

	Parameters
	----------
	plants_dict : dict
		Has the structure inherited from <read_csv_file_to_dict>.
	filename : str
		Output filepath; should not exist before function call.
	return_connection : bool (default False)
		Whether to return an active database connection.

	Returns
	-------
	conn: sqlite3.Connection
		Only returned if `return_connection` is True.

	Raises
	------
	OSError
		If SQLite cannot make a database connection.
	sqlite3.Error
		If database has already been populated.

	"""
	try:
		conn = sqlite3.connect(filename)
	except:
		raise OSError('Cannot connect to {0}'.format(filename))
	conn.isolation_level = None  # faster database insertions

	c = conn.cursor()

	try:
		c.execute('''CREATE TABLE powerplants (
						name TEXT,
						pw_idnr TEXT UNIQUE NOT NULL,
						capacity_mw REAL,
						year_of_capacity_data INTEGER,
						country TEXT,
						owner TEXT,
						source TEXT,
						url TEXT,
						latitude REAL,
						longitude REAL,
						fuel1 TEXT,
						fuel2 TEXT,
						fuel3 TEXT,
						fuel4 TEXT,
						generation_gwh_2012 REAL,
						generation_gwh_2013 REAL,
						generation_gwh_2014 REAL,
						generation_gwh_2015 REAL,
						generation_gwh_2016 REAL,
						estimated_generation_gwh REAL )''')
	except:
		raise sqlite3.Error('Cannot create table "powerplants" (it might already exist).')

	c.execute('begin')
	for k, p in plants_dict.iteritems():
		stmt = u'''INSERT INTO powerplants VALUES (
					?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
		vals = (p['name'],
				p['pw_idnr'],
				p['capacity_mw'],
				p['year_of_capacity_data'],
				p['country'],
				p['owner'],
				p['source'],
				p['url'],
				p['latitude'],
				p['longitude'],
				p['fuel1'],
				p['fuel2'],
				p['fuel3'],
				p['fuel4'],
				p['generation_gwh_2012'],
				p['generation_gwh_2013'],
				p['generation_gwh_2014'],
				p['generation_gwh_2015'],
				p['generation_gwh_2016'],
				p['estimated_generation_gwh'])
		c.execute(stmt, vals)

	c.execute('commit')

	index_stmt = '''CREATE INDEX idx_country ON powerplants (country)'''
	c.execute(index_stmt)

	if return_connection:
		return conn
	else:
		conn.close()


def copy_csv_to_sqlite(csv_filename, sqlite_filename, return_connection=False):
	"""
	Copy the output database from CSV format into SQLite format.

	Parameters
	----------
	csv_filename : str
		Input file to copy.
	sqlite_filename : str
		Output database file; should not exist prior to function call.
	"""
	pdb = read_csv_file_to_dict(csv_filename)
	try:
		conn = write_sqlite_file(pdb, sqlite_filename, return_connection=return_connection)
	except:
		raise Exception('Error handling sqlite database')
	if return_connection:
		return conn
