import osmnx  as ox
import pandas as pd
import numpy  as np
from itertools import groupby
import gr_utils # Contains useful geometry functions
from csv import writer
import warnings
import os.path
import gr_mapmatch # Contains functions that perform the map matching of roads

##############################
## --- Helper functions --- ##
##############################

def vector_difference(u,v):
    
    r = [u[0] - v[0],
         u[1] - v[1]]
    return r

def vector_dot(u,v):
    
    return u[0]*v[0] + u[1]*v[1]

def vector_distance(u,v):
    
    r = vector_difference(u,v)
    return np.sqrt(r[0]*r[0] + r[1]*r[1])

def mynorm(r):
    
    return np.sqrt(r[0]*r[0] + r[1]*r[1] + r[2]*r[2])

def get_p2seg_distance(P,P0,P1):
    
    v = vector_difference(P1,P0)
    w = vector_difference(P,P0)
    
    c1 = vector_dot(w,v)
    if c1<=0:
        return vector_distance(P,P0)
    
    c2 = vector_dot(v,v)
    if c2<=c1:
        return vector_distance(P,P1)
    
    b = c1/c2
    Pb = [P0[0] + b*v[0],
          P0[1] + b*v[1]]
    
    return vector_distance(P,Pb)

def sph2cart(lat, lon):
    
    R = 6371.8 # Mean Earth radius [km]
    return [R*np.cos(lat)*np.cos(lon), R*np.cos(lat)*np.sin(lon), R*np.sin(lat)]

def get_coords_from_route(gpx):
    
    xy = []
    for point in gpx: # adding one point for each entry
        xy.append([point[0],point[1]])
    point = gpx[-1]
    xy.append([point[2],point[3]]) # adding the last point
    return xy

def cartesian_distance(lat0,lon0,lat1,lon1):
    
    R = 6371.8 # Mean earth radius [km]
    r1 = sph2cart(np.radians(lat0), np.radians(lon0))
    r2 = sph2cart(np.radians(lat1), np.radians(lon1))
    dr = [r1[0] - r2[0], r1[1] - r2[1], r1[2] - r2[2]]
    return 1000.0*mynorm(dr) # in meters

def print_overwrite(text):
    
    print(text, end='\r', flush=True)

def get_path_error(route,trail_coords):
    
    xy = get_coords_from_route(route)
    err = 0
    for point in trail_coords: # for each point from the gpx
        dmin = 999
        for j in range(len(xy)-1): # find the min distance to the pathfind
            dmin = min(dmin,get_p2seg_distance(point,xy[j],xy[j+1]))
        err += dmin*dmin # save the squared error
        
    return err

# def gpx2points(gpx):
    
#     x = gpx['point_x'].values.tolist()
#     y = gpx['point_y'].values.tolist()
#     points = list(zip(x,y))
#     return [[point[1],point[0]] for point in points]

def edge_to_coords(network_edges,edge_id):
    
    lon = list(network_edges.loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[0])
    lat = list(network_edges.loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[1])
    edge_coords = list(zip(lon,lat))
    return [[coord[1],coord[0]] for coord in edge_coords]

def point2rectangle(rect, P):
    Px = P[1]
    Py = P[0]
    dx = max(rect['xmin'] - Px, 0, Px - rect['xmax'])
    dy = max(rect['ymin'] - Py, 0, Py - rect['ymax'])
    print(dx)
    print(dy)
    return np.sqrt(dx*dx + dy*dy)

def get_point_to_bbox_distance(point_x,point_y,bbox):

    d0 = get_p2seg_distance([point_y,point_x],bbox[0],bbox[1])
    d1 = get_p2seg_distance([point_y,point_x],bbox[1],bbox[2])
    d2 = get_p2seg_distance([point_y,point_x],bbox[2],bbox[3])
    d3 = get_p2seg_distance([point_y,point_x],bbox[3],bbox[0])
    return min(d0,d1,d2,d3)

def get_bbox(lat_min, lat_max, lon_min, lon_max):
    
    return [[lat_min,lon_min],[lat_min,lon_max],[lat_max,lon_max],[lat_max,lon_min],[lat_min,lon_min]]


#####################################
## --- Road matching functions --- ##
#####################################

# Converts gpx points to nodes dataframe
def gpx_to_nodes(gpx, gpx_coords, points_per_batch, delta_roads, min_dist_from_bbox):

    n_trail = len(gpx) # Number of GPX points in the trail
    n_batch = int(np.ceil(gpx.shape[0]/points_per_batch)) # Number of batches to be run
    nodes = pd.DataFrame() # ID of node matched to each GPX point

    ## --- Loop over all sections of the trail
    for b in range(n_batch): # Using batch counter b

        # Define the range of GPX points to process in the current batch
        n1 = b*points_per_batch # First point of this batch
        n2 = min(n1 + points_per_batch, n_trail) # Last point of this batch (clipped)

        print_overwrite(f"\rHandling batch #{b}/{n_batch-1} spanning GPX points {n1} through {n2-1}")

        gpx_section = gpx.loc[n1:n2] # Select that range of GPX points
        section_coords = gpx_coords[n1:n2] # Convert the points into a list of [lat, lon] pairs

        lat_min, lat_max, lon_min, lon_max = gr_mapmatch.get_bbox(gpx_section,delta_roads) # Calculate the bounding box
        network = gr_mapmatch.get_osm_network(lat_min, lat_max, lon_min, lon_max) # Download the street network from OSM
        new_nodes = gr_mapmatch.match_nodes_vec(network,section_coords) # Calculate corresponding node for each GPX point
        bbox = get_bbox(lat_min, lat_max, lon_min, lon_max) 

        delta_lat = lat_max - lat_min
        delta_lon = lon_max - lon_min
        
        # Calculate distance between each GPX point and its corresponding node, in this batch
        dvec = []
        for j in range(len(section_coords)):
            point_id = n1 + j
            point_y = section_coords[j][0]
            point_x = section_coords[j][1]
            node_id = new_nodes[j]
            node = network['points'].loc[node_id]
            node_x = node['x']
            node_y = node['y']
            # Distance from GPX point to node
            d2node = gr_mapmatch.get_dist(section_coords[j],[node_y,node_x]) # distance from gpx point to matching node
            # Distance from node to bbox
            d2bbox = get_point_to_bbox_distance(node_x,node_y,bbox)
            # Storing
            newrow = pd.DataFrame({'point_x':point_x, 'point_y':point_y,
                                   'node_id':node_id,
                                   'node_x':node_x, 'node_y':node_y,
                                   'd2node':d2node, 'd2bbox':d2bbox},index={point_id})
            nodes = pd.concat([nodes,newrow])
            
        # If we find any matched nodes that are close to the bounding box, recalculate with a bigger network!
        for idx, row in nodes.iterrows():
        
            if row['d2bbox']<min_dist_from_bbox:

                print(f'Point {idx} should be recalculated!')
                found = False

                # Now we need a while loop that checks a larger network around this point
                k = 0 # Counter for how many times we increased the bbox
                new_lat_min = row['point_y'] - delta_lat/2
                new_lat_max = row['point_y'] + delta_lat/2
                new_lon_min = row['point_x'] - delta_lon/2
                new_lon_max = row['point_x'] + delta_lon/2

                while not found:
                    
                    print(f'Recalculating with larger bbox, k = {k}')
                    
                    # Updating the bounding box using counter k
                    temp_lat_min = new_lat_min - k*delta_roads
                    temp_lat_max = new_lat_max + k*delta_roads
                    temp_lon_min = new_lon_min - k*delta_roads
                    temp_lon_max = new_lon_max + k*delta_roads
                    
                    new_bbox = get_bbox(temp_lat_min, temp_lat_max, temp_lon_min, temp_lon_max) 
                    
                    # New node matching
                    new_network = gr_mapmatch.get_osm_network(temp_lat_min, temp_lat_max, temp_lon_min, temp_lon_max)
                    nearest_edges = ox.distance.nearest_edges(new_network['graph'],row['point_x'],row['point_y'])
                    nearest_edge_end = gr_mapmatch.get_nearest_edge_end(
                        new_network,nearest_edges,[row['point_x'],row['point_y']]) # make sure the point coords are in nthe right order here!!!!!
                    node_id = nearest_edge_end
                    node = new_network['points'].loc[node_id]
                    node_x = node['x']
                    node_y = node['y']
                    d2bbox = get_point_to_bbox_distance(node_x,node_y,new_bbox)
                    print(f'new distance is {d2bbox} but ')
                    if d2bbox>min_dist_from_bbox:
                        d2node = gr_mapmatch.get_dist([row['point_y'],row['point_x']],
                                                      [node_y,node_x]) # distance from gpx point to matching node
                        nodes.loc[idx,'node_id'] = node_id
                        nodes.loc[idx,'node_x'] = node_x
                        nodes.loc[idx,'node_y'] = node_y
                        nodes.loc[idx,'d2node'] = d2node
                        nodes.loc[idx,'d2bbox'] = d2bbox
                        break
                    else:
                        k += 1 # retry with a larger bbox

    return nodes

# Converts nodes dataframe to pieces dataframe
def nodes_to_pieces(nodes):
    
    pieces = pd.DataFrame()
    k = 0 # piece counter
    n = nodes.shape[0] # nrows in node_list
    j0 = 0
    j1 = j0
    j2 = j0

    while j2<n-1:

        node0 = nodes.loc[j0]['node_id']
        j1 = j0 + 1
        node1 = nodes.loc[j1]['node_id']

        # increment j1 until we find a different node
        while node1==node0:
            j1 += 1
            node1 = nodes.loc[j1]['node_id']

        # increment j2 until we find another node
        j2 = j1
        node2 = nodes.loc[j2]['node_id']
        while node2==node1:
            if j2 == n-1: # we have reached the end of the gpx dataframe
                break
            j2 += 1
            node2 = nodes.loc[j2]['node_id']

        if j2 == n-1:
            j3 = j2
        else:
            # find the gpx point between j1 and j2 that is nearest to node1
            temp = nodes.loc[j1:j2-1]
            j3 = temp['d2node'].idxmin()

        # pathfinding is to take place between j0 and j3, add to pieces list
        newrow = pd.DataFrame({'node0':node0, 'node1':node1, 'gpx0':j0, 'gpx1':j3},index={k}).astype(int)
        pieces = pd.concat([pieces,newrow])
        k += 1

        # move to the next piece by setting j0 = j3
        j0 = j3
    
    return pieces

def get_single_edge_coords(network, edge_id):
    
    lon = list(network['edges'].loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[0])
    lat = list(network['edges'].loc[(edge_id[0],edge_id[1])]['geometry'][0].coords.xy[1])
    return [[coord[1],coord[0]] for coord in list(zip(lon,lat))]

# Extract the coordinates of the edge connecting node_id_start and node_id_end
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

    return segment_list

# Converts pieces dataframe into segments dataframe by performing pathfinding for each piece
def pieces_to_segments(trail,nodes,points_per_batch,delta_roads,pieces,npaths):

    n_trail = len(trail) # Number of GPX points in the trail
    n1 = 0 # First point of this batch
    n2 = min(n1 + points_per_batch, n_trail) # Last point of this batch (clipped)
    lat_min, lat_max, lon_min, lon_max = gr_mapmatch.get_bbox(trail.loc[n1:n2],delta_roads) # Calculate the bounding box
    network = gr_mapmatch.get_osm_network(lat_min, lat_max, lon_min, lon_max) # Download the street network from OSM

    total_route = []
#     total_route = pd.DataFrame()

    for idx, row in pieces.iterrows():

        print_overwrite(f"\rHandling piece {idx} of {pieces.shape[0]}, spanning GPX points {row['gpx0']} through {row['gpx1']}")

        # --- Grab GPX points to be used in error calculation
        nodes_select = nodes.loc[row['gpx0']:row['gpx1']] 
        x = nodes_select['point_x'].values.tolist()
        y = nodes_select['point_y'].values.tolist()
        temp = list(zip(x,y))
        points = [[item[1],item[0]] for item in temp]

        # --- Check if we need to download the next network
        if row['gpx0']>n2:
            n1 += points_per_batch
            n2 += points_per_batch
#             print('')
            lat_min, lat_max, lon_min, lon_max = gr_mapmatch.get_bbox(trail.loc[n1:n2],delta_roads) # Calculate the bounding box
            network = gr_mapmatch.get_osm_network(lat_min, lat_max, lon_min, lon_max) # Download the street network from OSM

        # --- Calculate paths
        found = False
        ntry = 1
        while not found: # in case the node is not in the network, reload it with bigger delta
            try:
                route = ox.k_shortest_paths(network['graph'], row['node0'], row['node1'], npaths)
                paths = []
                for path in route:
                    paths.append(path)
            except:
#                 print('')
                print('   Node not found in network, downloading larger network...')
#                 print(f"nodes are {row['node0']} and {row['node1']}")
#                 print(f'first has coords {} {}')
#                 print(f'bbox used was {lat_min} {lat_max} {lon_min} {lon_max}')
                lat_min, lat_max, lon_min, lon_max = gr_mapmatch.get_bbox(trail.loc[n1:n2],ntry*delta_roads) # Calculate the bounding box
                network = gr_mapmatch.get_osm_network(lat_min, lat_max, lon_min, lon_max) # Download the street network from OSM
                ntry += 1
            else:
                found = True

        # --- Choose the best path

        # Get segment coordinates for each path
        routes = []
        for path in paths:
            segment_list = []
            for j in range(len(path)-1):
                segment_list.extend(get_segments(network, path[j], path[j+1]))
            routes.append(segment_list)

        # Get the error for each path
        err = []
        d = []
        for route in routes:
            err.append(get_path_error(route,points))
            d_osm = 0
            for segment in route:
                d_osm += segment[5] # add d_osm column
            d.append(d_osm)
        dmin = min(d)
        weights = []
        if row['gpx1'] - row['gpx0'] < 4:
            for j in range(len(err)): # Weight factor takes into account error and length
                weights.append(d[j])
        else:
            for j in range(len(err)): # Weight factor takes into account error and length
                weights.append(err[j]*np.exp(d[j]/dmin))

        # Choose the best route
        imin = weights.index(min(weights))
        best_route = routes[imin]
        total_route.extend(best_route)

    return pd.DataFrame(total_route,columns=['x0','y0','x1','y1','d_cart','d_osm','highway','surface','tracktype'])