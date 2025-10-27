# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 15:51:26 2024

@author: OEM
"""

import geopandas as gpd
import os
import pandas as pd

# Define the directory containing the shapefiles
shapefiles_directory = 'D:/Nationwide_Tsunami_Inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/Nationwide_Land_Covers/'  # Replace with the path to your directory
output_shapefile_path = 'D:/Nationwide_Tsunami_Inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/Nationwide_Land_Covers/Merged_Nationwide_Land_Covers.shp'  # Replace with the desired output path

# Initialize an empty list to hold GeoDataFrames
gdf_list = []

# Iterate through the files in the directory
for filename in os.listdir(shapefiles_directory):
    if filename.endswith('.shp'):
        filepath = os.path.join(shapefiles_directory, filename)
        # Read each shapefile into a GeoDataFrame
        gdf = gpd.read_file(filepath)
        # Append the GeoDataFrame to the list
        gdf_list.append(gdf)

# Concatenate all GeoDataFrames in the list into a single GeoDataFrame
merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))

# Optional: Ensure all geometries are valid
merged_gdf = merged_gdf[merged_gdf.is_valid]

# Save the merged GeoDataFrame to a new shapefile
merged_gdf.to_file(output_shapefile_path)

print(f"Merged shapefile saved to {output_shapefile_path}")
