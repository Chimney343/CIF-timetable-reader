"""
ScotRail_CIF_timetable_converter.py

Analyze raw Scot Rail .cif files and convert them into .csv timetables proper. The only parameter
to adjust is the path to .cif file folder below and the output folder.

"""

paths = {
    'cif': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\New Rail Timetables',
    'output': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\Timetables\ScotRail',
}

# Do not edit below this point!
# ===================================================================================================

import os
import pandas as pd
import sys
import re
import datetime
import time
pd.set_option('display.max_columns', None)

def get_file_header(file):
    f = open(file, "r")
    for row in f:
        header = row
        break
    header_specification_dict =  {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'file_identity': (20, 3),
            'date_of_extract': (6, 23),
            'time_of_extract': (4, 29),
            'current_file_reference': (7, 33),
            'last_file_reference': (7, 41),
            'update_indicator': (1, 48),
            'version': (1, 49),
            'extract_start_date': (6, 50),
            'extract_end_date': (6, 61),
            'spare': (20, 62)
    }

    d = dict.fromkeys(list(header_specification_dict.keys()))
    for key in d.keys():
        start = header_specification_dict[key][1] - 1
        end = start + header_specification_dict[key][0]
        value = row[start:end].strip()
        d[key] = value
    return d
    
def extract_raw_scotrail_timetable(f):
    """
    Given a ScotRail .cif file, extract a timetable containing only information on:
    BS - basic schedule signature
    LO - origin location
    LI - intermediate location signature
    LT - terminatin location signature
    :param f: .cif file to be processed
    :return: raw timetable - a list of approved signatures.
    """

    approved_prefixes = ['BS', 'LO', 'LI', 'LT']
    raw_timetable = []
    for row in f:
        record_identity = row[0:2]
        if record_identity in approved_prefixes:
            raw_timetable.append(row)
    return raw_timetable

def get_journey_data(signature):
    """
    Given a row signature from a .cif file, return the parsed data as dictionary
    :param signature: one record from .cif file
    :return: dictionary with data parsed from .cif record
    """
    # This dictionary contains information on how to parse different records.
    specification_dict = {
        'BS': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'transaction_type': (1, 3),
            'train_uid': (6, 4),
            'date_runs_from': (6, 10),
            'date_runs_to': (6, 16),
            'days_run': (7, 22),
            'bank_holiday_running': (1, 29),
            'train_status': (1, 30),
            'train_category': (2, 31),
            'train_identity': (4, 33),
            'headcode': (4, 37),
            'course_indicator': (1, 41),
            'profit_centre_code': (8, 42),
            'business_sector': (1, 50),
            'power_type': (3, 51),
            'timing_load': (4, 54),
            'speed': (3, 58),
            'operating_chars': (6, 61),
            'train_class': (1, 67),
            'sleepers': (1, 68),
            'reservations': (1, 69),
            'connect_indicator': (1, 70),
            'catering_code': (4, 71),
            'service_branding': (4, 75),
            'spare': (1, 79),
            'stp_indicator': (1, 80), },
        'LO': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (8, 3),
            'scheduled_departure_time': (5, 11),
            'public_departure_time': (4, 16),
            'platform': (3, 20),
            'line': (3, 23),
            'engineering_allowance': (2, 26),
            'pathing_allowance': (2, 28),
            'activity': (12, 30),
            'performance_allowance': (2, 42),
            'spare': (37, 44), },
        'LI': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (8, 3),
            'scheduled_arrival_time': (5, 11),
            'scheduled_departure_time': (5, 16),
            'scheduled_pass': (5, 21),
            'public_arrival_time': (4, 26),
            'public_departure_time': (4, 30),
            'platform': (4, 34),
            'line': (3, 37),
            'path': (3, 40),
            'activity': (12, 43),
            'engineering_allowance': (2, 55),
            'pathing_allowance': (2, 57),
            'performance_allowance': (2, 59),
            'spare': (20, 61), },
        'LT': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (8, 3),
            'scheduled_arrival_time': (5, 11),
            'public_arrival_time': (4, 16),
            'platform': (3, 20),
            'path': (3, 23),
            'activity': (12, 26),
            'spare': (43, 80),}
    }

    # Identify what the record holds.
    record_identity = signature[0:2]
    try:
        specification = specification_dict[record_identity]
    except KeyError as e:
        print("{} - CIF signature not found for this record. Please expand specification_dict.".
              format(signature, file=sys.stderr))
        sys.exit(1)

    # Create a parsed dictionary.
    d = dict.fromkeys(list(specification.keys()))
    for key in specification.keys():
        start = specification[key][1] - 1
        end = start + specification[key][0]
        value = signature[start:end].strip()
        # Convert arrival, departure and passing times to proper datetime objects.
        if record_identity != 'BS':
            try:
                if 'time' in key:
                    value = datetime.datetime.strptime(value[0:4], "%H%M").time()
                if 'public_arrival' in key:
                    value = datetime.datetime.strptime(value[0:4], "%H%M").time()
                if 'public_departure' in key:
                    value = datetime.datetime.strptime(value[0:4], "%H%M").time()
                if 'public_departure' in key:
                    value = datetime.datetime.strptime(value[0:4], "%H%M").time()
                if 'scheduled_pass' in key:
                    value = datetime.datetime.strptime(value[0:4], "%H%M").time()
            except:
                pass
        d[key] = value
        if record_identity == 'BS':
            d['unique_identifier'] = str(d['train_uid'])\
            + '_' + str(d['train_status'])\
            + '_' + str(d['train_category'])\
            + '_' + str(d['train_identity'])\
            + '_' + str(d['train_class'])
    return d

def check_duplicate_stops(timetable):
    stops = [stop['location'] for stop in timetable]
    duplicates = [x for n, x in enumerate(stops) if x in stops[:n]]
    if duplicates != []:
        return True

def create_journey_timetable(id_list, journey_header, raw_timetable):
    """
    Create a list of stops making up a particular journey. The assumption is that you feed only id's making up a full
    journey, so:
    * first id has a LO signature
    * last id has a LT signature
    * intermediate id's have LI signatures

    There are two cases:
    * journey with intermediate stops, i.e more than two stops in total are provided.
    * journey without intermediate stops, i. two stops in total are provided.

    :param id_list: list of indices that make up the journey
    :param raw_timetable: raw timetable extracted from .cif file
    :param service_id: journey name/header
    :return: list of dictionaries containing information on stops in a particular journey
    """
    # Extract data from journey head - get everything except record identity
    journey_header_data = {key: value for (key, value) in journey_header.items() if not 'record_identity' in key}

    # Set up a dictionary container.
    timetable = []
    if len(id_list) > 2:
        #               Create and append origin header.
        origin_header = get_journey_data(raw_timetable[id_list[0]])
        next_stop_header = get_journey_data(raw_timetable[id_list[1]])

        origin_header['next_stop_id'] = next_stop_header['location']
        origin_header['next_stop_arrival_time'] = next_stop_header['scheduled_arrival_time']
        timetable.append(origin_header)

        destination_header = get_journey_data(raw_timetable[id_list[-1]])

        for header_id in id_list[1:-1]:
            stop_header = get_journey_data(raw_timetable[header_id])
            next_stop_header = get_journey_data(raw_timetable[header_id + 1])

            stop_header['next_stop_id'] = next_stop_header['location']
            stop_header['next_stop_arrival_time'] = next_stop_header['scheduled_arrival_time']
            timetable.append(stop_header)

        timetable.append(destination_header)
    else:
        origin_header = get_journey_data(raw_timetable[id_list[0]])
        next_stop_header = get_journey_data(raw_timetable[id_list[1]])

        origin_header['next_stop_id'] = next_stop_header['location']
        origin_header['next_stop_arrival_time'] = next_stop_header['scheduled_arrival_time']
        timetable.append(origin_header)

        destination_header = get_journey_data(raw_timetable[id_list[-1]])
        timetable.append(destination_header)

    # Check for duplicated stops
    if check_duplicate_stops(timetable):
        has_duplicates = 1
    else:
        has_duplicates = 0
    #     Add journey data to each stop.
    for stop in timetable:
        stop['has_duplicated_stops'] = has_duplicates
        stop = stop.update(journey_header_data)

    return timetable

def process_raw_scotrail_timetable(raw_timetable):
    """
    Given a raw scotrail timetable, this function analyzes which stops belong to which journey and returns a proper timetable
    as a list of dictionaries.
    :param raw_timetable: raw timetable extracted from a .cif file
    :return:
    """
    timetable = []
    journey_count = 0
    for i, signature in enumerate(raw_timetable):
        #   'BS' prefix designates a start of a new journey header.
        if signature.startswith('BS'):
            #       Set a flag to false until you find another 'BS' prefix.
            next_journey_found = False
            #       Get journey header and extract some data we'll append to individual stops.
            journey_header = get_journey_data(signature)
            train_uid = journey_header['train_uid']
            #       Count stops from 1 to next to next journey header.
            stop_count = 1
            #       Set up a container list for journey stop id's.
            print("Analyzing journey no {}: {}".format(journey_count + 1, train_uid))
            #           Gather a list of stop_indices respective to currently analyzed journey.
            stops_id = []
            while not next_journey_found:
                current_id = i + stop_count
                try:
                    current_row = raw_timetable[current_id]
                    if current_row.startswith('BS'):
                        next_journey_found = True
                        continue
                    stops_id.append(current_id)
                except:
                    break
                stop_count += 1
#             Create a journey timetable given a list of stop id's.
            journey_timetable = create_journey_timetable(stops_id, journey_header, raw_timetable)
            timetable.extend(journey_timetable)
            journey_count += 1

    print("{} journeys analyzed.\n".format(journey_count))
    return timetable

def main():
    # Clock starts.
    START = time.time()
    path = paths['cif']
    print("Checking directory tree.")
    if not os.path.exists(paths['output']):
        os.mkdir(os.path.join(paths['output']))
    if not os.path.exists(os.path.join(paths['output'], 'duplicates')):
        os.mkdir(os.path.join(paths['output'], 'duplicates'))
        
    print("CIF Timetable conversion commencing.\nAnalyzing files in: {}".format(path))
    filepaths = [os.path.join(path, file) for file in os.listdir(path) if file.lower().endswith('.cif')]
    print(".cif file list:\n", *filepaths, sep="\n")
    for i, file in enumerate(filepaths):
        start = time.time()
        print("\nAnalyzing: {}".format(file))
        header = get_file_header(file)
        # Open the .cif file.
        f = open(filepaths[i], "r")
        # Process the data.,
        raw_timetable = extract_raw_scotrail_timetable(f)
        timetable = process_raw_scotrail_timetable(raw_timetable)
        
        df = pd.DataFrame(timetable)
        # Check for duplicate entries.
        duplicates = df[df.duplicated()]
        if not duplicates.empty:
            duplicates_filename = file.split('\\')[-1].split('.')[0] + '_duplicates.csv'
            duplicates.to_csv(os.path.join(paths['output'], 'duplicates', duplicates_filename))
        df.drop_duplicates(inplace=True)
        
        df = pd.DataFrame(timetable)
        # Create "operates_on_(...) columns
        df['operates_on_mondays'] = df['days_run'].str[0]
        df['operates_on_tuesdays'] = df['days_run'].str[1]
        df['operates_on_wednesdays'] = df['days_run'].str[2]
        df['operates_on_thursdays'] = df['days_run'].str[3]
        df['operates_on_fridays'] = df['days_run'].str[4]
        df['operates_on_saturdays'] = df['days_run'].str[5]
        df['operates_on_sundays'] = df['days_run'].str[6]

        df = df[[
            'record_identity',
            'train_uid',
            'train_status',
            'train_category',
            'train_identity',
            'train_class',
            'unique_identifier',
            'has_duplicated_stops',
            'location',
            'scheduled_arrival_time',
            'scheduled_departure_time',
            'public_arrival_time',
            'public_departure_time',
            'scheduled_pass',
            'next_stop_id',
            'next_stop_arrival_time',
            'operates_on_mondays',
            'operates_on_tuesdays',
            'operates_on_wednesdays',
            'operates_on_thursdays',
            'operates_on_fridays',
            'operates_on_saturdays',
            'operates_on_sundays',
            'date_runs_from',
            'date_runs_to',
            'bank_holiday_running',
            'platform',
            'line',
            'path',
            'engineering_allowance',
            'pathing_allowance',
            'activity',
            'performance_allowance',
            'transaction_type',
            'headcode',
            'course_indicator',
            'profit_centre_code',
            'business_sector',
            'power_type',
            'timing_load',
            'speed',
            'operating_chars',
            'sleepers',
            'reservations',
            'connect_indicator',
            'catering_code',
            'service_branding',
            'stp_indicator'
        ]]
        
        df.to_csv(os.path.join(paths['output'], "{}_timetable.csv".format(os.path.basename(file).split('.')[0])), index=False)
        try:
            df.to_excel(os.path.join(paths['output'], "{}_timetable.xlsx".format(os.path.basename(file).split('.')[0])), index=False)
        except:
            print("Error saving {} to excel.".format(os.path.basename(file).split('.')[0]))
        
        print('Runtime: {0:.2f}'.format(time.time() - start))
    print("Finished successfully.")
    
if __name__ == '__main__':
    main()

        
