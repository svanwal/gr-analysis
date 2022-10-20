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

def get_landuse_places(bbox):
    
    tags = {"landuse": ['commercial','construction','education','industrial',
               'residential','retail','institutional','farmyard','cemetery',
                        'garages','railway','landfill','brownfield','quarry']}
    landuse_places = ox.geometries_from_polygon(bbox, tags)
    landuse_places['is_polygon'] = landuse_places.apply(is_polygon, axis=1)
    mask_polygon = landuse_places['is_polygon']==True
    return landuse_places[mask_polygon] # Return polygons with a landuse tag

def get_development_status(data_roads_section, places):
    
    # Test matching
    k = 0 # Counter
    developed = []
    for i, segment in data_roads_section.iterrows():
        developed.append(999.9)
        xmid = (segment['x0'] + segment['x1'])/2
        ymid = (segment['y0'] + segment['y1'])/2
        point = shapely.geometry.Point(ymid,xmid) # We work with the midpoint of the segment
        for j, place in places.iterrows():
            d = 1000*place['geometry'].distance(point) # Calculate distance midpoint - polygon
            developed[k] = min(d,developed[k])
        k += 1 # Increase counter
                
    return developed

def match_batch(data_roads_section, delta):

    bbox = get_bbox(data_roads_section, delta) # Polygon of bounding box around section
    places = get_landuse_places(bbox) # Download polygons with landuse tags that indicate heavy development
    near_development = get_development_status(data_roads_section, places)
    return near_development
    
    return data_places

def roads2places(trailname,data_roads,points_per_batch_places, delta_places):
    
    ## Matching GPX track to OSM places (uses _osm_place_download under the hood)
    n_roads = len(data_roads) # Number of segments in data_roads
    n_batch_places = int(np.ceil(n_roads/points_per_batch_places)) # Number of batches to be run
    data_roads['dev_dist'] = 0.0 # filling
    
    for b in range(n_batch_places): # Using batch counter b

        # Define the range of segments to process in the current batch
        n1 = b*points_per_batch_places # First point of this batch
        n2 = min(n1 + points_per_batch_places, n_roads) - 1 # Last point of this batch (clipped)

        # Check if this batch was processed before
        batch_out = f'cache/{trailname}_places_{n1}to{n2}.csv'
        print(f'Handling {b} of {n_batch_places-1} that covers road segments {n1} through {n2}...')
        if os.path.isfile(batch_out): # It already exists
            print('   This batch was processed before, skipping.')
        else: # It does not exist, so process it (use loc to avoid selection error)
            data_roads.loc[n1:n2,'dev_dist'] = match_batch(data_roads.loc[n1:n2], delta_places)
            gr_utils.write_batch_places(batch_out, data_roads.loc[n1:n2])
            print('   Finished this batch.')