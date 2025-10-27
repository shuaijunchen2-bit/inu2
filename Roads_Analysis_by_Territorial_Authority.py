import geopandas as gpd
import pandas as pd
import os
import re
import time

# Define the root directory containing the subfolders for each region
root_dir = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons_Territorial_Authority"

# Get the list of all subfolder names within the root directory
Territorial_Authorities = [folder for folder in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, folder))]


# Define the path to the base directories
base_inundation_directory = root_dir
base_road_shapefile_path = 'D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/ONRC-dissolved-roads.shp'
base_output_directory = 'D:/Nationwide_Tsunami_Inundation/Clipped_Roads_Territorial_Authorities'

# Ensure the base output directory exists
os.makedirs(base_output_directory, exist_ok=True)

# Regex pattern to extract return period and percentile
pattern = r"H(?P<return_period>\d+)y(?P<percentile>\d+)p_.*_Inundation_Polygon.gpkg"

# Load the road shapefile
roads_gdf = gpd.read_file(base_road_shapefile_path)

# Process each region
for Territory in Territorial_Authorities:
    # Reset the cumulative dataframe for the new region
    cumulative_results_df = pd.DataFrame()

    # Define the paths for the current region
    inundation_directory = os.path.join(base_inundation_directory, f"{Territory}")
    output_directory = os.path.join(base_output_directory, f"{Territory}")
    
    # Ensure the output directory exists for the current region
    os.makedirs(output_directory, exist_ok=True)
    
    # List all the inundation GPKG files for the current region
    inundation_files = [f for f in os.listdir(inundation_directory) if f.endswith('.gpkg')]
    
    # Process each inundation file in the current region
    for inundation_file in inundation_files:
        inundation_path = os.path.join(inundation_directory, inundation_file)
        inundation_gdf = gpd.read_file(inundation_path)

        # Extract return period and percentile from filename
        match = re.search(pattern, inundation_file)
        if match:
            return_period = match.group("return_period")
            percentile = match.group("percentile")
        else:
            print(f"Filename {inundation_file} does not match expected pattern.")
            continue
        
        # Clip the road data by the inundation polygon
        clipped_roads = gpd.clip(roads_gdf, inundation_gdf)

        # Calculate length for each feature in km and append it as a new column
        clipped_roads['Length_km'] = clipped_roads.geometry.length / 1000  # Convert to kilometers

        # Keep only the columns 'Length_km', 'ONRCClass', and the geometry
        clipped_roads = clipped_roads[['Length_km', 'ONRCClass', 'geometry']]
        
        # Construct the output file path for clipped roads
        file_name = f'Clipped_{Territory}_Roads_{os.path.splitext(inundation_file)[0]}.gpkg'
        clipped_output_path = os.path.join(output_directory, file_name)
        
        # Debug: Print the constructed output path
        print(f"Saving clipped roads to: {clipped_output_path}")
        
        # Save the clipped roads to a new GeoPackage file with length information
        try:
            clipped_roads.to_file(clipped_output_path, driver="GPKG")
        except Exception as e:
            print(f"Error saving {clipped_output_path}: {e}")
            continue
        
        # Calculate the total length of each road type within the inundation zone
        road_lengths = []
        total_length_km_all_roads = clipped_roads['Length_km'].sum()
        
        for road_type in clipped_roads['ONRCClass'].unique():
            road_type_gdf = clipped_roads[clipped_roads['ONRCClass'] == road_type]
            total_length_km = road_type_gdf['Length_km'].sum()
            road_lengths.append({
                'Territorial_Authority': Territory,
                'inundation_file': inundation_file,
                'Return_Period': return_period,
                'Percentile': percentile,
                'ONRCClass': road_type,
                'total_length_km': total_length_km
            })
        
        # Add the total length of all roads as a separate row
        road_lengths.append({
            'Territorial_Authority': Territory,
            'inundation_file': inundation_file,
            'Return_Period': return_period,
            'Percentile': percentile,
            'ONRCClass': 'Total All Roads',
            'total_length_km': total_length_km_all_roads
        })
        
        # Append the results to the cumulative dataframe
        results_df = pd.DataFrame(road_lengths)
        cumulative_results_df = pd.concat([cumulative_results_df, results_df], ignore_index=True)

        # Print the results
        print(f"Results for {inundation_file} in {Territory}:")
        for road_length in road_lengths:
            print(f"Road type: {road_length['ONRCClass']}, Total length (km): {road_length['total_length_km']}")
    
    # Save the cumulative results for the current region to a CSV file
    cumulative_results_csv_path = os.path.join(output_directory, f'Cumulative_Results_{Territory}.csv')
    cumulative_results_df.to_csv(cumulative_results_csv_path, index=False)

    print(f"Cumulative results saved to {cumulative_results_csv_path} for region {Territory}")
