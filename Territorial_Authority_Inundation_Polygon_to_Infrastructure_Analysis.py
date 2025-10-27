import geopandas as gpd
import pandas as pd
import os
import re
import glob

def extract_file_data(file_path, root):
    # Define the pattern to match the file naming convention
    patterns = [
        r"H(?P<period>\d+)y(?P<percent>\d+)p_(?P<region>[\w\s\-\_']+)_Inundation_Polygon\.gpkg"  # Territorial pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, file_path)
        if match:
            data = match.groupdict()
            if 'region' not in data:
                data['region'] = os.path.basename(root)
            return data
    return None

def save_clipped_data(data_clipped, asset_name, output_directory, extracted_data):
    if not data_clipped.empty:
        
        if 'fid' in data_clipped.columns:
            data_clipped['fid'] = data_clipped['fid'].astype(int)
        elif 't50_fid' in data_clipped.columns:  # Adjust this if another field is causing the issue
            data_clipped['t50_fid'] = data_clipped['t50_fid'].astype(int)
        
        asset_output_directory = os.path.join(output_directory, asset_name)
        os.makedirs(asset_output_directory, exist_ok=True)
        gpkg_path = os.path.join(asset_output_directory, f"Clipped_{asset_name}_H{extracted_data['period']}y{extracted_data['percent']}p.gpkg")
        data_clipped.to_file(gpkg_path, driver="GPKG")
        return gpkg_path
    return None

# Load national infrastructure data
road_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/ONRC-dissolved-roads-coastal-clip.shp").to_crs("EPSG:2193")
building_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-building-outlines/nz-building-outlines-coastal-clip.shp").to_crs("EPSG:2193")
rail_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-railway-centrelines-topo-150k/nz-railway-centrelines-topo-150k.shp").to_crs("EPSG:2193")
bridge_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/lds-nz-bridge-centrelines-topo-150k-SHP/nz-bridge-centrelines-topo-150k.shp").to_crs("EPSG:2193")
airport_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-airport-polygons-topo-150k/nz-airport-polygons-topo-150k.shp").to_crs("EPSG:2193")
hospital_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-hospital/nz-hospital.shp").to_crs("EPSG:2193")
school_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-schools/nz-schools.shp").to_crs("EPSG:2193")
tank_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-tank-polygons-topo-150k/nz-tank-polygons-topo-150k.shp").to_crs("EPSG:2193")

road_data.sindex
building_data.sindex
rail_data.sindex
bridge_data.sindex
airport_data.sindex
hospital_data.sindex
school_data.sindex
tank_data.sindex

# Specify the main directory containing the subfolders with inundation polygons
main_directory = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons_Territorial_Authority"

# Loop through each subfolder in the main directory
for subfolder in os.listdir(main_directory)[::-1]:
    subfolder_path = os.path.join(main_directory, subfolder)
    if os.path.isdir(subfolder_path):
        print(f"Processing subfolder: {subfolder_path}")

        # Determine the output directory and CSV file path
        region_name = os.path.basename(subfolder_path)
        output_directory = os.path.join("D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Clipped_Assets", region_name)
        
        # Check if any CSV file already exists in the output directory
        csv_files = glob.glob(os.path.join(output_directory, "*.csv"))
        
        if csv_files:
            print(f"CSV file already exists for {region_name}. Skipping...")
            continue  # Skip processing for this territorial authority
        
        folders_completed = glob.glob(output_directory)
        if folders_completed:
            print(f"{region_name} subfolder already exists. Skipping...")
            continue  # Skip processing for this territorial authority
        
        
        # Initialize variables to store the 2500y84p clipped assets
        road_data_clipped_2500y84p = None
        building_data_clipped_2500y84p = None
        rail_data_clipped_2500y84p = None
        bridge_data_clipped_2500y84p = None
        airport_data_clipped_2500y84p = None
        hospital_data_clipped_2500y84p = None
        school_data_clipped_2500y84p = None
        tank_data_clipped_2500y84p = None

        # Initialize an empty DataFrame to store all results for this subfolder
        all_results_df = pd.DataFrame()

        # Find the 2500y84p polygon
        polygon_2500y84p = None
        for root, _, files in os.walk(subfolder_path):
            for file in files:
                if file.endswith(".gpkg") and "2500y84p" in file:
                    full_path = os.path.join(root, file)
                    print(f"Found 2500y84p polygon: {full_path}")
                    polygon_2500y84p = gpd.read_file(full_path).to_crs("EPSG:2193")
                    break
            if polygon_2500y84p is not None:
                break

        if polygon_2500y84p is None:
            print(f"2500y84p polygon not found in subfolder {subfolder}. Skipping...")
            continue

        polygon_2500y84p.sindex

        # Clip all national assets to the 2500y84p polygon
        road_data_clipped_2500y84p = gpd.clip(road_data, polygon_2500y84p)
        building_data_clipped_2500y84p = gpd.clip(building_data, polygon_2500y84p).dissolve("building_i").reset_index() 
        rail_data_clipped_2500y84p = gpd.clip(rail_data, polygon_2500y84p)
        bridge_data_clipped_2500y84p = gpd.clip(bridge_data, polygon_2500y84p).dissolve("t50_fid").reset_index() 
        airport_data_clipped_2500y84p = gpd.clip(airport_data, polygon_2500y84p).dissolve("t50_fid").reset_index() 
        hospital_data_clipped_2500y84p = gpd.clip(hospital_data, polygon_2500y84p).dissolve("facility_i").reset_index() 
        school_data_clipped_2500y84p = gpd.clip(school_data, polygon_2500y84p).dissolve("facility_i").reset_index() 
        tank_data_clipped_2500y84p = gpd.clip(tank_data, polygon_2500y84p).dissolve("t50_fid").reset_index() 

        print(f"Assets clipped to 2500y84p polygon in subfolder {subfolder}.")

        # Save the 2500y84p clipped assets and append to results DataFrame
        extracted_data = {'region': os.path.basename(subfolder_path), 'period': '2500', 'percent': '84'}
        os.makedirs(output_directory, exist_ok=True)

        save_clipped_data(road_data_clipped_2500y84p, "Roads", output_directory, extracted_data)
        save_clipped_data(building_data_clipped_2500y84p, "Buildings", output_directory, extracted_data)
        save_clipped_data(rail_data_clipped_2500y84p, "Rails", output_directory, extracted_data)
        save_clipped_data(bridge_data_clipped_2500y84p, "Bridges", output_directory, extracted_data)
        save_clipped_data(airport_data_clipped_2500y84p, "Airports", output_directory, extracted_data)
        save_clipped_data(hospital_data_clipped_2500y84p, "Hospitals", output_directory, extracted_data)
        save_clipped_data(school_data_clipped_2500y84p, "Schools", output_directory, extracted_data)
        save_clipped_data(tank_data_clipped_2500y84p, "Tanks", output_directory, extracted_data)

        # Create and append the results DataFrame for 2500y84p
        results_df_2500y84p = pd.DataFrame([{
            'Region': extracted_data.get('region', 'Unknown'),
            'Period': extracted_data.get('period', '2500'),
            'Percent': extracted_data.get('percent', '84'),
            'Road_Length_km': road_data_clipped_2500y84p.length.sum() / 1000,
            'Building_Count': len(building_data_clipped_2500y84p),
            'Rail_Length_km': rail_data_clipped_2500y84p.length.sum() / 1000,
            'Bridge_Count': len(bridge_data_clipped_2500y84p),
            'Airport_Count': len(airport_data_clipped_2500y84p),
            'Hospital_Count': len(hospital_data_clipped_2500y84p),
            'School_Count': len(school_data_clipped_2500y84p),
            'Tank_Count': len(tank_data_clipped_2500y84p),
        }])

        all_results_df = pd.concat([all_results_df, results_df_2500y84p], ignore_index=True)

        # Now process each of the other inundation polygons in this subfolder
        for root, _, files in os.walk(subfolder_path):
            for file in files:
                if file.endswith(".gpkg") and "2500y84p" not in file:
                    full_path = os.path.join(root, file)
                    print(f"Processing file: {full_path}")

                    extracted_data = extract_file_data(full_path, root)
                    if extracted_data is None:
                        print(f"File path does not match pattern: {full_path}")
                        continue

                    inundation_polygon = gpd.read_file(full_path).to_crs("EPSG:2193")
                    inundation_polygon.sindex

                    # Clip the 2500y84p clipped assets with the current inundation polygon
                    road_data_clipped = gpd.clip(road_data_clipped_2500y84p, inundation_polygon)
                    building_data_clipped = gpd.clip(building_data_clipped_2500y84p, inundation_polygon)
                    rail_data_clipped = gpd.clip(rail_data_clipped_2500y84p, inundation_polygon)
                    bridge_data_clipped = gpd.clip(bridge_data_clipped_2500y84p, inundation_polygon)
                    airport_data_clipped = gpd.clip(airport_data_clipped_2500y84p, inundation_polygon)
                    hospital_data_clipped = gpd.clip(hospital_data_clipped_2500y84p, inundation_polygon)
                    school_data_clipped = gpd.clip(school_data_clipped_2500y84p, inundation_polygon)
                    tank_data_clipped = gpd.clip(tank_data_clipped_2500y84p, inundation_polygon)

                    # Save the further clipped assets
                    save_clipped_data(road_data_clipped, "Roads", output_directory, extracted_data)
                    save_clipped_data(building_data_clipped, "Buildings", output_directory, extracted_data)
                    save_clipped_data(rail_data_clipped, "Rails", output_directory, extracted_data)
                    save_clipped_data(bridge_data_clipped, "Bridges", output_directory, extracted_data)
                    save_clipped_data(airport_data_clipped, "Airports", output_directory, extracted_data)
                    save_clipped_data(hospital_data_clipped, "Hospitals", output_directory, extracted_data)
                    save_clipped_data(school_data_clipped, "Schools", output_directory, extracted_data)
                    save_clipped_data(tank_data_clipped, "Tanks", output_directory, extracted_data)

                    # Create and append the results DataFrame for the current polygon
                    results_df = pd.DataFrame([{
                        'Region': extracted_data.get('region', 'Unknown'),
                        'Period': extracted_data.get('period', 'Unknown'),
                        'Percent': extracted_data.get('percent', 'Unknown'),
                        'Road_Length_km': road_data_clipped.length.sum() / 1000,
                        'Building_Count': len(building_data_clipped),
                        'Rail_Length_km': rail_data_clipped.length.sum() / 1000,
                        'Bridge_Count': len(bridge_data_clipped),
                        'Airport_Count': len(airport_data_clipped),
                        'Hospital_Count': len(hospital_data_clipped),
                        'School_Count': len(school_data_clipped),
                        'Tank_Count': len(tank_data_clipped),
                    }])

                    all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)

        # Save the combined results DataFrame for the current subfolder
        # Save the combined results DataFrame
        output_combined_csv_path = os.path.join(output_directory, f"{extracted_data['region']}_Infrastructure_Metrics_Combined.csv")
        all_results_df.to_csv(output_combined_csv_path, index=False)
        print(f"Combined results saved to {output_combined_csv_path}")
