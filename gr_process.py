import numpy as np
import pandas as pd

def get_development_type(data,tol_d):
    
    data['development'] = 1
    mask_undev = (data['dev_dist']>tol_d)
    data.loc[mask_undev,'development'] = 0  # 0 is undeveloped, 1 is developed
    
    return data

def get_development_groups(data):
    
    devgroups = pd.DataFrame()
    k = 0 # group counter
    n = data.shape[0] # nrows in data
    j0 = 0
    j1 = j0

    while j1<n-1:

        dev0 = data.loc[j0]['development']
        j1 = j0 + 1
        dev1 = data.loc[j1]['development']

        # increment j1 until we find a different development type
        while dev1==dev0:
            if j1 == n-1: # we have reached the end of the data dataframe
                break
            j1 += 1
            dev1 = data.loc[j1]['development']
            
        # calculate distance of covered by this group
        d = 0
        for j in range(j0,j1+1):
            row = data.loc[j]
            d += row['d1'] - row['d0']
            
        # add to devgroups list
        newrow = pd.DataFrame({'dev':dev0, 'j0':j0, 'j1':j1-1, 'd':d},index={k})
        devgroups = pd.concat([devgroups,newrow])
        k += 1

        # move to the next devgroup by setting j0 = j1
        j0 = j1
    
    return devgroups

def smooth_development_type(data, tol_d):
    
    # First calculate cumulative distances
    data = calculate_cumulative_distances(data)
    
    # Group the data into pieces with the same development status
    groups = get_development_groups(data)
    
    return data
    
    
    
def get_traffic_type(data,types_slow,types_heavy):
    
    data['traffic'] = 1 # normal roads
    mask_slow = data['highway'].isin(types_slow)
    mask_heavy = data['highway'].isin(types_heavy)
    data.loc[mask_slow,'traffic'] = 0 # slow roads
    data.loc[mask_heavy,'traffic'] = 2 # heavy roads
    
    return data

def grab_first(x):
    
    if x is not None:
        bb = x.strip('][')
        cc = bb.split(',')
        dd = [element.strip().strip("'") for element in cc]
        return dd[0]
    
    return x

def get_paved_type(data,tracktype_p0,tracktype_p1,tracktype_p2,surface_p0,surface_p1,highway_p1):
    
    # Replacing nans
    data['highway'] = data['highway'].replace({np.nan:"none"})
    data['surface'] = data['surface'].replace({np.nan:"none"})
    data['tracktype'] = data['tracktype'].replace({np.nan:"none"})
    
    # Grabbing first one
    data['first_highway'] = data['highway'].apply(grab_first)
    data['first_surface'] = data['surface'].apply(grab_first)
    data['first_tracktype'] = data['tracktype'].apply(grab_first)
    
    # Establishing status
    data['paved'] = -1
    this_paved = -1
    for idx, row in data.iterrows():
        if row['first_tracktype'] in tracktype_p0: # Unpaved tracktype
            this_paved = 0
        elif row['first_tracktype'] in tracktype_p1: # Semi-paved tracktype
            this_paved = 1
        elif row['first_tracktype'] in tracktype_p2: # Paved tracktype
            this_paved = 2
        else: # Empty tracktype
            if row['first_surface'] in surface_p0: # Unpaved surface type
                this_paved = 0
            elif row['first_surface'] in surface_p1: # Semi-paved surface type
                this_paved = 1
            elif row['first_surface'] in ['none']: # Empty surface type
                if row['first_highway'] in highway_p1: # Semi-paved highway type
                    this_paved = 1
                else: # Paved highway type
                    this_paved = 2
            else: # Paved surface type
                this_paved = 2
        
        data.loc[idx,'paved'] = this_paved
        
    return data

def row2type(row):
    
    types_light = [[1,1,4],[1,1,6],[3,3,3]]
    types_heavy = [[2,2,4],[2,2,5],[3,3,3]]
    
    if row['development']==0: # light
        gr_type = types_light[row['traffic']][row['paved']]
    else: # heavy
        gr_type = types_heavy[row['traffic']][row['paved']]
    
    return gr_type

def get_gr_type(data):
    
    data['gr_type'] = data.apply(row2type, axis=1)
    return data

def get_city_name(row):
    
    if row['city8'] == 'none':
        return row['city9']
    return row['city8']

def places2processed(data,
                     tol_d,
                     types_slow,types_heavy,
                     tracktype_p0,tracktype_p1,tracktype_p2,surface_p0,surface_p1,highway_p1):
    
    # Establish paved status
    data = get_paved_type(data,tracktype_p0,tracktype_p1,tracktype_p2,surface_p0,surface_p1,highway_p1)
    
    # Establish traffic status
    data = get_traffic_type(data,types_slow,types_heavy)
    
    # Establish development status
    data = get_development_type(data,tol_d)
    
    # Smooth development status
#     data['development_smooth'] = smooth_development_type(data,250.0)
    
    # Establish GR route type
    data = get_gr_type(data)
    
    # Select city name from city8 & city9
    data['city'] = data.apply(get_city_name,axis=1)
    
    return data

def calculate_cumulative_distances(data):
    
    data['d_cum'] = data['d_cart'].cumsum()
    data['d0'] = data['d_cum'].shift(1)
    data.loc[0,'d0'] = 0
    data['d1'] = data['d_cum']
    return data