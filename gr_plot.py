import folium
import numpy as np
from IPython.display import IFrame
import branca.colormap as cm

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
#     mid = np.round(data_places.shape[0]/2)
#     focus = [data_places.iloc[mid,'x0'],data_places.iloc[mid,'y0']]
    chart = folium.Map(location=[49.69983, 5.3074], zoom_start=10, tiles="OpenStreetMap") # Focus on Ieper

    colors = (data_places['dev_dist']<tol_d).values.tolist()
    colors[colors==True] = 1
    colors[colors==False] = 0
    
    x = data_places['x0'].values.tolist()
    y = data_places['y0'].values.tolist()
    x.extend(data_places.tail(1)['x1'])
    y.extend(data_places.tail(1)['y1'])
    xy0 = list(zip(x,y))
    xy = [[coord[0],coord[1]] for coord in xy0]
    colormap = cm.LinearColormap(colors=['green','red'],vmin=0.25,vmax=0.75,index=[0.25,0.75])
    
    newline = folium.ColorLine(positions=xy, colors=colors, colormap=colormap, weight=3)
    newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_development.html"
    chart.save(filepath)
    return filepath