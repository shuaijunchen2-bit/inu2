# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 20:06:19 2024

@author: OEM
"""

import os
import shutil
import glob

Region = "Marlborough"

# Define the source and destination directories
source_dir = rf"D:\Nationwide_Tsunami_Inundation\Inundation_Results\{Region}_Region"
destination_dir = rf"D:\Nationwide_Tsunami_Inundation\Maximum_Inundation_Rasters\{Region}_Region"

# Create the destination directory if it doesn't exist
os.makedirs(destination_dir, exist_ok=True)

# Find all .tif files in the source directory and subdirectories that contain '2500y50p' and '10mResolution.tif'
pattern = os.path.join(source_dir, '**', '*2500y50p*10mResolution.tif')
for filepath in glob.glob(pattern, recursive=True):
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

print("All specified .tif files have been copied.")
