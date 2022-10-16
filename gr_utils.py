import sys
import re
from csv import writer

# def testing(x,y):
#     return x+y

# # This function computes the distances between point-node1 and point-node2
# def get_distances(node1,node2,point):
#     R = 6371.8 # Mean earth radius [km]
#     # Converting degrees to radians
#     lon1 = np.radians(node1[1])
#     lat1 = np.radians(node1[0])
#     lon2 = np.radians(node2[1])
#     lat2 = np.radians(node2[0])
#     lat  = np.radians(point[0])
#     lon  = np.radians(point[1])
#     # Computing distances between point-node1 and point-node2
#     r1 = [R*np.cos(lat1)*np.cos(lon1), R*np.cos(lat1)*np.sin(lon1), R*np.sin(lat1)]
#     r2 = [R*np.cos(lat2)*np.cos(lon2), R*np.cos(lat2)*np.sin(lon2), R*np.sin(lat2)]
#     r  = [R*np.cos(lat)*np.cos(lon),   R*np.cos(lat)*np.sin(lon),   R*np.sin(lat)]
#     dr1 = [r1[0]-r[0], r1[1]-r[1], r1[2]-r[2]]
#     dr2 = [r2[0]-r[0], r2[1]-r[1], r2[2]-r[2]]
#     d1 = np.sqrt(dr1[0]*dr1[0] + dr1[1]*dr1[1] + dr1[2]*dr1[2])
#     d2 = np.sqrt(dr2[0]*dr2[0] + dr2[1]*dr2[1] + dr2[2]*dr2[2])
#     return d1,d2

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