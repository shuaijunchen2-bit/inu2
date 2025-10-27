import os
import numpy as np
import rasterio
from rasterio.merge import merge

# Define the region and output directory
region = "Bay_of_Plenty"  # Replace with the actual region name
output_dir = f"D:/Nationwide_Tsunami_Inundation/Clipped_Inundation_Results/Clipped_{region}_Region"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# List of return periods to process
return_periods = [
    "H100y50p", "H100y84p",
    "H250y50p", "H250y84p",
    "H500y50p", "H500y84p",
    "H1000y50p", "H1000y84p",
    "H1500y50p", "H1500y84p",
    "H2000y50p", "H2000y84p",
    "H2500y50p", "H2500y84p"
]

# Function to merge rasters with largest value in overlapping areas
def merge_rasters(raster_paths):
    datasets = [rasterio.open(path) for path in raster_paths]
    # Merge rasters, taking the maximum value in overlapping areas
    mosaic, out_transform = merge(datasets, method='max')
    out_meta = datasets[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_transform,
        "nodata": np.nan
    })
    return mosaic, out_meta

# Process each return period
for return_period in return_periods:
    # Collect all .tif files corresponding to the return period
    raster_files = []

    for subfolder in os.listdir(output_dir):
        subfolder_path = os.path.join(output_dir, subfolder)
        if os.path.isdir(subfolder_path):
            for file in os.listdir(subfolder_path):
                if return_period in file and file.endswith(".tif"):
                    raster_files.append(os.path.join(subfolder_path, file))

    # Check if there are raster files to merge
    if raster_files:
        # Merge the rasters
        merged_mosaic, merged_meta = merge_rasters(raster_files)
        
        # Define the output path for the merged raster
        merged_output_path = os.path.join(output_dir, f"Merged_{region}_{return_period}.tif")
        
        # Save the merged raster
        with rasterio.open(merged_output_path, "w", **merged_meta) as dest:
            dest.write(merged_mosaic)

        print(f"Merged raster for {return_period} saved at {merged_output_path}")
    else:
        print(f"No raster files found for return period {return_period}")
