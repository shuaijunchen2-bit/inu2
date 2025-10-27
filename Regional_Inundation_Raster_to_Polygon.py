import geopandas as gpd
import pandas as pd
import os
import rasterio as rio
from shapely.geometry import box, Polygon, MultiPolygon
import shapely.geometry
import numpy as np
from rasterio import features
import re
from collections import defaultdict

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

def extract_file_data(file_path):
    # Define the pattern to match the new file naming convention
    pattern = r"Clipped_Merged_(?P<region>[^_]+(?:_[^_]+)*)_H(?P<period>\d+)y(?P<percent>\d+)p\.tif"
    match = re.search(pattern, file_path)
    if match:
        return match.groupdict()
    else:
        return None

def save_geometry_to_file(geometry, extracted_data):
    geo_df = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:2193")
    output_directory = f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{extracted_data['region']}_region"
    os.makedirs(output_directory, exist_ok=True)
    output_file_path = f"{output_directory}/Entire_H{extracted_data['period']}y{extracted_data['percent']}p_Inundation_Polygon.gpkg"
    geo_df.to_file(output_file_path, driver="GPKG")
    print(f"GeoDataFrame saved to {output_file_path}")
    return output_directory, output_file_path

# Directory containing the GeoTIFF files
Regions_of_Files = ["Southland"]

for Region_of_Files in Regions_of_Files:
    # Initialize a DataFrame for the current region
    region_results_df = pd.DataFrame()

    directory = f"D:/Nationwide_Tsunami_Inundation/Latest_Inundation_Rasters_Clipped/Clipped_{Region_of_Files}_Region"
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("Clipped_Merged"):
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    # Process each file
    for file in file_paths:
        print(f"Processing file: {file}")
        with rio.open(file) as inundation:
            bounds = inundation.bounds

            extracted_data = extract_file_data(file)
            if extracted_data is None:
                print(f"File path does not match pattern: {file}")
                continue

            polygon = gpd.GeoDataFrame({"id": 1, "geometry": [box(*bounds)]}, crs="EPSG:2193")
            inundation_array = inundation.read(1)
            entire_inundation_array = (inundation_array > 0).astype(np.uint8)
            entire_inundation_polygon = mask_to_polygons_layer(entire_inundation_array, inundation.transform)
            print("Polygon Generated")
            output_directory, gpkg_path = save_geometry_to_file(entire_inundation_polygon, extracted_data)