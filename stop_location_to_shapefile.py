"""
stop_location_to_shapefile.py

"""
import os
import pandas as pd
import geopandas
import sys
import time

# GLOBALS
paths = {
    'source': 'CIF_data',
    'output': 'shapefiles'
}


# Do not edit below this point!
# ===================================================================================================

def extract_raw_stop_location(f):
    """
    Given a .cif file, extract a set of records containing information on:
    QL - bus location
    QB - bus additional location information
    :param f: .cif file to be processed
    :return: raw stop locations - a list of approved signatures.
    """

    approved_prefixes = ['QL', 'QB']
    raw_timetable = []
    for row in f:
        record_identity = row[0:2]
        if record_identity in approved_prefixes:
            raw_timetable.append(row)
    return raw_timetable


def get_location_data(signature):
    """
    Given a row signature from a .cif file, return the parsed data as dictionary
    :param signature: one record from .cif file
    :return: dictionary with data parsed from .cif record
    """
    # This dictionary contains information on how to parse different records.
    specification_dict = {
        'QL': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'transaction_type': (1, 3),
            'operator': (12, 4),
            'full_location': (48, 16),
            'gazetteer_code': (1, 64),
            'point_type': (1, 65),
            'national_gazetteer_ID': (8, 66)},
        'QB': {
            #   'data_type': (chunk size, starting point [1-indexed])
            'record_identity': (2, 1),
            'transaction_type': (1, 3),
            'location': (12, 4),
            'grid_reference_easting': (8, 16),
            'grid_reference_northing': (8, 24),
            'distric_name': (24, 32),
            'town_name': (24, 56)}
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
        d[key] = value

    return d


def make_gdf_with_locations(raw_stop_locations):
    """
    From an extract of raw stop location records extracted from a .cif file, return a properly formatted geodataframe
    object.
    :param raw_stop_locations:
    :return:
    """
    stop_locations = []
    for location in raw_stop_locations:
        d = get_location_data(location)
        stop_locations.append(d)

    ql_frame = pd.DataFrame(stop_locations[::2])
    qb_frame = pd.DataFrame(stop_locations[1::2])

    df = pd.concat([ql_frame, qb_frame], axis=1) \
        .apply(pd.to_numeric, errors='ignore')

    gdf = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(df['grid_reference_easting'], df['grid_reference_northing']))
    gdf.crs = {'init': 'epsg:27700'}
    return gdf


def main():
    START = time.time()
    print("CIF stop location extraction commencing.\nAnalyzing files in: {}".format(paths['source']))
    filepaths = [os.path.join(paths['source'], file) for file in os.listdir(paths['source']) if file.endswith('.cif')]
    print(".cif file list:\n", *filepaths, sep="\n")
    #   Check directory tree.
    if not os.path.exists(paths['output']):
        os.mkdir(paths['output'])
    for file in filepaths:
        print("\nAnalyzing: {}".format(file))
        f = open(file, "r")
        output_filename = file.split('\\')[-1].replace('.cif', '.shp')
        raw_stop_locations = extract_raw_stop_location(f)
        gdf = make_gdf_with_locations(raw_stop_locations)

        print('Saving: {}'.format(output_filename))
        gdf.to_file(os.path.join(paths['output'], output_filename))

    print("\nFinished.\nTotal runtime: {0:.7}".format(str(time.time() - START)))


if __name__ == '__main__':
    main()
