import osmnx  as ox
import pandas as pd
import numpy  as np
from itertools import groupby
from csv import writer
import warnings

# Returns the latitude and longitude of a subsection of trail as a list
def trail_to_coords(trail_section):
    
    return trail_section[['latitude','longitude']].values.tolist()

# This function returns a list with the [lat, lon] of each point within an OSM edge
# def edge_to_coords(network_edges,edge_id):
def get_single_edge_coords(network, edge_id):
    
    lon = list(network['edges'].loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[0])
    lat = list(network['edges'].loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[1])
    return [[coord[1],coord[0]] for coord in list(zip(lon,lat))]

# Returns the bounding box around a set of coords, and applies a tolerance around it
def get_bbox(coords, delta):
    
    lat_min = coords['latitude'].min() - delta
    lat_max = coords['latitude'].max() + delta
    lon_min = coords['longitude'].min() - delta
    lon_max = coords['longitude'].max() + delta
    
    return lat_min, lat_max, lon_min, lon_max
    
# Downloads the OSM network defined by a bounding box, and processes it into nodes & edges
def get_osm_network(lat_min, lat_max, lon_min, lon_max):
    
    # Download the street network based on bounding box
    print('   Downloading street network...')
    graph = ox.graph_from_bbox(lat_max, lat_min, lon_max, lon_min,
                               network_type="all_private", clean_periphery=False)
    
    # Processing the street network
    print('   Processing street network...')
    points, edges = ox.graph_to_gdfs(graph) # Convert the street network
    points.sort_index(inplace=True) # Sort the nodes for faster selections with .loc
    edges.sort_index(inplace=True) # Sort the edges for faster selections with .loc
    return {'graph':graph, 'points':points, 'edges':edges}

def sph2cart(lat, lon):
    
    R = 6371.8 # Mean Earth radius [km]
    return [R*np.cos(lat)*np.cos(lon), R*np.cos(lat)*np.sin(lon), R*np.sin(lat)]

def mynorm(r):
    
    return np.sqrt(r[0]*r[0] + r[1]*r[1] + r[2]*r[2])

# Figures out which end of an edge (P0 or P1) the point X is closest to
def get_nearest_edge_end(network, nearest_edge, X):
    
    nearest_edge_coords = get_single_edge_coords(network, nearest_edge) # Coordinates of all points that make up the edge
    P0 = nearest_edge_coords[0] # Start point
    P1 = nearest_edge_coords[-1] # End point
    
    # Converting degrees to radians
    lat0 = np.radians(P0[0])
    lon0 = np.radians(P0[1])
    lat1 = np.radians(P1[0])
    lon1 = np.radians(P1[1])
    latX = np.radians(X[0])
    lonX = np.radians(X[1])
    
    # Computing distances between P0<->X and P1<->X
    r0 = sph2cart(lat0, lon0)
    r1 = sph2cart(lat1, lon1)
    rX = sph2cart(latX, lonX)
    
    dr0 = [r0[0]-rX[0], r0[1]-rX[1], r0[2]-rX[2]]
    dr1 = [r1[0]-rX[0], r1[1]-rX[1], r1[2]-rX[2]]
    d0 = mynorm(dr0)
    d1 = mynorm(dr1)
    
    if d0 < d1:
        return nearest_edge[0] # X is closest to the start of the edge
    else:
        return nearest_edge[1] # X is closest to the end of the edge
    
def cartesian_distance(lat0,lon0,lat1,lon1):
    
    R = 6371.8 # Mean earth radius [km]
    r1 = sph2cart(np.radians(lat0), np.radians(lon0))
    r2 = sph2cart(np.radians(lat1), np.radians(lon1))
    dr = [r1[0] - r2[0], r1[1] - r2[1], r1[2] - r2[2]]
    return 1000.0*mynorm(dr) # in meters
    
def remove_successive_duplicates(arr):
    
#     print(type(arr))
    return [item[0] for item in groupby(arr)] 

def print_overwrite(text):
    
    print(text, end='\r', flush=True)

# Calculates shortest route between two nodes of the network
def get_shortest_route(network, node_id_start, node_id_end):
    
    # Calculating the routes in both directions
    node_start   = network['points'].loc[node_id_start] # Start node with relevant information
    node_end     = network['points'].loc[node_id_end]   # End node with relevant information
    vertex_start = [node_start['y'], node_start['x']] # Coordinates of start node
    vertex_end   = [node_end['y'],   node_end['x']]   # Coordinates of end node
    route1 = ox.shortest_path(network['graph'], node_id_start, node_id_end) # Route from node_start -> node_end
    route2 = ox.shortest_path(network['graph'], node_id_end, node_id_start) # Route from node_end -> node_start

    # Select the direction that results in the shortest path (we do this to deal with one-way streets)
    if len(route1)<len(route2):
        return route1
    else:
        return route2[::-1] # We flip route2 because it runs opposite to the GPX track

def get_segments(network, node_id_start, node_id_end):
    
    node_start   = network['points'].loc[node_id_start] # Start node with relevant information
    node_end     = network['points'].loc[node_id_end]   # End node with relevant information
    vertex_start = [node_start['y'], node_start['x']] # Coordinates of start node
    vertex_end   = [node_end['y'],   node_end['x']]   # Coordinates of end node

    # Selecting the corresponding edge
    edge_id = [node_id_start, node_id_end] # Corresponding edge ID
    try: # To deal with one-way streets
        edge = network['edges'].loc[(node_id_start, node_id_end)] # Get coordinates of the points that make up that edge
        edge_coords = get_single_edge_coords(network, [node_id_start, node_id_end])
    except:
        edge = network['edges'].loc[(node_id_end, node_id_start)] # Get coordinates of the points that make up that edge
        edge_coords = edge_to_coords(network_edges, [node_id_end, node_id_start])
        edge_coords = edge_coords[::-1]

    # Filling the segment_list_raw list
    segment_list = []
#     print(f'No of points in edge: {len(edge_coords)}')
    for j in range(0,len(edge_coords)-1): # Loop over all vertex pairs in the edge        
        x0 = edge_coords[j][0]
        y0 = edge_coords[j][1]
        x1 = edge_coords[j+1][0]
        y1 = edge_coords[j+1][1]
        d_cart = cartesian_distance(x0,y0,x1,y1)
        d_osm = edge['length'][0]/(len(edge_coords)-1) # just divide the length equally between segments
        highway = edge['highway'][0]
        surface = np.nan
        tracktype = np.nan
        if 'surface' in edge.columns:
            surface = edge['surface'][0]
        if 'tracktype' in edge.columns:
            tracktype = edge['tracktype'][0]
        segment_list.append([x0,y0,x1,y1,d_cart,d_osm,highway,surface,tracktype])
    
#     print(f'Length of segment_list inside get_seg: {len(segment_list)}')
    return segment_list
    
# Main map matching algorithm, may want to split this up more
# Trail coords is a list of [lat, lon] pairs
def match_roads(network,trail_coords):
    warnings.filterwarnings("ignore", category=UserWarning) # TODO: Figure out projection issue so this warning is not thrown
    
    # --- MAPPING GPX POINT TO EDGE ENDS --- #
    k = 0 # Iteration counter
    node_list_raw = [] # Will contain the nodes between which pathfinding should take place
    for trail_point in trail_coords:
        print_overwrite(f'\r   Handling GPX point {k} of {len(trail_coords)-1}...')
        nearest_edge = ox.distance.nearest_edges(network['graph'],
                                                 trail_point[1],
                                                 trail_point[0]) # ID of the edge that trail_point is closest to
        nearest_edge_end = get_nearest_edge_end(network,
                                                nearest_edge,
                                                trail_point) # ID of the edge end node that trail_point is closest to
        node_list_raw.append(nearest_edge_end) # Add it to the list
        k += 1 # Increment iteration counter
    print('')
    node_list = remove_successive_duplicates(node_list_raw) # Because # trail_point may map to the same nearest_edge_end
    
    # --- PERFORM PATHFINDING BETWEEN THE NODES IN NODE_LIST --- #
    route_list_raw = [] # Contains IDs of all nodes that make up the shortest route between the nodes in node_list
    for i in range(0,len(node_list)-1):
        print_overwrite(f'\r   Handling node_list pair {i} of {len(node_list)-2}...')
        route_list_raw.extend(get_shortest_route(network, node_list[i], node_list[i+1]))
    print('')
    route_list = remove_successive_duplicates(route_list_raw)
    
    # --- EXTRACT SEGMENTS FROM THE LIST OF TRAVELED NODES --- #
    segment_list = [] # Contains OSM edge segments that were matched to GPX track
    # Format is [x0 y0 x1 y1 d dcum highway surface tracktype]
    for i in range(0,len(route_list)-1): # Loop over all pairs in the route_list
        print_overwrite(f'\r   Handling route_list pair {i} of {len(route_list)-2}...')
        segment_list.extend(get_segments(network, route_list[i], route_list[i+1]))
#         print(f'Length of appended segment_list: {len(segment_list)}')
    print('')
    
    return segment_list

def match_batch(trail_section, trail_coords, delta):
    
    lat_min, lat_max, lon_min, lon_max = get_bbox(trail_section,delta) # Calculate the bounding box
    network = get_osm_network(lat_min, lat_max, lon_min, lon_max) # Download the street network from OSM
    segment_list = match_roads(network, trail_coords) # Get the corresponding OSM segments
    
    return network, segment_list
    
    
def find_last_index(arr, item):
    rev_arr = arr[::-1]
    j = rev_arr.index(item)
    return len(arr) - j - 1

def remove_repeat_segments(data_roads):
    

    # Calculate if there are any repeats
    data_roads_filtered = data_roads
    repeat_rows = data_roads[data_roads.duplicated(['x0','y0'])] # Rows that have a repeated starting point
    grouped_repeats = repeat_rows.groupby(['x0','y0'])
    repeat_coords = grouped_repeats.first().index.to_list() # The starting points that are repeated

    # Loop over the repeated starting points, drop the relevant rows
    for repeat_coord in repeat_coords:
        mask_x0 = data_roads_filtered['x0']==repeat_coord[0]
        mask_y0 = data_roads_filtered['y0']==repeat_coord[1]
        mask = (mask_x0 & mask_y0).values.tolist()
        # We do this check on mask because a previous rowdrop may already have removed the current repeat
        if sum(mask)>0:
            first_index = mask.index(True)
            last_index = find_last_index(mask, True)
            data_roads_filtered = data_roads_filtered.drop(data_roads_filtered.index[first_index+1:last_index+1])

    return data_roads_filtered