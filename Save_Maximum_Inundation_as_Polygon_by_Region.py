# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 20:06:19 2024

@author: OEM
"""

import os
import glob
import rasterio
from rasterio import features
import geopandas as gpd
import shapely
from shapely.geometry import shape
import numpy as np

def mask_to_polygons_layer(mask, transform):
    all_polygons = []
    for shape, value in features.shapes(mask.astype(np.int16), mask=(mask > 0), transform=transform):
        all_polygons.append(shapely.geometry.shape(shape))

    all_polygons = shapely.geometry.MultiPolygon(all_polygons)
    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)
        if all_polygons.type == 'Polygon':
            all_polygons = shapely.geometry.MultiPolygon([all_polygons])
    return all_polygons

Region = "Northland"

# Define the source and destination directories
source_dir = rf"D:\Nationwide_Tsunami_Inundation\Inundation_Results\{Region}_Region"
destination_dir = rf"D:\Nationwide_Tsunami_Inundation\Maximum_Inundation_Rasters\{Region}_Region"
output_shapefile = os.path.join(destination_dir, f"{Region}_combined_polygons.shp")

# Create the destination directory if it doesn't exist
os.makedirs(destination_dir, exist_ok=True)

# Find all .tif files in the source directory and subdirectories that contain '2500y84p'
pattern = os.path.join(source_dir, '**', '*2500y84p*.tif')
polygons = []

for filepath in glob.glob(pattern, recursive=True):
    try:
        # Open the raster file
        with rasterio.open(filepath) as src:
            # Read the first band
            image = src.read(1)
            # Convert the mask to polygons
            mask_polygons = mask_to_polygons_layer(image, src.transform)
            polygons.append(mask_polygons)

        print(f"Processed {filepath}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

# Create a GeoDataFrame from the polygons
gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")  # Adjust CRS if necessary

# Merge all polygons into a single polygon (dissolve)
merged_polygon = gdf.unary_union

# Create a new GeoDataFrame for the merged polygon
merged_gdf = gpd.GeoDataFrame(geometry=[merged_polygon], crs="EPSG:4326")

# Save the merged polygon to a shapefile
merged_gdf.to_file(output_shapefile, driver='ESRI Shapefile')

print(f"All polygons have been combined and saved to {output_shapefile}")
