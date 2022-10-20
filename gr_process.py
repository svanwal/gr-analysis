import numpy as np

def get_development_type(data,tol_d):
    
    data['development'] = 1
    mask_undev = (data['dev_dist']>tol_d)
    data.loc[mask_undev,'development'] = 0  # 0 is undeveloped, 1 is developed
    
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
        if row['first_tracktype'] in tracktype_p0:
            this_paved = 0
        elif row['first_tracktype'] in tracktype_p1:
            this_paved = 1
        elif row['first_tracktype'] in tracktype_p2:
            this_paved = 2
        else:
            if row['first_surface'] in surface_p0:
                this_paved = 0
            elif row['first_surface'] in surface_p1:
                this_paved = 1
            elif row['first_surface'] in ['none']:
                this_paved = 2
            else:
                if row['first_highway'] in highway_p1:
                    this_paved = 1
                else:
                    this_paved = 2
        
        data.loc[idx,'paved'] = this_paved
        
    return data

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
    
    return data