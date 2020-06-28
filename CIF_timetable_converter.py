"""
CIF_timetable_converter.py

Analyze raw .cif files and convert them into .csv timetables proper. The only parameter
to adjust is the path to .cif file folder below and the output folder.

"""

paths = {
    'cif': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\Timetables',
    'output': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\Timetables\Traveline',
}


# Do not edit below this point!
# ===================================================================================================

import os
import pandas as pd
import sys
import re
import datetime
import time


def extract_raw_timetable(f):
    """
    Given a .cif file, extract a timetable containing only information on:
    QS - journey header signature
    QO - journey origin signature
    QI - journey intermediate signature
    QT - journey destination signature
    :param f: .cif file to be processed
    :return: raw timetable - a list of approved signatures.
    """

    approved_prefixes = ['QS', 'QO', 'QI', 'QT']
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
        'QS': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'transaction_type': (1, 3),
            'operator': (4, 4),
            'unique_journey_identifier': (6, 8),
            'first_date_of_operation': (8, 14),
            'last_date_of_operation': (8, 22),
            'operates_on_mondays': (1, 30),
            'operates_on_tuesdays': (1, 31),
            'operates_on_wednesdays': (1, 32),
            'operates_on_thursdays': (1, 33),
            'operates_on_fridays': (1, 34),
            'operates_on_saturdays': (1, 35),
            'operates_on_sundays': (1, 36),
            'school_term_time': (1, 37),
            'bank_holidays': (1, 38),
            'route_number_(identifier)': (4, 39),
            'running_board': (6, 43),
            'vehicle_type': (8, 49),
            'registration_number': (8, 57),
            'route_direction': (1, 65),
            'unique_id': (13, 1)},
        'QO': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (12, 3),
            'published_departure_time': (4, 15),
            'bay_number': (3, 19),
            'timing_point_indicator': (2, 22),
            'fare_stage_indicator': (2, 24), },
        'QI': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (12, 3),
            'published_arrival_time': (4, 15),
            'published_departure_time': (4, 19),
            'activity_flag': (1, 23),
            'bay_number': (3, 24),
            'timing_point_indicator': (2, 27),
            'fare_stage_indicator': (2, 29), },
        'QT': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'location': (12, 3),
            'published_arrival_time': (4, 15),
            'bay_number': (3, 19),
            'timing_point_indicator': (2, 22),
            'fare_stage_indicator': (2, 24)}
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
        # Convert arrival and departure times to proper datetime objects.
        if record_identity != 'QS' and 'time' in key:
            value = datetime.datetime.strptime(value, "%H%M").time()
        d[key] = value
    if record_identity == 'QS':
        d['unique_identifier'] = str(d['operator']) + str(d['unique_journey_identifier'])
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
    * first id has a QO signature
    * last id has a QT signature
    * intermediate id's have QI signatures

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
        origin_header['next_stop_arrival_time'] = next_stop_header['published_arrival_time']
        timetable.append(origin_header)

        destination_header = get_journey_data(raw_timetable[id_list[-1]])

        for header_id in id_list[1:-1]:
            stop_header = get_journey_data(raw_timetable[header_id])
            next_stop_header = get_journey_data(raw_timetable[header_id + 1])

            stop_header['next_stop_id'] = next_stop_header['location']
            stop_header['next_stop_arrival_time'] = next_stop_header['published_arrival_time']
            timetable.append(stop_header)

        timetable.append(destination_header)
    else:
        origin_header = get_journey_data(raw_timetable[id_list[0]])
        next_stop_header = get_journey_data(raw_timetable[id_list[1]])

        origin_header['next_stop_id'] = next_stop_header['location']
        origin_header['next_stop_arrival_time'] = next_stop_header['published_arrival_time']
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


def process_raw_timetable(raw_timetable):
    """
    Given a raw timetable, this function analyzes which stops belong to which journey and returns a proper timetable
    as a list of dictionaries.
    :param raw_timetable: raw timetable extracted from a .cif file
    :return:
    """
    timetable = []
    journey_count = 0
    for i, signature in enumerate(raw_timetable):
        #   'QS' prefix designates a start of a new journey header.
        if signature.startswith('QS'):
            #       Set a flag to false until you find another 'QS' prefix.
            next_journey_found = False
            #       Get journey header and extract some data we'll append to individual stops.
            journey_header = get_journey_data(signature)
            operator = journey_header['operator']
            service_id = journey_header['unique_id']
            #       Count stops from 1 to next to next journey header.
            stop_count = 1
            #       Set up a container list for journey stop id's.
            print("Analyzing journey no {}: {}".format(journey_count + 1, service_id))
            #           Gather a list of stop_indices respective to currently analyzed journey.
            stops_id = []
            while not next_journey_found:
                current_id = i + stop_count
                try:
                    current_row = raw_timetable[current_id]
                    if current_row.startswith('QS'):
                        next_journey_found = True
                        continue
                    stops_id.append(current_id)
                except:
                    break
                stop_count += 1
            # Create a journey timetable given a list of stop id's.
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
    filepaths = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.cif')]
    print(".cif file list:\n", *filepaths, sep="\n")
    for i, file in enumerate(filepaths):
        start = time.time()
        print("\nAnalyzing: {}".format(file))
        output_filename = file.split('\\')[-1].split('.')[0] + '_timetable.csv'
        # Open the .cif file.
        f = open(filepaths[i], "r")
        # Process the data.,
        raw_timetable = extract_raw_timetable(f)
        timetable = process_raw_timetable(raw_timetable)
        df = pd.DataFrame(timetable)
        # Check for duplicate entries.
        duplicates = df[df.duplicated()]
        if not duplicates.empty:
            duplicates_filename = file.split('\\')[-1].split('.')[0] + '_duplicates.csv'
            duplicates.to_csv(os.path.join(paths['output'], 'duplicates', duplicates_filename))
        df.drop_duplicates(inplace=True)

        # Rearrange columns.
        df = df[[
            'record_identity',
            'operator',
            'unique_journey_identifier',
            'unique_identifier',
            'route_number_(identifier)',
            'route_direction',
            'has_duplicated_stops',
            'location',
            'published_arrival_time',
            'published_departure_time',
            'next_stop_id',
            'next_stop_arrival_time',
            'operates_on_mondays',
            'operates_on_tuesdays',
            'operates_on_wednesdays',
            'operates_on_thursdays',
            'operates_on_fridays',
            'operates_on_saturdays',
            'operates_on_sundays',
            'first_date_of_operation',
            'last_date_of_operation',
            'school_term_time',
            'activity_flag',
            'bank_holidays',
            'running_board',
            'vehicle_type',
            'registration_number',
            'bay_number',
            'fare_stage_indicator',
            'timing_point_indicator',
        ]]

        # Exclude records with first date of operation exceeding today.
        df['first_date_of_operation'] = pd.to_datetime(df['first_date_of_operation'])
        df = df[df['first_date_of_operation'] < datetime.datetime.now()]
        # Safeguard against routes listed as 'UNKN'; "unknown".
        df.loc[(df['route_number_(identifier)'] == 'UNKN'),'route_number_(identifier)']=df['unique_identifier']
        # Split timetable by vehicle type and save each vehicle type individually.
        for mode in df['vehicle_type'].unique():
            temp_df = df[df['vehicle_type'] == mode]
            output_filename = file.split('\\')[-1].split('.')[0] + '_{}_timetable.csv'.format(mode)
            print('Saving {} timetable:\n{}'.format(mode, os.path.join(paths['output'], output_filename)))
            temp_df.to_csv(os.path.join(paths['output'], output_filename), index=False)
            try:
                temp_df.to_excel(os.path.join(paths['output'], output_filename.replace('.csv', '.xlsx')), index=False)
            except:
                print("Error writing {} timetable to excel.".format(mode))

        print('Runtime: {0:.2f}'.format(time.time() - start))

    print("Finished successfully.")


# START OF PROGRAM
if __name__ == '__main__':
    main()
