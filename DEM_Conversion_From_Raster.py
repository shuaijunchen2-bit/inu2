# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 17:10:18 2024

@author: OEM
"""

import rasterio
from rasterio.enums import Resampling
import numpy as np

def subtract_rasters(dem_path, conversion_path, output_path):
    # Open the DEM raster
    with rasterio.open(dem_path) as dem_src:
        dem_data = dem_src.read(1)
        dem_meta = dem_src.meta.copy()

    # Open the conversion raster
    with rasterio.open(conversion_path) as conv_src:
        # Resample the conversion raster to match the DEM raster if they don't match
        if dem_src.shape != conv_src.shape or dem_src.transform != conv_src.transform:
            conv_data = conv_src.read(
                1,
                out_shape=(dem_src.height, dem_src.width),
                resampling=Resampling.bilinear
            )
            conv_transform = dem_src.transform
        else:
            conv_data = conv_src.read(1)
            conv_transform = conv_src.transform

    # Subtract the conversion raster from the DEM raster
    result_data = dem_data - conv_data

    # Set any value below -9000 to -9999
    result_data[result_data < -9000] = -9999

    # Update metadata for the output file
    dem_meta.update({
        "driver": "GTiff",
        "height": result_data.shape[0],
        "width": result_data.shape[1],
        "transform": dem_src.transform,
        "crs": dem_src.crs,
        "nodata": -9999  # Set -9999 as the nodata value
    })

    # Save the result to a new file
    with rasterio.open(output_path, "w", **dem_meta) as dest:
        dest.write(result_data, 1)

    print(f"Subtraction result saved to {output_path}")

# Define the input and output file paths
dem_path = "D:/Nationwide_Tsunami_Inundation/DEM_Data/Manawatu-Whanganui_NIWA_1_10mResolution.tif"
conversion_path = "D:/Nationwide_Tsunami_Inundation/DEM_Data/Wellington_Conversion_Raster.tif"
output_path = "D:/Nationwide_Tsunami_Inundation/DEM_Data/Manawatu-Whanganui_NIWA_1_-NZVD2016_10mResolution.tif"

# Subtract the conversion raster from the DEM raster and save the result
subtract_rasters(dem_path, conversion_path, output_path)
