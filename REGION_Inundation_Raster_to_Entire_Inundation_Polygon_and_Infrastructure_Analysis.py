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

def calculate_and_save_clipped_assets(inundation_polygon, road_data, building_data, rail_data, bridge_data, airport_data, hospital_data, school_data, tank_data, extracted_data):
    base_output_directory = f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/{extracted_data['region']}_region"
    
    # Ensure the data is in EPSG:2193
    inundation_polygon = inundation_polygon.to_crs("EPSG:2193")

    # Access spatial indices to ensure they are created
    road_data.sindex
    building_data.sindex
    rail_data.sindex
    bridge_data.sindex
    airport_data.sindex
    hospital_data.sindex
    school_data.sindex
    tank_data.sindex

    def save_clipped_data(data_clipped, asset_name):
        if not data_clipped.empty:
            asset_output_directory = os.path.join(base_output_directory, asset_name)
            os.makedirs(asset_output_directory, exist_ok=True)
            gpkg_path = os.path.join(asset_output_directory, f"Clipped_{asset_name}_H{extracted_data['period']}y{extracted_data['percent']}p.gpkg")
            data_clipped.to_file(gpkg_path, driver="GPKG")
            return gpkg_path
        return None

    road_data_clipped = gpd.clip(road_data.to_crs("EPSG:2193"), inundation_polygon)
    print("Roads Clipped")
    building_data_clipped = gpd.clip(building_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("building_i")
    print("Buildings Clipped")
    rail_data_clipped = gpd.clip(rail_data.to_crs("EPSG:2193"), inundation_polygon)
    print("Rail Clipped")
    bridge_data_clipped = gpd.clip(bridge_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("t50_fid")
    print("Bridges Clipped")
    airport_data_clipped = gpd.clip(airport_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("t50_fid")
    print("Airports Clipped")
    hospital_data_clipped = gpd.clip(hospital_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("facility_i")
    print("Hospitals Clipped")
    school_data_clipped = gpd.clip(school_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("facility_i")
    print("Schools Clipped")
    tank_data_clipped = gpd.clip(tank_data.to_crs("EPSG:2193"), inundation_polygon).dissolve("t50_fid")
    print("Tanks Clipped")

    road_length = road_data_clipped.length.sum() / 1000  # Convert to km
    building_count = len(building_data_clipped)
    rail_length = rail_data_clipped.length.sum() / 1000  # Convert to km
    bridge_count = len(bridge_data_clipped)
    airport_count = len(airport_data_clipped)
    hospital_count = len(hospital_data_clipped)
    school_count = len(school_data_clipped)
    tank_count = len(tank_data_clipped)

    # Save the clipped data as GPKG
    road_gpkg_path = save_clipped_data(road_data_clipped, "Roads")
    building_gpkg_path = save_clipped_data(building_data_clipped, "Buildings")
    rail_gpkg_path = save_clipped_data(rail_data_clipped, "Rails")
    bridge_gpkg_path = save_clipped_data(bridge_data_clipped, "Bridges")
    airport_gpkg_path = save_clipped_data(airport_data_clipped, "Airports")
    hospital_gpkg_path = save_clipped_data(hospital_data_clipped, "Hospitals")
    school_gpkg_path = save_clipped_data(school_data_clipped, "Schools")
    tank_gpkg_path = save_clipped_data(tank_data_clipped, "Tanks")

    return road_length, building_count, rail_length, bridge_count, airport_count, hospital_count, school_count, tank_count, road_gpkg_path, building_gpkg_path, rail_gpkg_path, bridge_gpkg_path, airport_gpkg_path, hospital_gpkg_path, school_gpkg_path, tank_gpkg_path

# Load infrastructure data
road_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/nz-roads.shp").to_crs("EPSG:2193")
building_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-building-outlines/nz-building-outlines.shp").to_crs("EPSG:2193")
rail_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-railway-centrelines-topo-150k/nz-railway-centrelines-topo-150k.shp").to_crs("EPSG:2193")
bridge_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/lds-nz-bridge-centrelines-topo-150k-SHP/nz-bridge-centrelines-topo-150k.shp").to_crs("EPSG:2193")
airport_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-airport-polygons-topo-150k/nz-airport-polygons-topo-150k.shp").to_crs("EPSG:2193")
hospital_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-hospital/nz-hospital.shp").to_crs("EPSG:2193")
school_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-schools/nz-schools.shp").to_crs("EPSG:2193")
tank_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-tank-polygons-topo-150k/nz-tank-polygons-topo-150k.shp").to_crs("EPSG:2193")

# Directory containing the GeoTIFF files
Regions_of_Files = ["Hawke's Bay", "Manawatu-Whanganui", "Wellington", "Tasman", "West Coast", "Southland"]
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
            
            if isinstance(entire_inundation_polygon, (Polygon, MultiPolygon)):
                output_directory, gpkg_path = save_geometry_to_file(entire_inundation_polygon, extracted_data)

                # Load the saved GPKG file
                inundation_polygon = gpd.read_file(gpkg_path).to_crs("EPSG:2193")

                # Calculate infrastructure metrics and save clipped assets
                road_length, building_count, rail_length, bridge_count, airport_count, hospital_count, school_count, tank_count, road_gpkg_path, building_gpkg_path, rail_gpkg_path, bridge_gpkg_path, airport_gpkg_path, hospital_gpkg_path, school_gpkg_path, tank_gpkg_path = calculate_and_save_clipped_assets(inundation_polygon, road_data, building_data, rail_data, bridge_data, airport_data, hospital_data, school_data, tank_data, extracted_data)

                # Append the results to the DataFrame for the current region
                results_df = pd.DataFrame([{
                    'Region': extracted_data['region'],
                    'Period': extracted_data['period'],
                    'Percent': extracted_data['percent'],
                    'Road_Length_km': road_length,
                    'Building_Count': building_count,
                    'Rail_Length_km': rail_length,
                    'Bridge_Count': bridge_count,
                    'Airport_Count': airport_count,
                    'Hospital_Count': hospital_count,
                    'School_Count': school_count,
                    'Tank_Count': tank_count,
                }])
                region_results_df = pd.concat([region_results_df, results_df], ignore_index=True)
            else:
                print(f"Unsupported geometry type: {type(entire_inundation_polygon)}")

    # Save the results to a CSV file for the current region
    output_csv_path = os.path.join(output_directory, f"{Region_of_Files}_Infrastructure_Metrics.csv")
    region_results_df.to_csv(output_csv_path, index=False)
    print(f"Results for {Region_of_Files} saved to {output_csv_path}")