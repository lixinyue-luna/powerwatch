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

### PARAMS ###
# Folder directories
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR = os.path.join(ROOT_DIR, "raw_source_files")
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
SOURCE_DB_BIN_DIR = os.path.join(ROOT_DIR, "source_databases")
SOURCE_DB_CSV_DIR =	os.path.join(ROOT_DIR, "source_databases_csv")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output_database")
DIRs = {"raw": RAW_DIR, "resource": RESOURCES_DIR, "src_bin": SOURCE_DB_BIN_DIR,
		"src_csv": SOURCE_DB_CSV_DIR, "root": ROOT_DIR, "output": OUTPUT_DIR}

# Resource files
FUEL_THESAURUS_FILE 			= os.path.join(RESOURCES_DIR, "fuel_type_thesaurus.csv")
HEADER_NAMES_THESAURUS_FILE 	= os.path.join(RESOURCES_DIR, "header_names_thesaurus.csv")
COUNTRY_NAMES_THESAURUS_FILE 	= os.path.join(RESOURCES_DIR, "country_names_thesaurus.csv")
COUNTRY_INFORMATION_FILE 		= os.path.join(RESOURCES_DIR, "country_information.csv")
MASTER_PLANT_CONCORDANCE_FILE 	= os.path.join(RESOURCES_DIR, "master_plant_concordance.csv")
SOURCE_THESAURUS_FILE 			= os.path.join(RESOURCES_DIR, "sources_thesaurus.csv")

# Encoding
UNICODE_ENCODING = "utf-8"
NO_DATA_UNICODE = u""   # used to indicate no data for a Unicode-type attribute in the PowerPlant class
NO_DATA_NUMERIC = None  # used to indicate no data for a numeric-type attribute in the PowerPlant class
NO_DATA_OTHER = None 	# used to indicate no data for object- or list-type attribute in the PowerPlant class
NO_DATA_SET = set([])	# used to indicate no data for set-type attribute in the PowerPlant class

### CLASS DEFINITIONS ###

class PowerPlant(object):
	def __init__(self, plant_idnr, plant_name, plant_country,
		plant_owner = NO_DATA_UNICODE, plant_nat_lang = NO_DATA_UNICODE,
		plant_capacity = NO_DATA_NUMERIC, plant_cap_year = NO_DATA_NUMERIC,
		plant_source = NO_DATA_OTHER, plant_source_url = NO_DATA_UNICODE,
		plant_location = NO_DATA_OTHER, plant_coord_source = NO_DATA_UNICODE,
		plant_fuel = NO_DATA_SET,
		plant_generation = NO_DATA_NUMERIC, plant_gen_year = NO_DATA_NUMERIC,
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
		numeric_attributes = {'capacity':plant_capacity, 'cap_year':plant_cap_year, 'generation':plant_generation, 'gen_year':plant_gen_year}
		for attribute,input_parameter in numeric_attributes.iteritems():
			if input_parameter is NO_DATA_NUMERIC:
				setattr(self,attribute,NO_DATA_NUMERIC)
			else:
				if type(input_parameter) is float or type(input_parameter) is int:
					setattr(self,attribute,input_parameter)
				else:
					try:
						setattr(self,attribute,float(input_parameter))  # NOTE: sub-optimal; may want to throw an error here instead
					except:
						print("Error trying to create plant with parameter {0} for attribute {1}.".format(input_parameter,attribute))

		# check and set list for fuel types
		if not plant_fuel:
			setattr(self,'fuel',NO_DATA_SET)
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
			setattr(self,'fuel',NO_DATA_SET)

		# set data for other attributes
		# TODO: check data type for these
		object_attributes = {'source':plant_source,'location':plant_location}
		for attribute,input_parameter in object_attributes.iteritems():
			setattr(self,attribute,input_parameter)

class MasterPlant(object):
	def __init__(self, master_idnr, matches):
		self.idnr 			= master_idnr
		self.matches 		= matches

class SourceObject(object):
	def __init__(self, name, priority, country, url = NO_DATA_UNICODE, year = NO_DATA_NUMERIC):
		self.name 			= name
		self.country 		= country
		self.priority		= priority
		self.url 			= url
		self.year			= year

class CountryObject(object):
	def __init__(self, primary_name, iso_code, iso_code2, geo_name, carma_name, has_api, use_geo, fusion_table_id):
		self.primary_name 	= primary_name
		self.iso_code 		= iso_code
		self.iso_code2		= iso_code2
		self.geo_name 		= geo_name
		self.carma_name 	= carma_name
		self.has_api 		= has_api
		self.use_geo 		= use_geo
		self.fusion_table_id = fusion_table_id

class LocationObject(object):
	def __init__(self,description=u"",latitude=None,longitude=None):
		self.description 	= description
		self.latitude 		= latitude
		self.longitude 		= longitude

### ARGUMENT PARSER ###

def build_arg_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument("--download", help = "download raw files", action="store_true")
	return parser.parse_args()

def download(db_name = '', file_savedir_url = {}):
	if db_name == '':
		return True if build_arg_parser().download else False

	# TODO: handle xlsx, xls format. Finland and Yemen
	if build_arg_parser().download:
		print(u"Downloading {0} database...").format(db_name)
		for savedir, url in file_savedir_url.iteritems():
			response = requests.get(url)
			with open(savedir, 'w') as f:
				f.write(response.content)
		print(u"...done.")
	else:
		print(u"Using {0} file saved locally.").format(db_name)

### FILE PATHS ###

def make_file_path(fileType = "root", subFolder = "", filename = ""):
	# if path doesn't exist, create it
	for d in DIRs.keys():
		if not os.path.exists(DIRs[d]):
			os.mkdir(DIRs[d])
	# find/create directory and return path
	try:
		dst = DIRs[fileType]	# get root folder
		# if subFolder is not None, then create a directory
		# if filename is None:
		if subFolder != "":
			subFolder_path = os.path.normpath(os.path.join(dst, subFolder))
			if not os.path.exists(subFolder_path):
				os.mkdir(subFolder_path)
		return os.path.normpath(os.path.join(dst, subFolder, filename))
	except:
		print("Invalid FileType")
		return

### SOURCES ###

def make_source_thesaurus(source_thesaurus = SOURCE_THESAURUS_FILE):
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

def make_fuel_thesaurus(fuel_type_thesaurus = FUEL_THESAURUS_FILE):
	with open(fuel_type_thesaurus, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		fuel_thesaurus = {}
		for row in csvreader:
			fuel_primary_name = row[0].decode(UNICODE_ENCODING)
			fuel_thesaurus[fuel_primary_name] = [x.decode(UNICODE_ENCODING).lower().rstrip() for x in filter(None, row)]
		return fuel_thesaurus

def standardize_fuel(fuel_instance, fuel_thesaurus):
	# return set with primary fuel name(s) based on fuel_instance; split input on "/"

	if isinstance(fuel_instance,str):
		fuel_instance_u = fuel_instance.decode(UNICODE_ENCODING)
	elif isinstance(fuel_instance,unicode):
		fuel_instance_u = fuel_instance

	fuel_instance_list = fuel_instance_u.split("/")
	fuel_instance_list_lower = [f.lower().strip() for f in fuel_instance_list]
	fuel_set = set([])
	try:
		for fuel in fuel_instance_list_lower:
			for fuel_primary_name,fuel_synonyms in fuel_thesaurus.iteritems():
				if fuel in fuel_synonyms:
					fuel_set.add(fuel_primary_name)
					break
		return fuel_set
	except:
		print(u"-Error: Couldn't identify fuel type {0}".format(fuel_instance_u))
		return NO_DATA_SET

### HEADER NAMES ###

def make_header_names_thesaurus(header_names_thesaurus_file = HEADER_NAMES_THESAURUS_FILE):
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
	with open(country_names_thesaurus_file, 'rbU') as f:
		f.readline() # skip headers
		csvreader = csv.reader(f)
		country_names_thesaurus = {}
		for row in csvreader:
			country_primary_name = row[0].decode(UNICODE_ENCODING)
			country_names_thesaurus[country_primary_name] = [row[5].decode(UNICODE_ENCODING),row[6].decode(UNICODE_ENCODING)]
		return country_names_thesaurus

def make_country_dictionary(country_information_file = COUNTRY_INFORMATION_FILE):
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
			fusion_table_id = row[7].decode(UNICODE_ENCODING)
			new_country = CountryObject(primary_name,country_code,country_code2,geo_name,carma_name,has_api,use_geo,fusion_table_id)
			country_dictionary[primary_name] = new_country
		return country_dictionary

def standardize_country(country_instance, country_thesaurus):
	country_instance = country_instance.replace(",","")
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
# 	try:
# 		g = geocoder.google(coordinates, method = 'reverse')
# 		print g.country_long
# 		return g.country_long
# 	except:
# 		print "error"
# 		return "Unknown"

### ID NUMBERS AND MATCHING ###

def make_id(letter_code,id_number):
	# return standard-format id number (alpha. code followed by 7-digit number)
	return u"{:3}{:07d}".format(letter_code, id_number)

def make_plant_concordance(master_plant_condordance_file = MASTER_PLANT_CONCORDANCE_FILE):
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
	# strip possible newlines, replace commas, strip trailing whitespace
	# default to decode value to utf-8
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

def parse_powerplant_data(json_data,db_source):
	# parse data returned by Enipedia elastic search API

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
	desc = json_data['_source']
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


### LOAD/SAVE/WRITE CSV ###

def save_database(plant_dict,filename,savedir=OUTPUT_DIR,datestamp=False):
    # pickle database with timestamp
    if datestamp:
	    savename = (filename + '-Database-' + datetime.datetime.now().isoformat().replace(":","-")[:-10] + '.bin')
    else:
    	savename = (filename + '-Database.bin')
    savepath = os.path.join(savedir,savename)
    with open(savepath, 'wb') as f:
        pickle.dump(plant_dict, f)

def load_database(filename):
	# read in pickled file
	with open(filename, 'rb') as f:
		return pickle.load(f)

def write_csv_file(plants_dictionary,csv_filename,dump=None):
	# TODO: get csv_file abs path
	f = open(csv_filename,'w')
	warning_text = "NOTE: This Power Watch database of power plants is currently in draft status and not yet published. Please do not reference or cite the data as basis for research or publications until the data is officially published.\n"
	f.write(warning_text)
	if dump:
		header_text = "name,pw_idnr,in_pw,capacity_mw,year_of_capacity_data,annual_generation_gwh,year_of_generation_data,country,owner,source,url,latitude,longitude,fuel1,fuel2,fuel3,fuel4\n"
	else:
		header_text = "name,pw_idnr,capacity_mw,year_of_capacity_data,annual_generation_gwh,year_of_generation_data,country,owner,source,url,latitude,longitude,fuel1,fuel2,fuel3,fuel4\n"
	f.write(header_text)

	for k,p in plants_dictionary.iteritems():
		fuels = ",".join(p.fuel)
		try:
			row_text = u"{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}\n".format(
				p.name,p.idnr,p.capacity,p.cap_year,p.generation,p.gen_year,p.country,p.owner,p.source,p.url,p.location.latitude,p.location.longitude,fuels
				)
			f.write(row_text.encode(UNICODE_ENCODING))
		except:
			print(u"Unicode error with plant {0}".format(idnr))

	f.close()

def read_csv_file_to_dict(filename):
    """
    Read output CSV database into nested dict with pw_idnr as key.

    Parameters
    ----------
    filename : str
        Filepath for the CSV to read.
    """
    with open(filename, 'rbU') as fin:
        fin.readline()  # skip BETA warning statement
        reader = csv.DictReader(fin)
        pdb = {}  # returned object
        # counters for
        cap_year = 0
        annual_gen = 0
        gen_year = 0
        for row in reader:
            row = {k: format_string(v) for k, v in row.items()}
            row['capacity_mw'] = float(row['capacity_mw'])
            row['latitude'] = float(row['latitude'])
            row['longitude'] = float(row['longitude'])
            try:
                row['year_of_capacity_data'] = int(row['year_of_capacity_data'])
            except:
                row['year_of_capacity_data'] = None
                cap_year += 1
            try:
                row['annual_generation_gwh'] = float(row['annual_generation_gwh'])
            except:
                row['annual_generation_gwh'] = None
                annual_gen += 1
            try:
                row['year_of_generation_data'] = int(row['year_of_generation_data'])
            except:
                row['year_of_generation_data'] = None
                gen_year += 1
            pdb[row['pw_idnr']] = row
        print 'cap_year', cap_year, '\nannual_gen', annual_gen, '\ngen_year', gen_year
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
                        pw_idnr TEXT UNIQUE,
                        capacity_mw REAL,
                        year_of_capacity_data INTEGER,
                        annual_generation_gwh REAL,
                        year_of_generation_data INTEGER,
                        country TEXT,
                        owner TEXT,
                        source TEXT,
                        url TEXT,
                        latitude REAL,
                        longitude REAL,
                        fuel1 TEXT,
                        fuel2 TEXT,
                        fuel3 TEXT,
                        fuel4 TEXT )''')
    except:
        raise sqlite3.Error('Cannot create table "powerplants" (it might already exist).')

    c.execute('begin')
    for k, p in plants_dict.iteritems():
        stmt = u'''INSERT INTO powerplants VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        vals = (p['name'], p['pw_idnr'], p['capacity_mw'],
                p['year_of_capacity_data'], p['annual_generation_gwh'],
                p['year_of_generation_data'], p['country'], p['owner'],
                p['source'], p['url'], p['latitude'], p['longitude'],
                p['fuel1'], p['fuel2'], p['fuel3'], p['fuel4'])
        c.execute(stmt, vals)
    c.execute('commit')

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

