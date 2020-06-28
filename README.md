# cif-timetable-reader

ATCO-CIF (.cif) is the default file format of choice that UK Public transport authorities use to store data on timetables and stops. This repository contains a Python tool - cif-timetable-reader.py to wrangle that raw data according to latest ATCO-CIF specifications as well as a few tools for further analysis. 

**cif-timetable-reader.py** - analyze .cif files to create a timetable containing all information available for each route. The result is a .csv file containing records on each route, it's associated stops and other informations. Moreover, each stop and route pair holds information on next stop id and arrival time.

**stop_frequency_counter.py** - analyze journey time frequency within a given timeframe.

**stop_location_to_shapefile.py** - create a shapefile containing all stops listed inside the .cif.

**CIF_data** folder contains example .cif files with timetables for different modes of travel in Scotland inbetween 1.07.2019 and 7.07.2019. 

**atco-cif-spec1.pdf** - official ATCO-CIF .cif specification.

- **USAGE:** 

Open the cif-timetable-reader.py and adjust the path to folder with .cif files you want to analyze. The output .csv will be saved in the same directory.

 - **TODO:**
 - [ ] Create a tool to read route travel time.
 - [ ] Add more .cif prefixes like notes on specific journeys (QN .cif record prefix)
- [x] Add option to create shapefiles with stops (each .cif file contains information on stop coordinates)

