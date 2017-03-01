# PowerWatch: An open-source global power plant database project.

*NOTE: This Power Watch database of power plants is currently in draft status and not yet published. Please do not reference or cite the data as basis for research or publications until the data is officially published.*

This project aims to build an open database of all the power plants in the world. It is the result of a large collaboration involving many partners, coordinated by the [World Resources Institute](https://www.wri.org/) and [Google Earth Outreach](https://www.google.com/earth/outreach/index.html). If you would like to get involved, please email Johannes Friedrich (jfriedrich@wri.org), or fork the repo and code!

If you're just looking for the data, the latest database is available in CSV format [here](https://github.com/wri/powerwatch/blob/master/output_database/). *Please note this is a BETA version, and is not an official WRI publication.*

This work is made possible and supported by [Google](https://www.google.com).

## Database description

The PowerWatch database is built in several steps. 

* The first step involves gathering and processing country-level data. In some cases, these data are read automatically from offical government websites; the code to implement this is in the build_databases directory.
* In other cases we gather country-level data manually. These data are saved as public Google Fusion Tables, and are read into the processing chain using the build_database_WRI.py script in the build_database directory. 
* The second step is to integrate data from different sources, particularly for geolocation of power plants and annual total electricity generation. Some of these different sources are multi-national databases. For this step, we rely on offline work to match records; the concordance table mapping record IDs across databases is saved in resources/master_plant_concordance.csv.

Throughout the processing, we represent power plants as instances of the PowerPlant class, defined in powerwatch.py. The final database is in a flat-file CSV format.

## Key attributes of the database

The database includes the following indicators:

* Plant name
* Fuel type(s)
* Generation capacity
* Country
* Ownership
* Latitude/longitude of plant
* Data source
* Data source year
* Annual generation
* Annual generation year

We will expand this list in the future as we extend the database.

### Fuel Type Aggregation

We define the "Fuel Type" attribute of our database based on common fuel categories. In order to parse the different fuel types used in our various data sources, we map fuel name synonyms to our fuel categories [here](https://github.com/wri/powerwatch/blob/master/resources/fuel_type_thesaurus.csv). We plan to expand the database in the future to report more disaggregated fuel types.

## Combining Multiple Data Sources

A major challenge for this project is that data come from a variety of sources, including government ministries, utility companies, equipment manufacturers, crowd-sourced databases, financial reports, and more. The reliability of the data varies, and in many cases there are conflicting values for the same attribute of the same power plant from different data sources. To handle this, we match and de-duplicate records and then develop rules for which data sources to report for each indicator. We provide a clear [data lineage](https://en.wikipedia.org/wiki/Data_lineage) for each datum in the database. We plan to ultimately allow users to choose alternative rules for which data sources to draw on.

To the maximum extent possible, we read data automatically from trusted sources, and integrate it into the database. Our current strategy involves these steps:

* Automate data collection from machine-readable national data sources where possible. 
* For countries where machine-readable data are not available, gather and curate power plant data by hand, and then match these power plants to plants in other databases, including GEO and CARMA (see below) to determine their geolocation.
* For a limited number of countries with small total power-generation capacity, use data directly from Global Energy Observatory (GEO). 

A table describing the data source(s) for each country is listed below.

Finally, we are examining ways to automatically incorporate data from the following supra-national data sources:

* [Clean Development Mechanism](https://cdm.unfccc.int/Projects/projsearch.html)
* [ENTSO-E](https://www.entsoe.eu/Pages/default.aspx)
* [E-PRTR](http://prtr.ec.europa.eu/)
* [CARMA](http://carma.org/)
* [Arab Union of Electricity](http://www.auptde.org/Default.aspx?lang=en)
* [IAEA PRIS](https://www.iaea.org/pris/)
* [Industry About](http://www.industryabout.com/energy)
* [Think Geo Energy](http://www.thinkgeoenergy.com/map/)
* [WEC Global Hydropower Database](https://www.worldenergy.org/data/resources/resource/hydropower/)

## ID numbers

We assign a unique ID to each line of data that we read from each source. In some cases, these represent plant-level data, while in other cases they represent unit-level data. In the case of unit-level data, we perform an aggregation step and assign a new, unique plant-level ID to the result. For plants drawn from national data sources, the reference ID is formed by a three-letter country code [ISO 3166-1 alpha-3](http://unstats.un.org/unsd/tradekb/Knowledgebase/Country-Code) and a six-digit number. For plants drawn from other database, the reference ID is formed by a five-letter prefix code and a six-digit number.

## Power plant matching

In many cases our data sources do not include power plant geolocation information. To address this, we attempt to match these plants with the GEO and CARMA databases, in order to use that geolocation data. We use an [elastic search matching technique](https://github.com/cbdavis/enipedia-search) developed by Enipedia to perform the matching based on plant name, country, capacity, location, with confirmed matches stored in a concordance file. This matching procedure is complex and the algorithm we employ can sometimes wrongly match two power plants or fail to match two entries for the same power plant. We are investigating using the Duke framework for matching, which allows us to do the matching offline.

## Country data sources

Methods:
* "A" = automated with a dedicated build_database script
* "M/A" = currently manual, working to automate

In all other cases, we use manual data or GEO data. In a few cases, multiple methods are used for a single country. Further details are available in the [country information file](https://github.com/wri/powerwatch/blob/master/resources/country_information.csv).


| Country 		| Method  | Source(s)   
| --------------|:-------:|-------------
| Argentina		| A 	  | [MINEM](http://datos.minem.gob.ar)
| Australia		| A 	  | [AREMI](http://nationalmap.gov.au/renewables/)
| Belgium       | M/A     | [ELIA](http://publications.elia.be/upload/ProductionParkOverview.html?TS=20120416193815)
| Brazil		| A 	  | [ANEEL](http://sigel.aneel.gov.br/kmz.html)
| Canada        | M/A     | [PFF](http://powerforthefuture.ca/electricity-411/electricity-map/)
| Chile 		| A  	  | [CNE](http://datos.energiaabierta.cne.cl/developers/)
| China   		| A,M  	  | [Sourcewatch (coal)](http://www.sourcewatch.org/index.php/Category:Existing_coal_plants_in_China)
| Finland       | M/A     | [EA](http://www.energiavirasto.fi/en/voimalaitosrekisteri)
| Mexico        | M/A     | [SENER](http://base.energia.gob.mx/dgaic/DA/P/DGPlaneacionInformacionEnergeticas/CapacidadInstaladaPlantasProceso/SENER_05_CapacidadInstaladaPlantasPorPlantasProceso-PMXE1C18.csv)
| Portugal      | M/A     | [INEGI](http://e2p.inegi.up.pt/#Tec7)
| Switzerland   | M/A     | [BFE](http://www.bfe.admin.ch/geoinformation/05061/05249/index.html?lang=en)
| Turkey        | M/A     | [MENR](http://www.enerji.gov.tr/en-US/Mainpage)
| United Kingdom | A   	  | [DUKES](https://www.gov.uk/government/collections/digest-of-uk-energy-statistics-dukes), [REPD](https://www.gov.uk/government/collections/renewable-energy-planning-data)
| United States | A   	  | [EIA](https://www.eia.gov/electricity/data/eia860/)
| Uruguay       | M/A     | [MIEM](http://www.miem.gub.uy/en/datos-abiertos)

 
## Related repos

* [Open Power Systems Data](https://github.com/Open-Power-System-Data/)
* [Global Energy Observatory](https://github.com/hariharshankar/pygeo)
* [Duke](https://github.com/larsga/Duke)
