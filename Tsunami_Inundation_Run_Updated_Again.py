# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 09:21:50 2024

@author: OEM
"""

def Perform_Entire_Inundation(folder_path, Region, Area, Original_Area, Htsunami_Heights, folder, Roughness_Polygons):
    import numpy as np
    from datetime import datetime
    import geopandas as gpd
    import pandas as pd
    import rasterio as rio
    from shapely.geometry import box, Point
    import os
    import rasterio as rio
    from Functions import array_to_polygons, mask_of_polygon, inundation_extent, Find_Shoreline, TwoD_Crawl
    import gc
    
    #%%
    '''
    LOAD THE DEM, RESAMPLE AND DETERMINE THE BOUNDS
    '''
    DEM = rio.open(f"C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/DEM/Latest_North_Island_Merged_LiDAR_and_FABDEM.tif")  
    bounds = DEM.bounds
    polygon = gpd.GeoDataFrame({"id": 1, "geometry": [box(*bounds)]}, crs="EPSG:2193")
    
    #%%
    '''
    FIND THE LOCATION OF THE DEM AND THEN FIND THE NEAREST PORT LOCATION
    '''
    
    # Define the region of interest (polygon centroid)
    Centre_Interest_Region = Point(float(polygon.centroid.x), float(polygon.centroid.y))
    
    # Load the secondary port data
    Secondary_Port_Data = gpd.read_file("C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/Ports.gpkg")
    
    # Calculate the distance from each port to the region of interest
    Secondary_Port_Data['Distance'] = Secondary_Port_Data.geometry.apply(lambda port_location: Centre_Interest_Region.distance(port_location))
    
    # Find the 10 closest ports
    closest_ports = Secondary_Port_Data.nsmallest(5, 'Distance')
    
    print(closest_ports)
    
    # Review the closest ports and decide if they want to modify
    selection = input("Review the closest ports. If you want to change the selection, enter the row indices (e.g., 0,1,3) or press Enter to keep all: ")
    
    # Check if the user provided specific indices
    if selection:
        # Convert the input string into a list of integers for iloc
        indices = [int(i) for i in selection.split(',')]
        # Apply the selection to closest_ports
        closest_ports = closest_ports.iloc[indices]

    # Create the new column "Standard_P_minus_Chart_Datu"
    closest_ports['Standard_P_minus_Chart_Datu'] = closest_ports['Standard_P'] - closest_ports['Chart_Datu']
    
    # Calculate the weights based on the distance
    closest_ports['Weight'] = 1 / closest_ports['Distance']
    
    # Calculate the weighted height difference between the standard port elevation and chart datum
    weighted_Chart_Datum = (closest_ports['Standard_P_minus_Chart_Datu'] * closest_ports['Weight']).sum() / closest_ports['Weight'].sum()

    # Calculate the weighted mean high water springs (MHWS) above chart datum
    weighted_MHWS_above_Chart_Datum = (closest_ports['MHWS'] * closest_ports['Weight']).sum() / closest_ports['Weight'].sum()

    Elevation_Data = DEM.read(1)
    Elevation_Data[Elevation_Data == -9999] = np.NAN
    Elevation_Data = Elevation_Data - (weighted_Chart_Datum + weighted_MHWS_above_Chart_Datum)
    Zeroed_Elevation = np.nan_to_num(Elevation_Data)
    Zeroed_Elevation[Zeroed_Elevation <= 0] = 0
    
    del Secondary_Port_Data, Elevation_Data, closest_ports, weighted_Chart_Datum
    gc.collect()
    
    #%%
    '''
    CROP THE INUNDATION EXTENT TO RIVERS AND ESTUARIES AND FILL UNTIL THESE POINTS OR MHWS
    '''
    print("Creating Roughness Matrix")
    River_Present = Estuary_Present = Mangrove_Present = Herbaceous_Saline_Vegetation_Present = Harbour_Present = 0
    
    print("Clipping Roughness Data")
    Roughness_Polygons = gpd.read_file(f"C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/updated-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-with-roads-latest-roughness.shp")
    Local_Roughness_Data = gpd.clip(Roughness_Polygons, polygon)
    Local_Roughness_Data = Local_Roughness_Data[Local_Roughness_Data.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    Local_Roughness_Data.to_file(f"C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/updated-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-with-roads-latest-roughness.shp")
    print("Deleting Nationwide Roughness Data")
    
    Local_Land_Cover_Codes = Local_Roughness_Data['Class_2018'].unique().astype('int32')
    Local_Land_Cover_Names = Local_Roughness_Data['Name_2018'].unique()
    
    
    Roughness_Matrix = np.zeros((len(Local_Land_Cover_Codes), DEM.meta['height'], DEM.meta['width']), dtype='int32')
    
    
    print("Creating Masks of Roughness Data")
    for i in range(0, len(Local_Land_Cover_Codes), 1):
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
        if Class_Code == 23:
            Harbour_Present = 1
            Harbour_polygons = Local_Class_Data
        if Class_Code == 70:
            Mangrove_Present = 1
            Mangrove_polygons = Local_Class_Data
        if Class_Code == 46:
            Herbaceous_Saline_Vegetation_Present = 1
            Herbaceous_Saline_Vegetation_polygons = Local_Class_Data
            
    print("Generating Complete Array")
    a = np.max(Roughness_Matrix, axis=0).astype(np.int32)
    del Roughness_Matrix, Local_Roughness_Data, mask_local_polygons
    a[a == 0] = 5000
    
    gc.collect()
    
    #%%
    '''
    CROP THE INUNDATION EXTENT TO RIVERS AND ESTUARIES AND FILL UNTIL THESE POINTS TO THE MHWS
    '''
    print("Defining Initial Water Level")
    Water_Points_gdf = gpd.read_file("C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/TsunamiZones2021/Shapefiles2021/Water_Points.shp")
    Water_Point = Water_Points_gdf[Water_Points_gdf['SECTN_NAME'] == Original_Area]
    point = Water_Point.geometry.iloc[0]
    transform = DEM.transform
    inverse_transform = ~transform
    x, y = point.x, point.y
    col, row = inverse_transform * (x, y)
    row = int(row)
    col = int(col)    
    
    local_buffed_river_mask = local_buffed_estuary_mask = local_buffed_mangrove_mask = local_buff_Herbaceous_Saline_Vegetation_mask = local_buff_Harbour_mask = np.zeros_like(a)

    Initial_Water_Level = np.zeros([Zeroed_Elevation.shape[0], Zeroed_Elevation.shape[1]])
    Initial_Water_Level[Zeroed_Elevation <= 0] = 1
    Initial_Water_Level = Initial_Water_Level.astype(int)
    Wet_areas = inundation_extent(Initial_Water_Level, row, col)
    a[Wet_areas > 0] = 2000
    
# 河口（Class 22）
if Estuary_Present == 1 and "Estuary_polygons" in locals():
    try:
        buff_estuary = Estuary_polygons.buffer(10)
        # 可选释放：del Estuary_polygons
        if len(buff_estuary) > 0:
            buff_estuary = pd.DataFrame({'geometry': list(buff_estuary.values)})
            local_buffed_estuary_mask = mask_of_polygon(DEM, buff_estuary).astype(np.uint8)
            # 与原逻辑一致：这些区域从 Initial_Water_Level 中去除
            Initial_Water_Level[local_buffed_estuary_mask == 1] = 0
        del buff_estuary
    except Exception as e:
        print("Estuary buffer/mask failed:", e)

# 河流（Class 21）
if River_Present == 1 and "River_polygons" in locals():
    try:
        buff_rivers = River_polygons.buffer(10)
        # 可选释放：del River_polygons
        if len(buff_rivers) > 0:
            buff_rivers = pd.DataFrame({'geometry': list(buff_rivers.values)})
            local_buffed_river_mask = mask_of_polygon(DEM, buff_rivers).astype(np.uint8)
            Initial_Water_Level[local_buffed_river_mask == 1] = 0
        del buff_rivers
    except Exception as e:
        print("River buffer/mask failed:", e)

# 红树林（Class 70）
if Mangrove_Present == 1 and "Mangrove_polygons" in locals():
    try:
        buff_mangrove = Mangrove_polygons.buffer(10)
        # 可选释放：del Mangrove_polygons
        if len(buff_mangrove) > 0:
            buff_mangrove = pd.DataFrame({'geometry': list(buff_mangrove.values)})
            local_buffed_mangrove_mask = mask_of_polygon(DEM, buff_mangrove).astype(np.uint8)
            Initial_Water_Level[local_buffed_mangrove_mask == 1] = 0
        del buff_mangrove
    except Exception as e:
        print("Mangrove buffer/mask failed:", e)

# 盐生草本（Class 46）
if Herbaceous_Saline_Vegetation_Present == 1 and "Herbaceous_Saline_Vegetation_polygons" in locals():
    try:
        buff_hsv = Herbaceous_Saline_Vegetation_polygons.buffer(10)
        # 可选释放：del Herbaceous_Saline_Vegetation_polygons
        if len(buff_hsv) > 0:
            buff_hsv = pd.DataFrame({'geometry': list(buff_hsv.values)})
            local_buff_Herbaceous_Saline_Vegetation_mask = mask_of_polygon(DEM, buff_hsv).astype(np.uint8)
            Initial_Water_Level[local_buff_Herbaceous_Saline_Vegetation_mask == 1] = 0
        del buff_hsv
    except Exception as e:
        print("Herbaceous Saline Vegetation buffer/mask failed:", e)

# 港湾（Class 23）
if Harbour_Present == 1 and "Harbour_polygons" in locals():
    try:
        buff_harbour = Harbour_polygons.buffer(10)
        # 可选释放：del Harbour_polygons
        if len(buff_harbour) > 0:
            buff_harbour = pd.DataFrame({'geometry': list(buff_harbour.values)})
            local_buff_Harbour_mask = mask_of_polygon(DEM, buff_harbour).astype(np.uint8)
            Initial_Water_Level[local_buff_Harbour_mask == 1] = 0
        del buff_harbour
    except Exception as e:
        print("Harbour buffer/mask failed:", e)

# 若某些 mask 之前没定义（对应类别不存在），确保为 0 数组，避免后续 Water_Fill 报错
if 'local_buffed_river_mask' not in locals():
    local_buffed_river_mask = np.zeros_like(a, dtype=np.uint8)
if 'local_buffed_estuary_mask' not in locals():
    local_buffed_estuary_mask = np.zeros_like(a, dtype=np.uint8)
if 'local_buffed_mangrove_mask' not in locals():
    local_buffed_mangrove_mask = np.zeros_like(a, dtype=np.uint8)
if 'local_buff_Herbaceous_Saline_Vegetation_mask' not in locals():
    local_buff_Herbaceous_Saline_Vegetation_mask = np.zeros_like(a, dtype=np.uint8)
if 'local_buff_Harbour_mask' not in locals():
    local_buff_Harbour_mask = np.zeros_like(a, dtype=np.uint8)
    
    Initial_Water_Level = Initial_Water_Level.astype(int)
    Initial_Water_Level = inundation_extent(Initial_Water_Level, row, col)
    a[Initial_Water_Level > 0] = 5000
    a[local_buff_Harbour_mask > 0] = 5000
    Fill_to_the_MHWS = Initial_Water_Level.astype(int)  
    

import rasterio as rio
from rasterio.windows import Window

def write_big_geotiff(path, array, transform, crs=2193, dtype="uint8", block_size=1024):
    """安全写出大栅格，支持分块和BIGTIFF"""
    with rio.open(
        path, "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
        BIGTIFF="YES",   # 支持 >4GB 文件
        compress="lzw"   # 可选压缩，节省磁盘
    ) as dst:
        for row_start in range(0, array.shape[0], block_size):
            row_end = min(row_start + block_size, array.shape[0])
            window = Window(
                col_off=0, row_off=row_start,
                width=array.shape[1],
                height=row_end - row_start
            )
            dst.write(array[row_start:row_end, :], 1, window=window)



    with rio.open(f"{folder}/{Region}/{Area}/Initial_Water_Level.tif", 'w',
                  driver='GTiff', height=Initial_Water_Level.shape[0], width=Initial_Water_Level.shape[1],
                  count=1, dtype=Initial_Water_Level.dtype, crs=2193, transform=DEM.transform) as Tide_Raster:
        Tide_Raster.write(Initial_Water_Level, 1)
    
    print("Creating Raster")
    with rio.open(f"{folder}/{Region}/{Area}/Roughness_Raster.tif", 'w',
                  driver='GTiff', height=a.shape[0], width=a.shape[1],
                  count=1, dtype=a.dtype, crs=2193, transform=DEM.transform) as Roughness_Raster:
        Roughness_Raster.write(a, 1)
    
    Water_Fill = local_buffed_river_mask + local_buffed_estuary_mask + Fill_to_the_MHWS
    with rio.open(f"{folder}/{Region}/{Area}/Water_Fill.tif", 'w',
                  driver='GTiff', height=Water_Fill.shape[0], width=Water_Fill.shape[1],
                  count=1, dtype=Water_Fill.dtype, crs=2193, transform=DEM.transform) as Tide_Raster:
        Tide_Raster.write(Water_Fill, 1)
        
    del Tide_Raster, Initial_Water_Level, Water_Fill, local_buffed_river_mask, local_buffed_estuary_mask, local_buffed_mangrove_mask, local_buff_Herbaceous_Saline_Vegetation_mask, local_buff_Harbour_mask
    
    gc.collect()
    
    #%%
    '''
    SHORELINE
    '''
    Fill_to_the_MHWS = Fill_to_the_MHWS.astype(np.float16)
    Fill = (Fill_to_the_MHWS * - 1) + 1
    Fill[Fill < 0] = 0
    Shoreline_Boolean = Find_Shoreline(Fill)
    
    with rio.open(f"{folder}/{Region}/{Area}/Shoreline_Raster.tif", 'w',
                  driver='GTiff', height=Shoreline_Boolean.shape[0], width=Shoreline_Boolean.shape[1],
                  count=1, dtype='int32', crs=2193, transform=DEM.transform) as Shoreline_Raster:
        Shoreline_Raster.write(Shoreline_Boolean, 1)
    
    del Fill, Shoreline_Raster
    gc.collect()
    
        
    # Pause execution and check port outputs
    input("Review the shoreline. Press Enter to continue, or stop the execution to make changes.")
    
    #%%
    '''
    Crawl
    ''' 
    print('starting_inundation')
    
    # Define Local_Data_DataFrame as an empty DataFrame with the necessary columns
    Local_Data_DataFrame = pd.DataFrame(columns=['Return_Period', 'Percentile', 'Htsunami', 'Run_Time', 'Code_Iterations', 'Inundated_Area'])
    
    # Iterate through the DataFrame and extract 'Index' and 'Htsunami' values
    for idx, row in Htsunami_Heights.iterrows():
        Htsunami = row['Htsunami']
        
        # Extract the return period and percentile from the index
        return_period = idx[1:idx.find('y')]
        percentile = idx[idx.find('y') + 1:idx.find('p')]
            
        Fill_to_MHWS = Fill_to_the_MHWS.copy()
        Fill_to_MHWS[Fill_to_MHWS == 1] = Htsunami        
        I = Fill_to_MHWS.copy().astype(np.float32)
        Shoreline_Values = Shoreline_Boolean.copy().astype(np.float32)
        Shoreline_Values[Shoreline_Values == 1] = Htsunami       
        
        start = datetime.now()                
        I, update_count = TwoD_Crawl(Zeroed_Elevation.shape[0], Zeroed_Elevation.shape[1], Zeroed_Elevation, Htsunami, 10, 10, a, Fill_to_MHWS, Shoreline_Boolean)
        end = datetime.now() - start
        
        I[Fill_to_MHWS > 0] = 0
        
        print(end)
        
        I = I + Fill_to_MHWS
        
        # Generate an array of the global water depth as I + Elevation
        Water_Depth = I.copy()
        Water_Depth = Water_Depth - Fill_to_MHWS
        Water_Depth = Water_Depth + Shoreline_Values
        
        Inundated_Area = Water_Depth.copy()
        Inundated_Area[Inundated_Area > 0] = 1
        Inundated_Area = Inundated_Area.sum() * 10 * 10
        
        Water_Depth[Water_Depth == 0] = np.nan
        
        # Create A raster of the Global Water Level numpy array
        with rio.open(f'{folder}/{Region}/{Area}/{Area}_H{return_period}y{percentile}p_{Htsunami}m_10mResolution.tif',
                                      'w', driver='GTiff', height = Water_Depth.shape[0], width = Water_Depth.shape[1],
                                      count = 1, dtype = 'float32', crs = 2193, transform = DEM.transform) as Inundation_Raster:
            Inundation_Raster.write(Water_Depth,1)
        
        #polygon_of_inundation = array_to_polygons(Water_Depth, transform)
        #os.makedirs(f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{Region}/{Area}", exist_ok=True)
        #polygon_of_inundation.to_file(f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{Region}/{Area}/Entire_Inundation_Polygon_{Area}_H{return_period}y{percentile}p_{Htsunami}m.shp")
        
        Local_Data_DataFrame = Local_Data_DataFrame.append({'Return_Period': return_period, 'Percentile': percentile, 'Htsunami': Htsunami, 'Run_Time': end, 'Code_Iterations':update_count, 'Inundated_Area': Inundated_Area}, ignore_index=True)
        
        del Inundation_Raster, Water_Depth, I, Shoreline_Values, Fill_to_MHWS
    
        Local_Data_DataFrame.to_csv(f'{folder}/{Region}/{Area}/{Area}_Data.csv')    
    
    return 
