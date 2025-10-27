# -*- coding: utf-8 -*-
"""
Created on Sun Jun 12 14:57:51 2022

@author: OEM
"""
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 10:27:58 2022

@author: OEM
"""
import numpy as np
import os
import matplotlib.pyplot as plt
import rasterio.features as features
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
from collections import deque
import math

#%%

def array_to_polygons(raster_array, transform):
    # Set CRS (coordinate reference system)
    crs = "EPSG:2193"  # Example CRS, adjust as needed
    
    # Convert all values greater than 0 to 1
    raster_array[raster_array > 0] = 1

    # Ensure the array is of a supported dtype
    raster_array = raster_array.astype('int32')

    # Generate mask for values equal to 1
    mask = raster_array == 1

    # Extract shapes (polygons) from the raster data
    results = (
        {'properties': {'value': v}, 'geometry': s}
        for i, (s, v) in enumerate(
            shapes(raster_array, mask=mask, transform=transform)
        )
    )

    # Convert shapes to geometries
    geoms = list(results)

    # Create a GeoDataFrame from the shapes
    gdf = gpd.GeoDataFrame.from_features(geoms)

    # Set the CRS (coordinate reference system)
    gdf.crs = crs

    return gdf


#%%

def roughness_assignment(Roughness_Polygons):
    
    River = 2000
    Estuary_Lake = 2000
    Bare_Urban_Open = 200
    Low_Vegetation = 150
    Tall_Vegetation = 75
    Built = 40
        
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 0, 'Roughness_'] = Estuary_Lake               #Not_land (Outlined in the LCDB databased)
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 1, 'Roughness_'] = Built                 #Built-up_Area_(settlement)
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 2, 'Roughness_'] = Bare_Urban_Open	    #Urban_Parkland_and_Open_Space
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 5, 'Roughness_'] = Bare_Urban_Open	    #Transport_Infrastructure
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 6, 'Roughness_'] = Bare_Urban_Open    #Surface_Mine_or_Dump
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 10, 'Roughness_'] = Bare_Urban_Open	#Sand_or_Gravel
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 12, 'Roughness_'] = Bare_Urban_Open	#Landslide
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 14, 'Roughness_'] = Bare_Urban_Open	#Permanent_Snow_and_Ice
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 16, 'Roughness_'] = Bare_Urban_Open	#Gravel_or_Rock
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 15, 'Roughness_'] = Low_Vegetation	    #Alpine_Grass_and_Herbfield
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 20, 'Roughness_'] = Estuary_Lake	    #Lake_or_Pond
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 21, 'Roughness_'] = River	            #River
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 22, 'Roughness_'] = Estuary_Lake	    #Estuarine_Open_Water
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 23, 'Roughness_'] = 7500 	       #Harbours
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 30, 'Roughness_'] = Low_Vegetation	#Short-rotation_Cropland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 33, 'Roughness_'] = Low_Vegetation	#Orchards,_Vineyards_or_Other_Perennial_Crops
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 40, 'Roughness_'] = Low_Vegetation	#High_Producing_Exotic_Grassland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 41, 'Roughness_'] = Low_Vegetation	#Low_Producing_Grassland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 43, 'Roughness_'] = Low_Vegetation	#Tall_Tussock_Grassland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 44, 'Roughness_'] = Low_Vegetation	#Depleted_Grassland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 45, 'Roughness_'] = Low_Vegetation	#Herbaceous_Freshwater_Vegetation
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 46, 'Roughness_'] = Low_Vegetation	#Herbaceous_Saline_Vegetation
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 47, 'Roughness_'] = Low_Vegetation	#Flaxland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 50, 'Roughness_'] = Tall_Vegetation	#Fernland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 51, 'Roughness_'] = Tall_Vegetation	#Gorse_and_or_Broom
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 52, 'Roughness_'] = Tall_Vegetation	    #Manuka_and_or_Kanuka
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 54, 'Roughness_'] = Tall_Vegetation	    #Broadleaved_Indigenous_Hardwoods
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 55, 'Roughness_'] = Tall_Vegetation	#Sub_Alpine_Shrubland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 56, 'Roughness_'] = Tall_Vegetation	#Mixed_Exotic_Shrubland
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 58, 'Roughness_'] = Tall_Vegetation	#Matagouri_or_Grey_Scrub
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 80, 'Roughness_'] = Tall_Vegetation	#Peat_Shrubland_(Chatham_Is)
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 81, 'Roughness_'] = Tall_Vegetation	#Dune_Shrubland_(Chatham_Is)
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 70, 'Roughness_'] = Tall_Vegetation	#Mangrove
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 64, 'Roughness_'] = Tall_Vegetation	#Forest_-_Harvested
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 68, 'Roughness_'] = Tall_Vegetation	    #Deciduous_Hardwoods
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 69, 'Roughness_'] = Tall_Vegetation	    #Indigenous_Forest
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 71, 'Roughness_'] = Tall_Vegetation	    #Exotic_Forest
    Roughness_Polygons.loc[Roughness_Polygons['Class_2018'] == 200, 'Roughness_'] = Bare_Urban_Open	#Roads


    return Roughness_Polygons


#%%
def mask_of_polygon (src, train_df):

    rasterized = features.rasterize(train_df.geometry,
                                    out_shape = src.shape,
                                    fill = 0,
                                    out = None,
                                    transform = src.transform,
                                    all_touched = False,
                                    default_value = 1,
                                    dtype = None)
    
    return rasterized

#%%
def inundation_extent(qin, row, col):
          
    def floodFill(c, r, mask):
        
        """
        Crawls a mask array containing only 1 and 0 values from the
        starting point (c=column, r=row - a.k.a. x, y) and returns
        an array with all 1 values connected to the starting cell.
        This algorithm performs a 4-way check non-recursively.
        """
        # cells already filled
        filled = set()
        # cells to fill
        fill = set()
        fill.add((c, r))
        width = mask.shape[1]
        height = mask.shape[0]
        # Our output inundation array
        flood = np.zeros_like(mask, dtype=np.int16)
        # Loop through and modify the cells which need to be checked.
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0:
                # Don't fill
                continue
            if (mask[y][x] == 1):
                # Do fill
                flood[y][x] = 1
                filled.add((x, y))
                # Check neighbors for 1 values
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                if west not in filled:
                    fill.add(west)
                if east not in filled:
                    fill.add(east)
                if north not in filled:
                    fill.add(north)
                if south not in filled:
                    fill.add(south)
        return flood

    # set up water depth just for demo
    Water = qin.copy()

    rows = Water.shape[0]
    cols = Water.shape[1]
    # Set all edges to 0 as the floodfill doesnt work starting from an edge
    Water[0, :] = 0
    Water[(rows - 1), :] = 0
    Water[:, 0] = 0
    Water[:, (cols - 1)] = 0
    
    # Find all the coordinates of the remaining water cells
    Coords = np.nonzero(Water)
    x = Coords[0]
    y = Coords[1]
    
    # Use the coordinate of the middle water cell to perform the floodfill
    # x_0 = x[int(round(((x.shape[0])/2),0))]
    # y_0 = y[int(round(((x.shape[0])/2),0))]
    
    fld = floodFill(col, row, qin)
    
    return fld  

#%%
def Find_Shoreline(Fill): 
    
    # Initialize boolean array to False
    boolean_array = np.zeros_like(Fill)
    
    # Extract the contour line that represents the shoreline
    shoreline = None
    #plt.switch_backend('agg') 
    for path in plt.contour(Fill, levels= [0], colors='none').collections[0].get_paths():
        shoreline = path.vertices
                     
        # Set values inside shoreline contour to True
        for i in range (shoreline.shape[0]):
            x = int(shoreline[i,0])
            y = int(shoreline[i,1])
            boolean_array[y][x] = 1
    
    
    plt.close('all')
    return boolean_array

#%%

def TwoD_Crawl(ny, nx, Z, Htsunami, dx, dy, roughness, Flood, shoreline):
    
    def disregardBorders(A):
        A[:, 0] = 0
        A[:, -1] = 0
        A[0, :] = 0
        A[-1, :] = 0
        return A
    
    I = Flood.copy().astype(np.float32)
    
    ## Has changed? matrix - Disregard borders (visited)
    C = np.ones_like(I)
    C[Flood == Htsunami] = 0
    C = disregardBorders(C)
    
    ## Levels matrix - Advance line by line
    L = np.where(Flood > 0, 0, -1).astype(np.int32)
    
    # Get indices and levels as a deque for efficient pop from the left
    indices = deque([i.tolist() for i in np.argwhere(shoreline)])
    levels = deque([1 for _ in indices])
    
    neighbours = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    dl = np.sqrt(dx**2 + dy**2)  # Diagonal
    distances = [dl, dy, dl, dx, dx, dl, dy, dl]
    
    # Counter for updates
    update_count = 0
    
    while levels:
        # Coordinates and level
        i0, j0 = indices.popleft()
        curr_level = levels.popleft()
        
        # Update changed status to 0 (visited/unchanged)
        C[i0, j0] = 0
        
        # Propagate to neighbours if positive inundation only
        if I[i0, j0] > 0.05:
            for (di, dj), dist in zip(neighbours, distances):
                i1, j1 = i0 + di, j0 + dj
                if 0 <= i1 < ny and 0 <= j1 < nx:
                    # Update inundation
                    a = (roughness[i0, j0] + roughness[i1, j1]) / 2
                    S0 = (Z[i1, j1] - Z[i0, j0]) / dist
                    aux = I[i0, j0] - 2 / 3. * (S0 + I[i0, j0] / a) * dist
                    
                    # Update if higher level
                    if aux > math.ceil(I[i1, j1] * 1000) / 1000:
                        I[i1, j1] = aux
                        C[i1, j1] = 1
                        if L[i1, j1] < curr_level:
                            L[i1, j1] = curr_level + 1
                        levels.append(L[i1, j1])
                        indices.append([i1, j1])
                        
                        # Increment the update counter
                        update_count += 1
                        
        # Disregard borders
        C = disregardBorders(C)
        
    return I, update_count

