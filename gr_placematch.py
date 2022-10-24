import shapely
import osmnx  as ox
import numpy as np
import os.path
import gr_utils

def is_polygon(row):
    
    is_simplepoly = type(row['geometry']) is shapely.geometry.polygon.Polygon
    is_multipoly = type(row['geometry']) is shapely.geometry.multipolygon.MultiPolygon
    return is_simplepoly or is_multipoly

def get_bbox(data_roads_section, delta):

    # Select point subset & construct bbox
    lat_min = data_roads_section['x0'].min() - delta
    lat_max = data_roads_section['x0'].max() + delta
    lon_min = data_roads_section['y1'].min() - delta
    lon_max = data_roads_section['y1'].max() + delta
    return ox.utils_geo.bbox_to_poly(lat_max, lat_min, lon_max, lon_min) # polygon of bbox around subset

def get_places(bbox):
    
    # Downloading places information
    tags = {"landuse": ['commercial','construction','education','industrial',
                        'residential','retail','institutional','farmyard','cemetery',
                        'garages','railway','landfill','brownfield','quarry'],
            "admin_level": True
           }
    places = ox.geometries_from_polygon(bbox, tags)
    
    # Filtering places with landuse that have a polygon or multipolygon
    mask_landuse = places['landuse'].notna()
    places_landuse_raw = places[mask_landuse]
    mask_polygon = (places_landuse_raw.apply(is_polygon, axis=1))==True
    places_landuse = places_landuse_raw[mask_polygon] 

    # Filtering places with admin_level 8 or 9
    mask_admin8 = places['admin_level']=="8" # True if it has admin_level = 8
    mask_admin9 = places['admin_level']=="9" # True if it has admin_level = 9
    places_admin8 = places[mask_admin8]
    places_admin9 = places[mask_admin9]
       
    # Return places
    return places_landuse, places_admin8, places_admin9

def get_place_info(data_section, places_landuse, places_admin8, places_admin9):
    
    d_vec = []
    city8_vec = []
    city9_vec = []
    
    for i, segment in data_roads_section.iterrows():

        xmid = (segment['x0'] + segment['x1'])/2
        ymid = (segment['y0'] + segment['y1'])/2
        point = shapely.geometry.Point(ymid,xmid) # We work with the midpoint of the segment
        
        # Calculating distance to development
        d = 999.9;
        for j, place in places_landuse.iterrows():
            new_d = 1000*place['geometry'].distance(point) # Calculate distance midpoint - polygon
            d = min(d, new_d)
        d_vec.append(d)
   
        # Check if the segment midpoint lies in any admin level 8 regions
        city8 = ''
        for j, place in places_admin8.iterrows():
            if point.within(place['geometry']):
                city8 = place['name']
                break
        city8_vec.append(city8)

        # Check if the segment midpoint lies in any admin level 9 regions
        city9 = ''
        for j, place in places_admin9.iterrows():
            if point.within(place['geometry']):
                city9 = place['name']
                break
        city9_vec.append(city9)
    
    return d_vec, city8_vec, city9_vec

def add_places(data_roads, delta, n1, n2):

    # Collect place data from OSM
    bbox = get_bbox(data_roads.loc[n1:n2], delta) # Polygon of bounding box around section
    places_landuse, places_admin8, places_admin9 = get_places(bbox) # Grab relevant place information
    
    # Get development distance & city names
    d_vec, city8_vec, city9_vec = get_place_info(data_roads.loc[n1:n2], places_landuse, places_admin8, places_admin9)
    data_roads.loc[n1:n2,'dev_dist'] = d_vec
    data_roads.loc[n1:n2,'city8'] = city8_vec
    data_roads.loc[n1:n2,'city9'] = city9_vec
    
    return data_roads

def roads2places(trailname,data_roads,points_per_batch_places, delta_places):
    
    ## Matching GPX track to OSM places (uses _osm_place_download under the hood)
    n_roads = len(data_roads) # Number of segments in data_roads
    n_batch_places = int(np.ceil(n_roads/points_per_batch_places)) # Number of batches to be run
    
    data_roads['dev_dist'] = 0.0 # filling
    data_roads['city8'] = ''
    data_roads['city9'] = ''
    
    for b in range(n_batch_places): # Using batch counter b

        # Define the range of segments to process in the current batch
        n1 = b*points_per_batch_places # First point of this batch
        n2 = min(n1 + points_per_batch_places, n_roads) - 1 # Last point of this batch (clipped)

        # Check if this batch was processed before
        batch_out = f'cache/{trailname}_places_{n1}to{n2}.csv'
        print(f'Handling batch {b} of {n_batch_places-1} that covers road segments {n1} through {n2}...')
        
        if os.path.isfile(batch_out): # It already exists
            print('   This batch was processed before, skipping.')
        
        else: # It does not exist, so process it (use loc to avoid selection error)
            data_roads = add_places(data_roads, delta_places, n1, n2)
            gr_utils.write_batch_places(batch_out, data_roads.loc[n1:n2])
            print('   Finished this batch.')
            

# def get_development_distance(data_roads_section, places):
    
#     # Test matching
#     k = 0 # Counter
#     dvec = []
#     for i, segment in data_roads_section.iterrows():
#         dvec.append(999.9)
#         xmid = (segment['x0'] + segment['x1'])/2
#         ymid = (segment['y0'] + segment['y1'])/2
#         point = shapely.geometry.Point(ymid,xmid) # We work with the midpoint of the segment
#         for j, place in places.iterrows():
#             d = 1000*place['geometry'].distance(point) # Calculate distance midpoint - polygon
#             dvec[k] = min(d,dvec[k])
#         k += 1 # Increase counter
                
#     return dvec

# def get_city_names(data_section, places_admin8, places_admin9):
    
#     city8 = []
#     city9 = []
    
#     # Looping over segments
#     for idx, row in data_section.iterrows():

#         xmid = (row['x0'] + row['x1'])/2
#         ymid = (row['y0'] + row['y1'])/2
#         point = shapely.geometry.Point(ymid,xmid) # Segment midpoint
        
#         # Check if the segment midpoint lies in any admin level 8 regions
#         this_city8 = ''
#         for j, place in places_admin8.iterrows():
#             if point.within(place['geometry']):
#                 this_city8 = place['name']
#                 break
#         city8.append(this_city8)
                
#         # Check if the segment midpoint lies in any admin level 9 regions
#         this_city9 = ''
#         for j, place in places_admin9.iterrows():
#             if point.within(place['geometry']):
#                 this_city9 = place['name']
#                 break
#         city9.append(this_city9)
    
#     return city8, city9

# def add_place_info(data_roads, delta, n1, n2):

#     # Collect place data from OSM
#     bbox = get_bbox(data_roads.loc[n1:n2], delta) # Polygon of bounding box around section
#     places_landuse, places_admin8, places_admin9 = get_places(bbox) # Grab relevant place information
    
#     # Get development distance & city names
#     d_vec, city8_vec, city9_vec = get_place_info(data_roads.loc[n1:n2], places_landuse, places_admin8, places_admin9)
#     data_roads.loc[n1:n2,'dev_dist'] = d_vec
#     data_roads.loc[n1:n2,'city8'] = city8_vec
#     data_roads.loc[n1:n2,'city9'] = city9_vec
    
#     # Calculate distance to nearest developed area
# #     data_roads.loc[n1:n2,'dev_dist'] = get_development_distance(data_roads.loc[n1:n2], places_landuse)
    
#     # Grab city names
# #     city8, city9 = get_city_names(data_roads.loc[n1:n2], places_admin8, places_admin9)
# #     data_roads.loc[n1:n2,'city8'] = city8
# #     data_roads.loc[n1:n2,'city9'] = city9
    
#     return data_roads
        