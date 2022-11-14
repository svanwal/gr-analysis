import sys
import re
import numpy as np
import pandas as pd
import os.path
from csv import writer

# This function returns a list with the [lat, lon] of each point within an OSM edge
def edge_to_coords(network_edges,edge_id):
    lon = list(network_edges.loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[0])
    lat = list(network_edges.loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[1])
    edge_coords = list(zip(lon,lat))
    return [[coord[1],coord[0]] for coord in edge_coords]

# Distance between two points
def cartesian_distance(lat0,lon0,lat1,lon1):
    R = 6371.8 # Mean earth radius [km]
    lat0r = np.radians(lat0)
    lon0r = np.radians(lon0)
    lat1r = np.radians(lat1)
    lon1r = np.radians(lon1)
    
    r1 = [R*np.cos(lat0r)*np.cos(lon0r), R*np.cos(lat0r)*np.sin(lon0r), R*np.sin(lat0r)]
    r2 = [R*np.cos(lat1r)*np.cos(lon1r), R*np.cos(lat1r)*np.sin(lon1r), R*np.sin(lat1r)]
    dr = [r1[0] - r2[0], r1[1] - r2[1], r1[2] - r2[2]]
    return 1000.0*np.sqrt(dr[0]*dr[0] + dr[1]*dr[1] + dr[2]*dr[2])

# Converts a GPX file into a CSV file with a list of the latitude/longitude/elevation points
def process_gpx(filename_in, filename_out):
    
    with open(filename_in) as file:
        raw = file.read()

    # Use Regex to grab all lat/lon pairs
#     pattern = re.compile(r'lat="(?P<lat>\d+.\d+)" lon="(?P<lon>\d+.\d+)">\n\s+<ele>(?P<ele>\d+)<') # did not account for negative elevations
    pattern = re.compile(r'<trkpt lat="(?P<lat>\d+.\d+)" lon="(?P<lon>\d+.\d+)">\n\s+<ele>(?P<ele>(?:-?\d+)?)</ele>')
    dat = pattern.findall(raw)

    # Write the lat/lon pairs to a CSV file
    with open(filename_out, "w") as file:
        csv_writer = writer(file)
        csv_writer.writerow(['latitude','longitude','elevation'])
        for row in dat:
            csv_writer.writerow(row)
            
def write_batch(filename, segment_list):
    
    print('   Writing outputs to file...')
    with open(filename, 'w') as file:
        csv_writer = writer(file)
        headers = ['x0','y0','x1','y1','d_cart','d_osm','highway','surface','tracktype']
        csv_writer.writerow(headers)
        for segment in segment_list:
            csv_writer.writerow(segment)
            
def write_batch_places(filename, data_roads_section):
    
    print('   Writing outputs to file...')
    data_roads_section.to_csv(filename)
#     with open(filename, 'w') as file:
#         csv_writer = writer(file)
#         headers = ['x0','y0','x1','y1','d_cart','d_osm','highway','surface','tracktype','dev_dist']
#         csv_writer.writerow(headers)
#         for i, segment in data_roads_section.iterrows():
#             csv_writer.writerow(segment)
            
def merge_roads(trailname, trail, points_per_batch):
    
    n_batch = int(np.ceil(trail.shape[0]/points_per_batch)) # Number of batches to be run
    
    # Load the first batch
    filename = f'cache/{trailname}_roads_0to{points_per_batch}.csv'
    data = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str})
    
    # Load and merge the remaining batches
    for b in range(1,n_batch): # b is the batch counter
        n1 = b*points_per_batch # First point
        n2 = min(n1 + points_per_batch, len(trail)) # Last point
        filename = f'cache/{trailname}_roads_{n1}to{n2}.csv'
        data_new = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str})
        data = pd.concat([data,data_new],ignore_index=True)
        
    return data

def write_roads(trailname, data_roads):
    
    filename = f'cache/{trailname}_roads.csv'
    data_roads.to_csv(filename)

def read_roads(trailname):
    
    filename = f'cache/{trailname}_roads.csv'
    return pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str},index_col=0)

def merge_places(trailname, data_roads, points_per_batch_places):
    
    n_batch = int(np.ceil(data_roads.shape[0]/points_per_batch_places)) # Number of batches to be run
    
    # Load the first batch
    filename = f'cache/{trailname}_places_0to{points_per_batch_places-1}.csv'
    data = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str},index_col=0)
    
    # Load and merge the remaining batches
    for b in range(1,n_batch): # b is the batch counter
        n1 = b*points_per_batch_places # First point
        n2 = min(n1 + points_per_batch_places, data_roads.shape[0]) - 1 # Last point
#         print(f'Merging section n1={n1} to n2={n2}')
#         print(f'no of rows {data_roads.shape[0]}')
        filename = f'cache/{trailname}_places_{n1}to{n2}.csv'
        data_new = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str},index_col=0)
        data = pd.concat([data,data_new],ignore_index=True)
        
    return data

def write_places(trailname, data_places):
    
    filename = f'cache/{trailname}_places.csv'
    data_places.to_csv(filename)
    
def write_processed(trailname, data):
    
    filename = f'data_output/{trailname}_processed.csv'
    data.to_csv(filename)
    
def read_processed(trailname):
    
    filename_processed = 'data_output/' + trailname + '_processed.csv'
    if not os.path.isfile(filename_processed): # The PROCESSED file does not exist
        ValueError('Error file not found, did you process it?')
    data = pd.read_csv(filename_processed,
                       dtype={'highway':str, 'surface': str, 'tracktype':str,
                              'city8':str, 'city9':str, 'city':str},
                       index_col=0)
    return data

def read_places(trailname):
    
    filename = f'cache/{trailname}_places.csv'
    return pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str},index_col=0)

def get_gpx(trailname):
    
    filename_gpx = 'data_input/' + trailname + '.gpx'
    filename_csv = 'data_output/' + trailname + '.csv'
    if not os.path.isfile(filename_csv): # The GPX file was not processed into a clean CSV file before
        if not os.path.isfile(filename_gpx): # The GPX file does not exist, throw error
            raise ValueError(f'The GPX file <{filename_gpx}> was not found! Please make sure it exists.')
        else: # The GPX file exists, so convert it into a clean CSV file
            print(f'Converting GPX file <{filename_gpx}> into cleaned CSV file <{filename_csv}>...')
            process_gpx(filename_gpx,filename_csv)
            print('Completed conversion.')
    print(f'Loading trail points from <{filename_gpx}>...')
    trail = pd.read_csv(filename_csv) # Now read the cleaned CSV file into a DataFrame (latitude, longitude, elevation)
    print('Finished loading.')
    
    return trail