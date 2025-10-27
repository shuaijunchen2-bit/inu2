import rasterio
from rasterio.merge import merge
import numpy as np
import glob
import os

Region = "Canterbury"

# List all the raster files you want to merge
raster_files = glob.glob(f'D:/Nationwide_Tsunami_Inundation/Shoreline_Rasters/{Region}_Region/*.tif')

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
output_path = f"D:/Bridge_Assessment/Merged_{Region}_Shorelines.tif"
with rasterio.open(output_path, "w", **out_meta) as dest:
    dest.write(mosaic)

# Close all source files
for src in src_files_to_mosaic:
    src.close()

print(f"Merged raster saved to {output_path}")
