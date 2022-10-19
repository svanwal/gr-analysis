import folium
import numpy as np
from IPython.display import IFrame

def get_coords_from_frame(data_roads):
    
    x = data_roads['x0'].values.tolist()
    y = data_roads['y0'].values.tolist()
    x.extend(data_roads.tail(1)['x1'])
    y.extend(data_roads.tail(1)['y1'])
    xy0 = list(zip(x,y))
    return [[coord[0],coord[1]] for coord in xy0]

def compare_tracks(trail_coords,data_roads):
    
    # Map setup
    mid = int(len(trail_coords)/2)
    chart = folium.Map(location=trail_coords[mid], zoom_start=12, tiles="OpenStreetMap") 
    
    # Draw GPX track
    newline = folium.PolyLine(locations=trail_coords, weight=3, color='red')
    newline.add_to(chart)
    
    # Draw map matched frame
    xy = get_coords_from_frame(data_roads)
    newline = folium.PolyLine(locations=xy, weight=2, color='black')
    newline.add_to(chart)
    
    # Render the map
    filepath = "cache/chart_tracks.html"
    chart.save(filepath)
    
    return filepath

def show_repeats(trail_coords,data_roads,repeat_coords):
    
    # Map setup
    mid = int(len(trail_coords)/2)
    chart = folium.Map(location=trail_coords[mid], zoom_start=12, tiles="OpenStreetMap") 
    
    # Draw GPX track
    newline = folium.PolyLine(locations=trail_coords, weight=3, color='red')
    newline.add_to(chart)
    
    # Draw map matched frame
    xy = get_coords_from_frame(data_roads)
    newline = folium.PolyLine(locations=xy, weight=2, color='black')
    newline.add_to(chart)
    
    # Draw repeat points
    for point in repeat_coords:
        newmarker = folium.CircleMarker(location=point,radius=3,color='blue')
        newmarker.add_to(chart)
    
    # Render the map
    filepath = "cache/chart_repeat.html"
    chart.save(filepath)
    
    return filepath

# Show the development status of data frame
def show_development(data_places,tol_d):
    
    # Map setup
    mid = np.round(data_places.shape[0]/2)
    focus = [data_places.iloc[mid,'x0'],data_places.iloc[mid,'y0']]
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")

    # Draw midpoints according to development status
    for idx, row in data_places.iterrows():
        x0 = row['x0']
        x1 = row['x1']
        y0 = row['y0']
        y1 = row['y1']
        xmid = (x0 + x1)/2
        ymid = (y0 + y1)/2
        midpoint = [xmid,ymid]
        if data_places.iloc[idx,'dev_dist']<tol_d:
            newmarker = folium.CircleMarker(location=midpoint,radius=2,color='red')
        else:
            newmarker = folium.CircleMarker(location=midpoint,radius=2,color='green')
        newmarker.add_to(chart)