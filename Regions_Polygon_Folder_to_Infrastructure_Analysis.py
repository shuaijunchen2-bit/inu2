import geopandas as gpd
import pandas as pd
import os
import re

def extract_file_data(file_path):
    # Define the pattern to match the new file naming convention
    pattern = r"Clipped_Merged_(?P<region>[^_]+(?:_[^_]+)*)_H(?P<period>\d+)y(?P<percent>\d+)p\.tif"
    match = re.search(pattern, file_path)
    if match:
        return match.groupdict()
    else:
        return None

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


# Define the path to the directory containing the GeoPackage files
gpkg_directory = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons"
output_directory = "D:/Nationwide_Tsunami_Inundation/Infrastructure_Metrics"

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Load infrastructure data
road_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/nz-roads.shp").to_crs("EPSG:2193")
building_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-building-outlines/nz-building-outlines.shp").to_crs("EPSG:2193")
rail_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-railway-centrelines-topo-150k/nz-railway-centrelines-topo-150k.shp").to_crs("EPSG:2193")
bridge_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/lds-nz-bridge-centrelines-topo-150k-SHP/nz-bridge-centrelines-topo-150k.shp").to_crs("EPSG:2193")
airport_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-airport-polygons-topo-150k/nz-airport-polygons-topo-150k.shp").to_crs("EPSG:2193")
hospital_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-hospital/nz-hospital.shp").to_crs("EPSG:2193")
school_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-schools/nz-schools.shp").to_crs("EPSG:2193")
tank_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-tank-polygons-topo-150k/nz-tank-polygons-topo-150k.shp").to_crs("EPSG:2193")

# List all the GPKG files in the directory
gpkg_files = [os.path.join(root, file) for root, _, files in os.walk(gpkg_directory) for file in files if file.endswith('.gpkg')]

# Initialize a DataFrame to store results for all regions
all_results_df = pd.DataFrame()

# Process each GPKG file
for gpkg_file in gpkg_files:
    print(f"Processing file: {gpkg_file}")
    inundation_polygon = gpd.read_file(gpkg_file).to_crs("EPSG:2193")
    
    # Extract metadata from the filename
    extracted_data = extract_file_data(gpkg_file)
    if extracted_data is None:
        print(f"File path does not match pattern: {gpkg_file}")
        continue
    
    # Calculate infrastructure metrics and save clipped assets
    (road_length, building_count, rail_length, bridge_count, airport_count, 
     hospital_count, school_count, tank_count, road_gpkg_path, 
     building_gpkg_path, rail_gpkg_path, bridge_gpkg_path, airport_gpkg_path, 
     hospital_gpkg_path, school_gpkg_path, tank_gpkg_path) = calculate_and_save_clipped_assets(
        inundation_polygon, road_data, building_data, rail_data, bridge_data, 
        airport_data, hospital_data, school_data, tank_data, extracted_data)

    # Append the results to the DataFrame for all regions
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
        'Road_GPKG': road_gpkg_path,
        'Building_GPKG': building_gpkg_path,
        'Rail_GPKG': rail_gpkg_path,
        'Bridge_GPKG': bridge_gpkg_path,
        'Airport_GPKG': airport_gpkg_path,
        'Hospital_GPKG': hospital_gpkg_path,
        'School_GPKG': school_gpkg_path,
        'Tank_GPKG': tank_gpkg_path
    }])
    all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)

    # Save the results to a CSV file for the current region
    region_output_csv_path = os.path.join(output_directory, f"{extracted_data['region']}_Infrastructure_Metrics.csv")
    results_df.to_csv(region_output_csv_path, index=False)
    print(f"Results for {extracted_data['region']} saved to {region_output_csv_path}")

# Save all results to a single CSV file
all_results_csv_path = os.path.join(output_directory, "All_Regions_Infrastructure_Metrics.csv")
all_results_df.to_csv(all_results_csv_path, index=False)
print(f"All results saved to {all_results_csv_path}")

