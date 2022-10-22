import folium
import numpy as np
from IPython.display import IFrame
import branca.colormap as cm
import gr_mapmatch

def get_fullcoords_from_frame(data):
    
    x = data['x0'].values.tolist()
    y = data['y0'].values.tolist()
    x.extend(data.tail(1)['x1'])
    y.extend(data.tail(1)['y1'])
    xy = list(zip(x,y))
    return [[coord[0],coord[1]] for coord in xy]

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
def show_development(data_places,focus):
    
    # Prepare data to be plotted
    colors = data_places['development'].values.tolist()
    x = data_places['x0'].values.tolist()
    y = data_places['y0'].values.tolist()
    x.extend(data_places.tail(1)['x1'])
    y.extend(data_places.tail(1)['y1'])
    xy0 = list(zip(x,y))
    xy = [[coord[0],coord[1]] for coord in xy0]
    
    # Colormap setup
    colormap = cm.LinearColormap(colors=['#21ce2c','red'],vmin=0.25,vmax=0.75,index=[0.25,0.75])
    
    # Map setup
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")

    # Draw development type
    newline = folium.ColorLine(positions=xy, colors=colors, colormap=colormap, weight=3, popup=colors)
    newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_development.html"
    chart.save(filepath)
    return filepath

def show_traffic(data_places,focus):
    
    # Prepare data to be plotted
    colors = data_places['traffic'].values.tolist()
    x = data_places['x0'].values.tolist()
    y = data_places['y0'].values.tolist()
    x.extend(data_places.tail(1)['x1'])
    y.extend(data_places.tail(1)['y1'])
    xy0 = list(zip(x,y))
    xy = [[coord[0],coord[1]] for coord in xy0]
    
    # Colormap setup
    colormap = cm.LinearColormap(colors=['#21ce2c','black','red'],vmin=0,vmax=2,index=[0,1,2])
    
    # Map setup
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")

    # Draw development type
    newline = folium.ColorLine(positions=xy, colors=colors, colormap=colormap, weight=3, popup=colors)
    newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_traffic.html"
    chart.save(filepath)
    return filepath

def show_paved(data_places,focus):
    
    # Prepare data to be plotted
    colors = data_places['paved'].values.tolist()
    x = data_places['x0'].values.tolist()
    y = data_places['y0'].values.tolist()
    x.extend(data_places.tail(1)['x1'])
    y.extend(data_places.tail(1)['y1'])
    xy0 = list(zip(x,y))
    xy = [[coord[0],coord[1]] for coord in xy0]
    
    # Colormap setup
    colormap = cm.LinearColormap(colors=['#21ce2c','#21ce2c','black'],vmin=0,vmax=2,index=[0,1,2])
    
    # Map setup
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")

    # Draw development type
    newline = folium.ColorLine(positions=xy, colors=colors, colormap=colormap, weight=3, popup=colors)
    newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_paved.html"
    chart.save(filepath)
    return filepath

def show_paved_detail(data,focus):

    # Map setup
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")
    
    # Draw path
    coords = get_fullcoords_from_frame(data)
    for i in range(len(coords)-1):
        # Determine color based on paved status
        if data.loc[i,'paved']==0:
            c = '#21ce2c'
        elif data.loc[i,'paved']==1:
            c = '#21ce2c'
        else:
            c = 'black'
        # Determine label based on highway/surface/tracktype
        label = f"{i}: {data.loc[i,'highway']} / {data.loc[i,'surface']} / {data.loc[i,'tracktype']}"
        newline = folium.PolyLine(locations=coords[i:i+2], weight=3, color=c, popup=label)
        newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_detail.html"
    chart.save(filepath)
    return filepath

def get_focus(trail):
    
    trail_coords  = gr_mapmatch.trail_to_coords(trail)
    mid = int(np.round(len(trail_coords)/2))
    return trail_coords[mid]

def show_type_detail(data,focus):

    # Map setup
    chart = folium.Map(location=focus, zoom_start=10, tiles="OpenStreetMap")
    
    # Draw path
    coords = get_fullcoords_from_frame(data)
    for i in range(len(coords)-1):
        # Determine color based on paved status
        if data.loc[i,'gr_type']==1:
            c = 'green'
        elif data.loc[i,'gr_type']==2:
            c = '#53e0fc' # lightblue
        elif data.loc[i,'gr_type']==3:
            c = 'red'
        elif data.loc[i,'gr_type']==4:
            c = 'blue'
        elif data.loc[i,'gr_type']==5:
            c = 'magenta'
        else: # type 6
            c = 'yellow'

        # Determine label based on highway/surface/tracktype
        label = f"Type {data.loc[i,'gr_type']} with hwy:{data.loc[i,'highway']} // srf:{data.loc[i,'surface']} // trk:{data.loc[i,'tracktype']} // trf:{data.loc[i,'traffic']} // dev:{data.loc[i,'development']}"
#         label = f"Segment {i} // highway:{data.loc[i,'highway']} // surface:{data.loc[i,'surface']} // tracktype:{data.loc[i,'tracktype']} // traffic:{data.loc[i,'traffic']} // development:{data.loc[i,'development']}"
#         label = f"{i}: {data.loc[i,'highway']} / {data.loc[i,'surface']} / {data.loc[i,'tracktype']}"
        newline = folium.PolyLine(locations=coords[i:i+2], weight=3, color=c, popup=label)
        newline.add_to(chart)
        
    # Render the map
    filepath = "cache/chart_detail.html"
    chart.save(filepath)
    return filepath