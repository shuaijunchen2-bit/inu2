# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 09:21:50 2024

@author: OEM
"""

def Perform_Entire_Inundation(folder_path, Region, Area, Original_Area, Htsunami_Heights, folder, Roughness_Polygons):
    import numpy as np
    import geopandas as gpd
    import time
    import pandas as pd
    import rasterio as rio
    from shapely.geometry import box, Point
    from datetime import datetime
    import os
    from Functions import array_to_polygons, mask_of_polygon, inundation_extent, Find_Shoreline, TwoD_Crawl
    
    #%%
    '''
    LOAD THE DEM, RESAMPLE AND DETERMINE THE BOUNDS
    '''
    
    DEM = rio.open(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/{Area}_DEM.tif")  
    bounds = DEM.bounds
    polygon = gpd.GeoDataFrame({"id": 1, "geometry": [box(*bounds)]}, crs="EPSG:2193")
    
    #%%
    '''
    FIND THE LOCATION OF THE DEM AND THEN FIND THE NEAREST PORT LOCATION
    '''
    # Find the Location of the centre of the region of interest
    Centre_Interest_Region = Point(float(polygon.centroid.x), float(polygon.centroid.y))
    # Import the Secondary Port Data from GeoPackage
    Secondary_Port_Data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Ports.gpkg")
    # Measure Distances between Secondary Ports and the region of interest
    Secondary_Port_Data['Distance'] = Secondary_Port_Data.geometry.apply(lambda port_location: Centre_Interest_Region.distance(port_location))
    # Select the 10 closest ports
    closest_ports = Secondary_Port_Data.nsmallest(10, 'Distance')
    # Calculate weights based on inverse distances (closer ports have higher weights)
    closest_ports['Weight'] = 1 / closest_ports['Distance']
    # Calculate weighted average of MHWS based on distances
    weighted_MHWS_above_Chart_Datum = (closest_ports['MHWS'] * closest_ports['Weight']).sum() / closest_ports['Weight'].sum()
    
    # Identify the Standard Port with the shortest distance to the centroid of the region of interest and obtain the tidal data    
    Closest_Standard_Port = Secondary_Port_Data.iloc[int(Secondary_Port_Data['Distance'].idxmin())]
    Closest_Port_Name, Elevation_of_Survey_point_NZVD, Chart_Datum_Below_Survey_Point = Closest_Standard_Port[1], Closest_Standard_Port[15], Closest_Standard_Port[14]
    
    weighted_Chart_Datum_Below_Survey_Point = (closest_ports['Chart_Datu'] * closest_ports['Weight']).sum() / closest_ports['Weight'].sum()
    
    # Apply the tidal data to the whole elevation array in the region of interest (not good for large regions of interest)
    Elevation_Data = DEM.read(1)
    Elevation_Data[Elevation_Data == -9999] = np.NAN
    Elevation_Data = Elevation_Data - (Elevation_of_Survey_point_NZVD - weighted_Chart_Datum_Below_Survey_Point)
    Elevation_Data = Elevation_Data - weighted_MHWS_above_Chart_Datum
    # Create elevation array of the DEM data
    Zeroed_Elevation = np.nan_to_num(Elevation_Data)
    # Zero the elevation data up for anything that is below zero, 0 elevation up until the MHWS    
    Zeroed_Elevation[Zeroed_Elevation <= 0] = 0
    
    # Clean up to free memory
    del Secondary_Port_Data, Elevation_Data
    
    #%%
    '''
    CROP THE INUNDATION EXTENT TO RIVERS AND ESTUARIES AND FILL UNTIL THESE POINTS OR MHWS
    '''
    print("Creating Roughness Matrix")
    River_Present = 0
    Estuary_Present = 0
    Mangrove_Present = 0
    Herbaceous_Saline_Vegetation_Present = 0
    
    print("Clipping Roughness Data")
    Local_Roughness_Data = gpd.clip(Roughness_Polygons, polygon)
    Local_Roughness_Data = Local_Roughness_Data[Local_Roughness_Data.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    Local_Roughness_Data.to_file(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/{Area}_Roughness_Clip.shp")
    print("Deleting Nationwide Roughness Data")
    
    Local_Land_Cover_Codes = Local_Roughness_Data['Class_2018'].unique().astype('int32')
    Local_Land_Cover_Names = Local_Roughness_Data['Name_2018'].unique()
    Roughness_Matrix = np.zeros((len(Local_Land_Cover_Codes), DEM.meta['height'], DEM.meta['width']), dtype='int32')
    print("Creating Masks of Roughness Data")
    for i in range(0, len(Local_Land_Cover_Codes), 1):
        print("New Mask")
        Class_Code = int(Local_Land_Cover_Codes[i])
        Local_Class_Data = Local_Roughness_Data.loc[Local_Roughness_Data['Class_2018'] == Class_Code]
        mask_local_polygons = np.int32(mask_of_polygon(DEM, Local_Class_Data))
        mask_local_polygons[mask_local_polygons == 1] = Local_Class_Data['Roughness_'].iloc[0]
        Roughness_Matrix[i, :, :] = mask_local_polygons
        
        if Class_Code == 21:
            River_Present = 1
            River_polygons = Local_Class_Data
        if Class_Code == 22:
            Estuary_Present = 1
            Estuary_polygons = Local_Class_Data  
        if Class_Code == 70:
            Mangrove_Present = 1
            Mangrove_polygons = Local_Class_Data
        if Class_Code == 46:
            Herbaceous_Saline_Vegetation_Present = 1
            Herbaceous_Saline_Vegetation_polygons = Local_Class_Data
            
    print("Generating Complete Array")
    a = np.max(Roughness_Matrix, axis=0).astype(np.int32)
    # Clean up to free memory
    del Roughness_Matrix, Local_Roughness_Data, mask_local_polygons
    a[a == 0] = 7500
    
    #%%
    '''
    CROP THE INUNDATION EXTENT TO RIVERS AND ESTUARIES AND FILL UNTIL THESE POINTS TO THE MHWS
    '''
    print("Defining Initial Water Level")
    # Set the location of water as a point and then call that to determine the row and column for the inundation_extent water find
    Water_Points_gdf = gpd.read_file("D:/Nationwide_Tsunami_Inundation/TsunamiZones2021/Shapefiles2021/Water_Points.shp")
    Water_Point = Water_Points_gdf[Water_Points_gdf['SECTN_NAME'] == Original_Area]
    point = Water_Point.geometry.iloc[0]
    transform = DEM.transform
    inverse_transform = ~transform
    # Step 4: Determine the row and column that the point corresponds to
    x, y = point.x, point.y
    row, col = inverse_transform * (x, y)
    # Convert to integer indices
    row = int(row)
    col = int(col)    
    
    local_buffed_river_mask = np.zeros_like(a)
    local_buffed_estuary_mask = np.zeros_like(a)
    
    Initial_Water_Level = np.zeros([Zeroed_Elevation.shape[0], Zeroed_Elevation.shape[1]])
    Initial_Water_Level[Zeroed_Elevation <= 0] = 1
    Initial_Water_Level = Initial_Water_Level.astype(int)
    Wet_areas = inundation_extent(Initial_Water_Level, row, col)
    a[Wet_areas > 0] = 7500
    
    if Estuary_Present == 1:
        buff_estuary = Estuary_polygons.buffer(10)
        buff_estuary = pd.DataFrame(buff_estuary)
        if not buff_estuary.empty:
            buff_estuary = buff_estuary.rename(columns={0: 'geometry'})
            local_buffed_estuary_mask = mask_of_polygon(DEM, buff_estuary)
            Initial_Water_Level[local_buffed_estuary_mask == 1] = 0
    
    if River_Present == 1:
        buff_rivers = River_polygons.buffer(10)
        buff_rivers = pd.DataFrame(buff_rivers)
        if not buff_rivers.empty:
            buff_rivers = buff_rivers.rename(columns={0: 'geometry'})
            local_buffed_river_mask = mask_of_polygon(DEM, buff_rivers)
            Initial_Water_Level[local_buffed_river_mask == 1] = 0
            
    if Mangrove_Present == 1:
        buff_mangrove = Mangrove_polygons.buffer(10)
        buff_mangrove = pd.DataFrame(buff_mangrove)
        if not buff_mangrove.empty:
            buff_mangrove = buff_mangrove.rename(columns={0: 'geometry'})
            local_buffed_mangrove_mask = mask_of_polygon(DEM, buff_mangrove)
            Initial_Water_Level[local_buffed_mangrove_mask == 1] = 0
    
    if Herbaceous_Saline_Vegetation_Present == 1:
        buff_Herbaceous_Saline_Vegetation = Herbaceous_Saline_Vegetation_polygons.buffer(10)
        buff_Herbaceous_Saline_Vegetation = pd.DataFrame(buff_Herbaceous_Saline_Vegetation)
        if not buff_Herbaceous_Saline_Vegetation.empty:
            buff_Herbaceous_Saline_Vegetation = buff_Herbaceous_Saline_Vegetation.rename(columns={0: 'geometry'})
            local_buff_Herbaceous_Saline_Vegetation_mask = mask_of_polygon(DEM, buff_Herbaceous_Saline_Vegetation)
            Initial_Water_Level[local_buff_Herbaceous_Saline_Vegetation_mask == 1] = 0
    
    Initial_Water_Level = Initial_Water_Level.astype(int)
    Initial_Water_Level = inundation_extent(Initial_Water_Level, row, col)
    a[Initial_Water_Level > 0] = 7500
    Fill_to_the_MHWS = Initial_Water_Level.astype(int)  
    
    with rio.open(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/Initial_Water_Level.tif", 'w',
                  driver='GTiff', height=Initial_Water_Level.shape[0], width=Initial_Water_Level.shape[1],
                  count=1, dtype=Initial_Water_Level.dtype, crs=2193, transform=DEM.transform) as Tide_Raster:
        Tide_Raster.write(Initial_Water_Level, 1)
    
    print("Creating Raster")
    with rio.open(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/Roughness_Raster.tif", 'w',
                  driver='GTiff', height=a.shape[0], width=a.shape[1],
                  count=1, dtype=a.dtype, crs=2193, transform=DEM.transform) as Roughness_Raster:
        Roughness_Raster.write(a, 1)
    
    Water_Fill = local_buffed_river_mask + local_buffed_estuary_mask + Fill_to_the_MHWS
    with rio.open(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/Water_Fill.tif", 'w',
                  driver='GTiff', height=Water_Fill.shape[0], width=Water_Fill.shape[1],
                  count=1, dtype=Water_Fill.dtype, crs=2193, transform=DEM.transform) as Tide_Raster:
        Tide_Raster.write(Water_Fill, 1)
        
    # Clean up to free memory
    del Tide_Raster, local_buffed_river_mask, local_buffed_estuary_mask, Initial_Water_Level, Water_Fill
    
    #%%
    '''
    SHORELINE
    '''
    Fill_to_the_MHWS = Fill_to_the_MHWS.astype(np.float16)
    # Set 1 as the land and 0 as the water
    Fill = (Fill_to_the_MHWS * - 1) + 1
    Fill[Fill < 0] = 0
    Shoreline_Boolean = Find_Shoreline(Fill)
    
    with rio.open(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/Shoreline_Raster.tif", 'w',
                  driver='GTiff', height=Shoreline_Boolean.shape[0], width=Shoreline_Boolean.shape[1],
                  count=1, dtype='int32', crs=2193, transform=DEM.transform) as Shoreline_Raster:
        Shoreline_Raster.write(Shoreline_Boolean, 1)
    
    # Clean up to free memory
    del Fill, Shoreline_Raster
    
    #%%
    # '''
    # Crawl
    # ''' 
    # print('starting_inundation')
    
    # # Define Local_Data_DataFrame as an empty DataFrame with the necessary columns
    # Local_Data_DataFrame = pd.DataFrame(columns=['Return_Period', 'Percentile', 'Htsunami', 'Run_Time', 'Inundated_Area'])
    
    # # Iterate through the DataFrame and extract 'Index' and 'Htsunami' values
    # for idx, row in Htsunami_Heights.iterrows():
    #     Htsunami = row['Htsunami']
        
    #     # Extract the return period and percentile from the index
    #     return_period = idx[1:idx.find('y')]
    #     percentile = idx[idx.find('y') + 1:idx.find('p')]
            
    #     Fill_to_MHWS = Fill_to_the_MHWS.copy()
    #     Fill_to_MHWS[Fill_to_MHWS == 1] = Htsunami        
    #     I = Fill_to_MHWS.copy().astype(np.float32)
    #     Shoreline_Values = Shoreline_Boolean.copy().astype(np.float32)
    #     Shoreline_Values[Shoreline_Values == 1] = Htsunami       
        
    #     start = datetime.now()                
    #     I = TwoD_Crawl(Zeroed_Elevation.shape[0], Zeroed_Elevation.shape[1], Zeroed_Elevation, Htsunami, 10, 10, a, Fill_to_MHWS, Shoreline_Boolean)
    #     end = datetime.now() - start
        
    #     I[Fill_to_MHWS > 0] = 0
        
    #     print(end)
        
    #     I = I + Fill_to_MHWS
        
    #     # Generate an array of the global water depth as I + Elevation
    #     Water_Depth = I.copy()
    #     Water_Depth = Water_Depth - Fill_to_MHWS
    #     Water_Depth = Water_Depth + Shoreline_Values
        
    #     Inundated_Area = Water_Depth.copy()
    #     Inundated_Area[Inundated_Area > 0] = 1
    #     Inundated_Area = Inundated_Area.sum() * 10 * 10
        
    #     Water_Depth[Water_Depth == 0] = np.nan
        
    #     # Create A raster of the Global Water Level numpy array
    #     with rio.open(f'D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/{Area}_H{return_period}y{percentile}p_{Htsunami}m_10mResolution.tif',
    #                                   'w', driver='GTiff', height = Water_Depth.shape[0], width = Water_Depth.shape[1],
    #                                   count = 1, dtype = 'float32', crs = 2193, transform = DEM.transform) as Inundation_Raster:
    #         Inundation_Raster.write(Water_Depth,1)

    #     del Inundation_Raster
        
    #     polygon_of_inundation = array_to_polygons(Water_Depth, transform)
    #     os.makedirs(f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{Region}/{Area}", exist_ok=True)
    #     polygon_of_inundation.to_file(f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{Region}/{Area}/Entire_Inundation_Polygon_{Area}_H{return_period}y{percentile}p_{Htsunami}m.shp")
        
    #     Local_Data_DataFrame = Local_Data_DataFrame.append({'Return_Period': return_period, 'Percentile': percentile, 'Htsunami': Htsunami, 'Run_Time': end, 'Inundated_Area': Inundated_Area}, ignore_index=True)
        
    # return Local_Data_DataFrame
