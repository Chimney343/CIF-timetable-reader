
"""
Scotrail_TRACC_stop_frequency_counter.py

This tool analyzes timetables created with Scotrail_CIF_timetable_converter and returns:
- a summary of stop frequencies, distinguishing between routes heading inbound
and outbound
- a summary of stops and their associated routes and their respective outbound
and inbound frequencies


"""

# GLOBAL PARAMETERS
paths = {
    # Path to folder with timetable data (that is - .csv timetable converted from RAW CIF file)
        'timetable': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\Timetables\ScotRail',
    # Name of folder in timetable data to store stop frequencies.
       'output': r'C:\Users\kominem\Jacobs\STPR2 - TRACC\TRACC_COVID19 Support\Stop Frequency Results\Stop Frequency_Scripting_Output\Stop_Frequency_ScotRail'
}

# Day of operation - from monday to sunday.
DAY = 'tuesday'

# Starting/ending point.
START_HOUR = 8
START_MINUTES = 00
END_HOUR = 9
END_MINUTES = 00

# Do not edit below this point!
# ===================================================================================================
import os
import time
import pandas as pd
import datetime



def get_stop_frequency(df_timetable, day, start_hour, end_hour, group_by_departure=True, group_by_routes=False,
                       get_services=False,
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
    #   Set up parameters.
    start = datetime.time(hour=start_hour, minute=start_minute)
    end = datetime.time(hour=end_hour, minute=end_minute)
    day = 'operates_on_' + day.lower() + 's'
    arrival_column = 'public_arrival_time'
    departure_column = 'public_departure_time'
    
    if group_by_routes:
        group_by_cols = ['location', 'unique_identifier']
        output_columns = ['location', 'unique_identifier', day]
    else:
        group_by_cols = ['location']
        output_columns = ['location', day]

    #   Trim the timetable to day, hour and direction.
    total = pd.concat([
        df_timetable.loc[
            (df_timetable[day] == 1)
            & (df_timetable['scheduled_pass'].isna())
            & (df_timetable[arrival_column] >= start)
            & (df_timetable[arrival_column] <= end)],
        df_timetable.loc[
            (df_timetable[day] == 1)
            & (df_timetable['scheduled_pass'].isna())
            & (df_timetable[departure_column] >= start)
            & (df_timetable[departure_column] <= end)]
    ]) \
        .drop_duplicates(subset=[
        'location',
        'unique_identifier',
        day,
        'scheduled_arrival_time',
        'scheduled_departure_time',
        'public_arrival_time',
        'public_departure_time',
        'scheduled_pass',
    ])

    if get_services:
        #   Analyze services on each location.
        locations_and_routes = []
        keys = ['location', 'total_routes']
        locations = total['location'].unique().tolist()

        #   Get a list of routes at evey location
        for i, location in enumerate(locations):
            data = dict.fromkeys(keys)
            data['location'] = location
        
            total_routes = set(total[total['location'] == location]['unique_identifier'] \
                                 .unique())
            data['total_routes'] = list(total_routes)
            locations_and_routes.append(data)
            print("Location {}: {}/{}\nTotal routes: {}\n".format(location, i+1, len(locations), total_routes))
        
        services = pd.DataFrame(locations_and_routes)

    # Analyze service frequencies.
    total_freq = total \
        .groupby(group_by_cols) \
        .sum() \
        .reset_index() \
        [output_columns]

    # Get it all together.
    frequency = total_freq \
        .rename(columns={day: 'total_frequency'})\
        .sort_values(by='total_frequency', ascending=False)

    if get_services:
        frequency = frequency.merge(services, how='left', on='location')

    #       Add prefix for easier joining with shapefiles.
    frequency['location'] = frequency['location'].apply(lambda x: 'QLN9100' + str(x).strip())

    return frequency


def load_timetable(csv):
    """
    Load a timetable created with ScotRail_CIF_timetable_converter.py and cast proper 
    dtypes. 
    """
    # Cast column dtypes.
    df = pd.read_csv(csv, dtype={
        'unique_identifier': str,
        'train_uid': str,
        'train_status': str,
        'train_category': str,
        'train_identity': str,
        'train_class': str,
        'unique_identifier': str,
        'location': str
    })
    
    #   Cast time columns to datetime.time objects.
    time_cols = [
        'scheduled_arrival_time',
        'scheduled_departure_time',
        'public_arrival_time',
        'public_departure_time',
        'next_stop_arrival_time',]
    for col in time_cols:
        df[col] = pd.to_datetime(df[col]).dt.time

    return df


def main():
    """
    Given variables: DAY / START_HOUR / END_HOUR, this function will analyze all timetables in source folder, perform
    a stop frequency calculation for all stops within the timetable and return a .csv with stop frequency in given period.
    :return:
    """
    START = time.time()
    print("Frequency calculation commencing.")
    #   Check directory tree.
    output_folder = os.path.join(paths['output'],
                                 "{}_{}_{}_to_{}_{}".format(DAY, str(START_HOUR), str(START_MINUTES), str(END_HOUR),
                                                            str(END_MINUTES)))
    if not os.path.exists(paths['output']):
        os.mkdir(paths['output'])
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    filepaths = [file for file in os.listdir(paths['timetable']) if file.endswith('timetable.csv')]
    for i, file in enumerate(filepaths):
        print(os.path.join(paths['timetable'], file))
        df_timetable = load_timetable(os.path.join(paths['timetable'], file))
    
        print("{}/{} - Analyzing timetable from {}.".format(i + 1, len(filepaths), filepaths[i]))
        print('\tDay: {}\n\tTimeframe: {}-{}\n\tCalculating frequency...'.format(DAY, START_HOUR, END_HOUR))
        frequency = get_stop_frequency(df_timetable, DAY, START_HOUR, END_HOUR, get_services=True)
        route_frequency = get_stop_frequency(df_timetable, DAY, START_HOUR, END_HOUR, group_by_routes=True)

        print('\tSaving.')
        output_file = "{}_{}_{}_{}_to_{}_{}.csv".format(os.path.basename(file).split('_')[0], DAY, str(START_HOUR), str(START_MINUTES), str(END_HOUR),
                                                        str(END_MINUTES))
        frequency.to_csv(os.path.join(output_folder, output_file), index=False)
        frequency.to_excel(os.path.join(output_folder, output_file.replace('csv', 'xlsx')), index=False)

        output_route_frequency = "{}_{}_{}_{}_to_{}_{}_route_frequency.csv".format(os.path.basename(file).split('_')[0], DAY, str(START_HOUR),
                                                                                   str(START_MINUTES), str(END_HOUR),
                                                                                   str(END_MINUTES))
        route_frequency.to_csv(os.path.join(output_folder, output_route_frequency), index=False)
        route_frequency.to_excel(os.path.join(output_folder, output_route_frequency.replace('csv' , 'xlsx')), index=False)

    print("\nFinished.\nTotal runtime: {0:.7}".format(str(datetime.timedelta(time.time() - START))))

if __name__ == '__main__':
    main()
