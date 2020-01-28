"""
CIF_timetable_converter.py
"""

# GLOBAL PARAMETERS
paths = {
    # Path to folder with timetable data.
    'timetable':
        '..\\TRACC Data\PT Timetable Data',
    # Name of folder in timetable data to store stop frequencies.
    'output': 'stop_frequency'
}

# Day of operation - from monday to sunday.
DAY = 'tuesday'

# Starting/ending point.
START_HOUR = 8
START_MINUTES = 0
END_HOUR = 9
END_MINUTES = 0

MODES = {
    'ferry': 'ATCO_Ferry_timetable.csv',
    'bus': 'Bus_2_timetable.csv',
    'coach': 'Coach_1_timetable.csv',
    'metro': 'Metro_3_timetable.csv',
    'rail': 'NationalRail_4_timetable.csv',
    'tram': 'Tram_5_timetable.csv',
}

# Do not edit below this point!
# ===================================================================================================
import os
import time
import pandas as pd
import datetime

def get_stop_frequency(df_timetable, day, start_hour, end_hour, group_by_routes=False, group_by_departure=True,
                       start_minute=0, end_minute=0):
    """
    Given a timetable produced from a .cif file with CIF-timetable-converter.py, analyze stop frequency in a given
    time period.
    :param df_timetable: timetable dataframe
    :param day: day of week
    :param start_hour: starting hour
    :param end_hour: ending hour
    :param group_by_routes: True if you want to get frequencies of particular routes on a stop
    :param group_by_departure: True if you want to analyze frequency by departure, not arrival time
    :param start_minute: starting minute
    :param end_minute: ending minute
    :return: dataframe with stops and frequencies in a given time period.
    """
    start = datetime.time(hour=start_hour, minute=start_minute)
    end = datetime.time(hour=end_hour, minute=end_minute)
    day = 'operates_on_' + day.lower() + 's'

    if group_by_routes:
        group_by_cols = ['location', 'route_number_(identifier)']
        output_columns = ['location', 'route_number_(identifier)', day]
    else:
        group_by_cols = ['location']
        output_columns = ['location', day]

    if group_by_departure:
        timestamp_column = 'published_departure_time'
    else:
        timestamp_column = 'published_arrival_time'

    # TOTAL
    # Get records within the timeframe.
    total = df_timetable.loc[
        (df_timetable[timestamp_column] >= start)
        & (df_timetable[timestamp_column] <= end)
        & (df_timetable[day] == 1)] \
        .groupby(group_by_cols) \
        .sum() \
        .reset_index() \
        [output_columns]

    # INBOUND
    inbound = df_timetable.loc[
        (df_timetable[timestamp_column] >= start)
        & (df_timetable[timestamp_column] <= end)
        & (df_timetable[day] == 1)
        #         Add condition for taking only records heading in inbound direction.
        & (df_timetable['route_direction'] == 'I')] \
        .groupby(group_by_cols) \
        .sum() \
        .reset_index() \
        [output_columns]

    # OUTBOUND
    outbound = df_timetable.loc[
        (df_timetable[timestamp_column] >= start)
        & (df_timetable[timestamp_column] <= end)
        & (df_timetable[day] == 1)
        #         Add condition for taking only records heading in outbound direction.
        & (df_timetable['route_direction'] == 'O')] \
        .groupby(group_by_cols) \
        .sum() \
        .reset_index() \
        [output_columns]

    # Merge all dataframes.
    frequency = total \
        .merge(inbound, how='left', on=group_by_cols) \
        .merge(outbound, how='left', on=group_by_cols) \
        .rename(columns={
        day + '_x': 'frequency',
        day + '_y': 'inbound_frequency',
        day: 'outbound_frequency'}) \
        .sort_values(by='frequency', ascending=False)
    #   Add prefix for easier joining with shapefiles.
    frequency['location'] = frequency['location'].apply(lambda x: 'QLN' + str(x).strip())

    return frequency


def main():
    """
    Given variables: DAY / START_HOUR / END_HOUR, this function will analyze timetables listed in MODES dictionary, perform
    a stop frequency calculation for all stops within the timetable and return a .csv with stop frequency in given period.
    :return:
    """
    # Clock starts.
    START = time.time()

    print("Frequency calculation commencing.")
    #     Loop through all MODES of travels and their associated timetables.
    for i, mode in enumerate(MODES.keys()):
        print("{}/{} - Analyzing {} timetable from {}.".format(i + 1, len(MODES.keys()), mode, MODES[mode]))
        # Cast column dtypes.
        df_timetable = pd.read_csv(os.path.join(paths['timetable'], MODES[mode]), dtype={
            'unique_identifier': str,
            'route_number_(identifier)': str,
            'location': str
        })

        #   Cast time columns to datetime.time objects.
        time_cols = ['published_arrival_time', 'published_departure_time', 'next_stop_arrival_time']
        for col in time_cols:
            df_timetable[col] = pd.to_datetime(df_timetable[col]).dt.time

        #   Calculate frequency.
        print('\tDay: {}\n\tTimeframe: {}-{}\n\tCalculating frequency...'.format(DAY, START_HOUR, END_HOUR))
        frequency = get_stop_frequency(df_timetable, DAY, START_HOUR, END_HOUR, group_by_departure=True)

        #   Save to .csv
        print('\tSaving.')
        output = "{}_{}_{}_to_{}.csv".format(mode, DAY, str(START_HOUR), str(END_HOUR))
        frequency.to_csv(os.path.join(paths['timetable'], paths['output'], output), index=False)

    print("\nFinished.\nTotal runtime: {0:.7}".format(str(time.time() - START)))

if __name__ == '__main__':
    main()