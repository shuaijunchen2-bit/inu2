import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge

Region = "Marlborough"

# Set the parent directory, shapefile path, and output directory
parent_dir = f"D:/Nationwide_Tsunami_Inundation/Latest_Inundation_Results/{Region}_Region"
shapefile_path = "D:/Nationwide_Tsunami_Inundation/TsunamiZones2021/Shapefiles2021/Maximum_Inundation_TsunamiHazard2021_Updated_2193.shp"
output_dir = f"D:/Nationwide_Tsunami_Inundation/Clipped_Inundation_Results/Clipped_{Region}_Region"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load the shapefile
shapefile = gpd.read_file(shapefile_path)

# Function to clip a raster by a given polygon and replace 0s with NaN
def clip_raster(raster_path, polygon):
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, [polygon.geometry], crop=True)
        # Replace 0s with NaN
        out_image = np.where(out_image == 0, np.nan, out_image)
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": np.nan
        })
        return out_image, out_meta

# Function to transform SECTN_NAME to folder name format
def transform_section_name(section_name):
    section_name = section_name.replace(" ", "_")
    section_name = section_name.replace("/", "_")
    section_name = section_name.replace(" / ", "_")
    return section_name

# Iterate over subfolders in the parent directory
for subfolder in os.listdir(parent_dir):
    subfolder_path = os.path.join(parent_dir, subfolder)
    
    # Check if the item is a directory
    if os.path.isdir(subfolder_path):
        # Iterate through shapefile rows to find matching SECTN_NAME
        matching_row = None
        for _, row in shapefile.iterrows():
            transformed_name = transform_section_name(row['SECTN_NAME'])
            if transformed_name == subfolder:
                matching_row = row
                break

        if matching_row is not None:
            # Extract the polygon
            polygon = matching_row

            # Iterate over .tif files in the subfolder
            for file in os.listdir(subfolder_path):
                if file.endswith("10mResolution.tif"):
                    file_path = os.path.join(subfolder_path, file)
                    
                    # Clip the raster
                    clipped_image, clipped_meta = clip_raster(file_path, polygon)

                    # Define the output path for the clipped image
                    output_subfolder = os.path.join(output_dir, subfolder)
                    os.makedirs(output_subfolder, exist_ok=True)
                    clipped_path = os.path.join(output_subfolder, f"Clipped_{file}")

                    # Save the clipped image
                    with rasterio.open(clipped_path, "w", **clipped_meta) as dest:
                        dest.write(clipped_image)

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
        merged_output_path = os.path.join(output_dir, f"Merged_{Region}_{return_period}.tif")
        
        # Save the merged raster
        with rasterio.open(merged_output_path, "w", **merged_meta) as dest:
            dest.write(merged_mosaic)

        print(f"Merged raster for {return_period} saved at {merged_output_path}")
    else:
        print(f"No raster files found for return period {return_period}")
