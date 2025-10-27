import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge

# Define the target region and paths
Region = "Wellington"
parent_dir = "D:/Nationwide_Tsunami_Inundation/FABDEM_2_Latest_Inundation_Results"
segments_shapefile_path = "D:/Nationwide_Tsunami_Inundation/TsunamiZones2021/Shapefiles2021/Maximum_Inundation_TsunamiHazard2021_2193_Regions_and_Territorial_Authorities.shp"
region_shapefile_path = "D:/Nationwide_Tsunami_Inundation/statsnz-new-zealand-4layers-SHP/regional-council-2023-generalised/regional-council-2023-generalised.shp"
output_dir = f"D:/Nationwide_Tsunami_Inundation/Latest_Inundation_Rasters_Clipped/Clipped_{Region}_Region"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load the segments shapefile
segments = gpd.read_file(segments_shapefile_path)

# Load the region polygons shapefile
regions = gpd.read_file(region_shapefile_path)

# Filter segments that belong to or intersect with the target region
filtered_segments = segments[segments['REGC2023_1'].str.contains(Region, na=False)]

# Filter the region polygon by the target region
region_polygon = regions[regions['REGC2023_1'] == f"{Region} Region"]

# Function to clip a raster by a given polygon and replace 0s with NaN
def clip_raster(raster_path, polygon):
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, [polygon.geometry], crop=True)
        out_image = np.where(out_image == 0, np.nan, out_image)  # Replace 0s with NaN
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
    section_name = section_name.replace(" ", "_").replace("/", "_").replace(" / ", "_")
    return section_name

# Identify all folders containing relevant segments
segment_folders = set()
for _, segment in filtered_segments.iterrows():
    transformed_name = transform_section_name(segment['SECTN_NAME'])
    for region_folder in os.listdir(parent_dir):
        region_folder_path = os.path.join(parent_dir, region_folder)
        if os.path.isdir(region_folder_path):
            for segment_folder in os.listdir(region_folder_path):
                if transform_section_name(segment_folder) == transformed_name:
                    segment_folders.add(os.path.join(region_folder_path, segment_folder))

# Iterate over identified segment folders
for segment_folder_path in segment_folders:
    # Iterate over .tif files in the segment folder
    for file in os.listdir(segment_folder_path):
        if file.endswith("10mResolution.tif"):
            file_path = os.path.join(segment_folder_path, file)
            
            # Clip the raster for each matching segment
            for _, segment in filtered_segments.iterrows():
                if transform_section_name(segment['SECTN_NAME']) in segment_folder_path:
                    clipped_image, clipped_meta = clip_raster(file_path, segment)

                    # Define the output path for the clipped image
                    output_subfolder = os.path.join(output_dir, transform_section_name(segment['SECTN_NAME']))
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
    mosaic, out_transform = merge(datasets, method='max')  # Merge, taking max value in overlaps
    out_meta = datasets[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_transform,
        "nodata": np.nan
    })
    return mosaic, out_meta

# Function to clip the merged raster by the region polygon
def clip_merged_raster(merged_raster_path, output_path, polygon):
    with rasterio.open(merged_raster_path) as src:
        out_image, out_transform = mask(src, [polygon.geometry], crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": np.nan
        })
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)

# Process each return period
for return_period in return_periods:
    print(f"Processing return period: {return_period}...")
    raster_files = []

    for subfolder in os.listdir(output_dir):
        subfolder_path = os.path.join(output_dir, subfolder)
        if os.path.isdir(subfolder_path):
            for file in os.listdir(subfolder_path):
                if return_period in file and file.endswith(".tif"):
                    raster_files.append(os.path.join(subfolder_path, file))

    # Check if there are raster files to merge
    if raster_files:
        print(f"Merging raster files for {return_period}...")
        # Merge the rasters
        merged_mosaic, merged_meta = merge_rasters(raster_files)

        # Clip the merged mosaic directly, without saving the merged raster
        clipped_merged_output_path = os.path.join(output_dir, f"Clipped_Merged_{Region}_{return_period}.tif")
        
        # Define the clipping function to handle in-memory clipping
        def clip_merged_in_memory(merged_mosaic, merged_meta, polygon, output_path):
            # Clip the in-memory merged mosaic with the provided polygon
            with rasterio.MemoryFile() as memfile:
                with memfile.open(**merged_meta) as dataset:
                    dataset.write(merged_mosaic)
                    out_image, out_transform = mask(dataset, [polygon.geometry], crop=True)
                    out_meta = merged_meta.copy()
                    out_meta.update({
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                        "nodata": np.nan
                    })
                    with rasterio.open(output_path, "w", **out_meta) as dest:
                        dest.write(out_image)
        
        # Clip the merged mosaic and save the final output
        clip_merged_in_memory(merged_mosaic, merged_meta, region_polygon.iloc[0], clipped_merged_output_path)

        print(f"Clipped and merged raster for {return_period} saved at {clipped_merged_output_path}")
    else:
        print(f"No raster files found for return period {return_period}")