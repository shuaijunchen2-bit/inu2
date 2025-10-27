# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 20:06:19 2024

@author: OEM
"""

import os
import shutil
import glob
import rasterio
from rasterio.merge import merge
import numpy as np

Region = "Canterbury"

# Define the source and destination directories
source_dir = rf"D:\Nationwide_Tsunami_Inundation\Latest_Inundation_Results\{Region}_Region"
destination_dir = rf"D:\Nationwide_Tsunami_Inundation\Roughness_Rasters\{Region}_Region"

# Create the destination directory if it doesn't exist
os.makedirs(destination_dir, exist_ok=True)

# Find all Shoreline_Raster.tif files in the source directory and subdirectories
for filepath in glob.glob(os.path.join(source_dir, '**', 'Roughness_Raster.tif'), recursive=True):
    try:
        # Create a unique filename by including part of the directory path
        relative_path = os.path.relpath(filepath, source_dir)
        unique_filename = relative_path.replace(os.sep, '_')

        # Ensure the unique filename does not exceed filesystem limits
        unique_filename = unique_filename[:255]  # Adjust if necessary

        # Destination path for the copied file
        destination_path = os.path.join(destination_dir, unique_filename)

        # Copy the file to the destination directory with the new unique name
        shutil.copy(filepath, destination_path)
        print(f"Copied {filepath} to {destination_path}")
    except Exception as e:
        print(f"Error copying {filepath}: {e}")

print("All Shoreline_Raster.tif files have been copied.")

##############################################################################################################

# List all the raster files you want to merge
raster_files = glob.glob(f'D:/Nationwide_Tsunami_Inundation/Roughness_Rasters/{Region}_Region/*.tif')

# Read each raster file and stack them into a list
src_files_to_mosaic = []
for fp in raster_files:
    src = rasterio.open(fp)
    src_files_to_mosaic.append(src)

# Merge the rasters
mosaic, out_trans = merge(src_files_to_mosaic)

# Ensure the data type is boolean
mosaic = mosaic.astype(np.uint8)

# Set all overlapping areas to 1 (shoreline)
mosaic[mosaic > 0] = 1

# Get the metadata of the first file
out_meta = src_files_to_mosaic[0].meta.copy()

# Update the metadata to reflect the number of layers, transform, and height/width
out_meta.update({
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans
})

# Write the mosaic raster to disk
output_path = f"D:/Bridge_Assessment/Merged_{Region}_Roughness_Raster.tif"
with rasterio.open(output_path, "w", **out_meta) as dest:
    dest.write(mosaic)

# Close all source files
for src in src_files_to_mosaic:
    src.close()

print(f"Merged raster saved to {output_path}")