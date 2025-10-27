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

Region = "Hawke's_Bay"

# Define the source and destination directories
source_dir = rf"D:\Nationwide_Tsunami_Inundation\FABDEM_Latest_Inundation_Results\{Region}_Region"
destination_dir = rf"D:\Nationwide_Tsunami_Inundation\FABDEM_Maximum_Inundation_Rasters\{Region}_Region"

# Create the destination directory if it doesn't exist
os.makedirs(destination_dir, exist_ok=True)

# Find all .tif files in the source directory and subdirectories that contain '2500y84p'
pattern = os.path.join(source_dir, '**', '*2500y84p*.tif')
raster_files = []

for filepath in glob.glob(pattern, recursive=True):
    try:
        # Create the destination path by keeping the same filename
        destination_path = os.path.join(destination_dir, os.path.basename(filepath))

        # Copy the file to the destination directory with the same name
        shutil.copy(filepath, destination_path)
        raster_files.append(destination_path)
        print(f"Copied {filepath} to {destination_path}")
    except Exception as e:
        print(f"Error copying {filepath}: {e}")

print("All specified .tif files have been copied.")
