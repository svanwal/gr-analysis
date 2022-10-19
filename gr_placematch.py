import shapely
import osmnx  as ox

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
