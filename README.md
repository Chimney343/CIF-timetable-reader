# cif-timetable-reader

ATCO-CIF (.cif) is the default file format of choice that UK Public transport authorities use to store data on timetables and stops. 

**cif-timetable-reader.py** is a script that analyzes the .cif files to create a timetable of each route acccording to official ATCO specification. The result is a .csv file containing records on each stop in the network and it's associated routes. Moreover, each stop and route pair also contains information on next stop id and arrival time (so you can easily infer the total expected journey time or travel time between stops)

**CIF_data** folder contains example .cif files with timetables for different modes of travel in Scotland inbetween 1.07.2019 and 7.07.2019. 

**stop_frequency_counter.py** - given the output timetable from cif-timetable-reader.py, you can use it to analyze journey frequency on particular bus stops in a given timeframe.

The official document with parsing instructions is contained within atco-cif-spec1.pdf document.

- **USAGE:** 

Open the cif-timetable-reader.py and adjust the path to folder with .cif files you want to analyze. The output .csv will be saved in the same directory.

 - **TODO:**
 - [ ] Add more .cif prefixes like notes on specific journeys (QN .cif record prefix)
- [x] Add option to create shapefiles with stops (each .cif file contains information on stop coordinates)
