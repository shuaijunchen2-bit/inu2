# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 16:40:38 2023

@author: OEM
"""

import os
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
from Tsunami_Inundation_Run_Updated import Perform_Entire_Inundation

# Path to the DEM raster file
dem_raster_path = 'D:/Nationwide_Tsunami_Inundation/DEM_Data/South_Island_Merged_LiDAR.tif'
# Path to the polygon bounding boxes
shapefile_path = 'D:/Nationwide_Tsunami_Inundation/DEM_Data/DEM_Region_Extents/Section_Runs/South_Island_LiDAR_Bounding_Boxes.shp'

folder = "D:/Nationwide_Tsunami_Inundation/Inundation_Results"
# Open the shapefile with the attribute table
gdf = gpd.read_file(shapefile_path)

Roughness_Polygons = gpd.read_file('D:/Nationwide_Tsunami_Inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/updated-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-with-roads-latest-roughness.shp')

# Open the DEM raster once before the loop
with rasterio.open(dem_raster_path) as src:
    # Iterate through each row in the DataFrame
    for index, row in gdf.iterrows():
        # Get the geometry for the current row
        geometry = row.geometry

        Original_Area = row['SECTN_NAME']
        Area = row['SECTN_NAME']
        Area = Area.replace(" ", "_")
        Area = Area.replace("/", "_")
        Area = Area.replace(" / ", "_")

        # Extract 'Region' from the row
        Region = row['REGC2023_1']
        Region = Region.replace(" ", "_")

        # Split the Region string by comma and get both parts
        region_parts = Region.split(',')
        if len(region_parts) > 1:
            first_part = region_parts[0].strip()  # Part before the comma
            second_part = region_parts[1].strip()  # Part after the comma
        else:
            first_part = Region.strip()  # If there is no comma, use the whole string
            second_part = None

        os.makedirs(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}", exist_ok=True)

        # Create a folder based on "Northland_" followed by the 'id' name within the output directory
        folder_path = f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}"

        segments_completed = os.listdir(f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}")

        if f"{Area}" in segments_completed:
            continue

        os.makedirs(folder_path, exist_ok=True)

        # Define the output filename based on the index
        output_path = f"D:/Nationwide_Tsunami_Inundation/Inundation_Results/{Region}/{Area}/{Area}_DEM.tif"

        # Clip the DEM using the geometry
        clipped_dem, clipped_transform = mask(src, [geometry], crop=True)

        # Update the metadata for the clipped DEM
        clipped_profile = src.profile
        clipped_profile.update(
            width=clipped_dem.shape[2],
            height=clipped_dem.shape[1],
            transform=clipped_transform,
        )

        # Save the clipped DEM to the output directory
        with rasterio.open(output_path, 'w', **clipped_profile) as DEM:
            DEM.write(clipped_dem)

        # Explicitly delete variables to free up memory
        del clipped_dem, clipped_transform, clipped_profile

        # Tsunami Height Extrapolated
        Htsunami_Heights = pd.DataFrame(data={'Htsunami': [round(row['H100y50p'], 2),
                                                           round(row['H100y84p'], 2),
                                                           round(row['H250y50p'], 2),
                                                           round(row['H250y84p'], 2),
                                                           round(row['H500y50p'], 2),
                                                           round(row['H500y84p'], 2),
                                                           round(row['H1000y50p'], 2),
                                                           round(row['H1000y84p'], 2),
                                                           round(row['H1500y50p'], 2),
                                                           round(row['H1500y84p'], 2),
                                                           round(row['H2000y50p'], 2),
                                                           round(row['H2000y84p'], 2),
                                                           round(row['H2500y50p'], 2),
                                                           round(row['H2500y84p'], 2)]},
                                                           index=['H100y50p', 'H100y84p', 'H250y50p', 'H250y84p',
                                                                  'H500y50p', 'H500y84p', 'H1000y50p', 'H1000y84p',
                                                                  'H1500y50p', 'H1500y84p', 'H2000y50p', 'H2000y84p',
                                                                  'H2500y50p', 'H2500y84p'])

        print(f"Clipped DEM saved to {output_path}")

        Local_Data_DataFrame = Perform_Entire_Inundation(folder_path, Region, Area, Original_Area, Htsunami_Heights, folder, Roughness_Polygons)

        # Clean up after processing each segment
        del Local_Data_DataFrame, Htsunami_Heights

        # Force garbage collection
        import gc
        gc.collect()
