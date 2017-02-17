# PowerWatch: An open-source global power plant database project.

*NOTE: This Power Watch database of power plants is currently in draft status and not yet published. Please do not reference or cite the data as basis for research or publications until the data is officially published.*

This project aims to build an open database of all the power plants in the world. It is the result of a large collaboration involving many partners, coordinated by the [World Resources Institute](https://www.wri.org/). If you would like to get involved, please email Johannes Friedrich (jfriedrich@wri.org), or fork the repo and code!

If you're just looking for the data, the latest database is available in CSV format [here](https://github.com/Arjay7891/WRI-Powerplant/tree/master/output_database). *Please note this is a BETA version, and is not an official WRI publication.*

This work is made possible and supported by [Google](https://www.google.com).

## Database description

The PowerWatch database is built in several stages. 

* The first stage involves gathering and processing country-level data. In some cases, these data are read automatically from offical government websites; the code to implement this is in the build_databases directory.
* In other cases we gather country-level data manually. These data are saved as public Google Fusion Tables, and are read into the processing chain using the build_database_WRI.py script in the build_database directory. 
* The second stage is to integrate data from different sources, particularly for geolocation of power plants and annual total electricity generation. Some of these different sources are multi-national databases. For this stage, we rely on offline work to match records; the concordance table mapping record IDs across databases is saved in resources/master_plant_concordance.csv.

Throughout the processing, we represent power plants as instances of the PowerPlant class, defined in powerwatch.py. The final database is in a flat-file CSV format.

## Key attributes of the database

The database aims to include the following indicators for each power plant:

* Plant name
* Fuel type(s)
* Generation capacity
* Country
* Ownership
* Latitude/longitude of plant
* Data source
* Data source year
* Annual generation
* Annual generation data source year

We will expand this list in the future as we extend the database.

### Fuel Type Aggregation

The "Fuel Type" attribute of our data base needs a little more explanation. We find different levels 
of details for the fuel type in our sources. For example, while some data sources just list a power plant as
an "Oil" plant, others are more specific regarding the category of fuel, e.g. they distinguish between
light and heavy fuel oil, diesel, kerosene and so on. In order to be able to better match and compare power plants
between different data bases we have aggregated these detailed fuel types to 12 overarching fuel categories like
coal, oil, gas, solar and others. You can find a document that lists exactly how we aggregate fuel types to the 
different categories [here](https://github.com/Arjay7891/WRI-Powerplant/blob/master/resources/fuel_type_thesaurus.csv).
We are planning to expand our data base in the future to include the more detailed fuel types as well.

## Combining Multiple Data Sources

A major challenge for this project is that data come from a variety of sources, including government 
ministries, utility companies, equipment manufacturers, crowd-sourced databases, financial reports, 
and more. The reliability of the data therefore varies a lot, and in many cases there are 
conflicting values for the same attribute of the same power plant from different data sources. To 
handle this, we match and de-duplicate records and then develop rules for which data sources to 
rely on for various indicators. Ultimately, we intend to provide a clear 
[data lineage](https://en.wikipedia.org/wiki/Data_lineage) for each datum in the database, and 
surface this to users, allowing them to choose alternative rules for which data sources to draw on.

To the maximum extent possible, we intend to automatically pull data from trusted sources, and integrate it into the database. Our current strategy approach involves these steps:

* Automate data collection from machine-readable national data sources wherever possible. This currently includes:
 * [Argentina](http://datos.minem.gob.ar)
 * [Australia](http://nationalmap.gov.au/renewables/)
 * [Brazil](http://sigel.aneel.gov.br/kmz.html)
 * [Chile](http://datos.energiaabierta.cne.cl/developers/)
 * [China SourceWatch data for coal](http://www.sourcewatch.org/index.php/Category:Existing_coal_plants_in_China)
 * [United Kingdom](https://www.gov.uk/government/collections/digest-of-uk-energy-statistics-dukes); [(second source)](https://www.gov.uk/government/collections/renewable-energy-planning-data)
 * [USA](https://www.eia.gov/electricity/data/eia860/)
* For countries where machine-readable data are not available, gather and curate power plant data by hand, and then match these power plants to plants in other databases, including GEO and CARMA (see below).
* Read data from [Global Energy Observatory](http://globalenergyobservatory.org) (GEO). For countries where GEO has additional power plants to the ones we found before, we add these to the database.

Other national data sources we are working to integrate include:
* [Belgium](http://publications.elia.be/upload/ProductionParkOverview.html?TS=20120416193815)
* [Canada](http://powerforthefuture.ca/electricity-411/electricity-map/)
* [Finland](http://www.energiavirasto.fi/en/voimalaitosrekisteri)
* [Mexico](http://base.energia.gob.mx/dgaic/DA/P/DGPlaneacionInformacionEnergeticas/CapacidadInstaladaPlantasProceso/SENER_05_CapacidadInstaladaPlantasPorPlantasProceso-PMXE1C18.csv)
* [Portugal](http://e2p.inegi.up.pt/#Tec7)
* [Switzerland Hydropower](http://www.bfe.admin.ch/geoinformation/05061/05249/index.html?lang=en)
* [Turkey](http://www.enerji.gov.tr/en-US/Mainpage)
* [Uruguay](http://www.miem.gub.uy/en/datos-abiertos)
* Countries in the [Arab Union of Electricity](http://www.auptde.org/Default.aspx?lang=en): Egypt, Marocco, Kuwait, Lebanon, Oman, Sudan, Bahrain, Tunisia, United Arab Emirates, Yemen

Additionally, we are considering drawing data from the following supra-national data sources:
* [CARMA](http://carma.org/)
* [IAEA PRIS](https://www.iaea.org/pris/)
* [Industry About](http://www.industryabout.com/energy)
* [Think Geo Energy](http://www.thinkgeoenergy.com/map/)
* [WEC Global Hydropower Database](https://www.worldenergy.org/data/resources/resource/hydropower/)

## ID numbers

We are using a two-tiered ID system. First, every single line of data that we read in is assigned a reference ID. These data lines may be individual units of a power plant or a whole plant themselves. This depends on the data source. In a subsequent step, we internally aggregate lines that represent different units of the same plant. Then, we assign an ID to the plant (which can be comprised of multiple units, i.e. data lines). For plants drawn from national data sources, these are based on a three-letter prefix code from [ISO 3166-1 alpha-3](http://unstats.un.org/unsd/tradekb/Knowledgebase/Country-Code) and a six-digit number. For plants drawn from other database, these are based on a letter prefix code and a six-digit number. 

## Power plant matching

Since we draw data from different sources, we often have information from multiple sources for the same power plant. E.g. GEO and CARMA have many of the plants that we also find in the national sources. The challenge then is to reliably match all of these plants across the multiple data bases based on their names and other indicators such as country, capacity and location. This matching procedure is a difficult step and the algorithm we employ can sometimes wrongly match two power plants that are not the same. On the other hand, it can also fail to match two plants that are the same. 

We used an [elastic search matching technique](https://github.com/cbdavis/enipedia-search) developed by 
Enipedia to perform the matching and have built a [concordance file](https://github.com/Arjay7891/WRI-Powerplant/blob/master/resources/master_plant_concordance.csv) for matches between our hand-curated data and data from GEO and CARMA.
The Enipedia elastic search engine produces a score that indicates the quality of a match. We have found that above a certain threshold score the matches always seem to be correct and below a certain threshold they are predominantly wrong. In the grey area in between these two thresholds there are a lot of "maybe" matches and we have hand-checked many of these instances to verify the correctness of the match for the concordance file.

We are also looking into the [Duke](https://github.com/larsga/Duke) framework for matching, which allows us to do the matching offline.

## Related repos

* [Open Power Systems Data](https://github.com/Open-Power-System-Data/datapackage_power_plants_europe )
* [Global Energy Observatory](https://github.com/hariharshankar/pygeo)
* [Duke](https://github.com/larsga/Duke)
