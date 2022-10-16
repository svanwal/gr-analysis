import sys
import re
import numpy as np
import pandas as pd
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
    pattern = re.compile(r'lat="(?P<lat>\d+.\d+)" lon="(?P<lon>\d+.\d+)">\n\s+<ele>(?P<ele>\d+)<')
    dat = pattern.findall(raw)

    # Write the lat/lon pairs to a CSV file
    with open(filename_out, "w") as file:
        csv_writer = writer(file)
        csv_writer.writerow(['latitude','longitude','elevation'])
        for row in dat:
            csv_writer.writerow(row)
            
def write_batch(filename, segment_list):
    
    print('   Writing outputs to file')
    with open(filename, 'w') as file:
        csv_writer = writer(file)
        headers = ['x0','y0','x1','y1','d_cart','d_osm','highway','surface','tracktype']
        csv_writer.writerow(headers)
        for segment in segment_list:
            csv_writer.writerow(segment)
            
def merge_roads(trailname, trail, points_per_batch):
    
    n_batch = int(np.ceil(trail.shape[0]/points_per_batch)) # Number of batches to be run
    
    # Load the first batch
    filename = f'cache/{trailname}_0to{points_per_batch}.csv'
    data = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str})
    
    # Load and merge the remaining batches
    for b in range(1,n_batch): # b is the batch counter
        n1 = b*points_per_batch # First point
        n2 = min(n1 + points_per_batch, len(trail)) # Last point
        filename = f'cache/{trailname}_{n1}to{n2}.csv'
        data_new = pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str})
        data = pd.concat([data,data_new],ignore_index=True)
        
    return data

def write_roads(trailname, data_roads):
    
    filename = f'cache/{trailname}_roads.csv'
    data_roads.to_csv(filename)

def read_roads(trailname):
    
    filename = f'cache/{trailname}_roads.csv'
    return pd.read_csv(filename,dtype={'highway':str, 'surface': str, 'tracktype':str})