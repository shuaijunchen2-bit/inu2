import geopandas as gpd
import os
import pandas as pd

# Paths to the directories and files
inundation_folder = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons_Nationwide"

# Load the asset data
bridge_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/lds-nz-bridge-centrelines-topo-150k-SHP/nz-bridge-centrelines-topo-150k.shp").to_crs("EPSG:2193")
airport_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-airport-polygons-topo-150k/nz-airport-polygons-topo-150k.shp").to_crs("EPSG:2193")
hospital_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-hospital/nz-hospital.shp").to_crs("EPSG:2193")
school_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-schools/nz-schools.shp").to_crs("EPSG:2193")
tank_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-tank-polygons-topo-150k/nz-tank-polygons-topo-150k.shp").to_crs("EPSG:2193")

# Combine all assets into a dictionary for easier processing
assets = {
    "bridges": bridge_data,
    "airports": airport_data,
    "hospitals": hospital_data,
    "schools": school_data,
    "tanks": tank_data
}

# Output folder for the processed GeoPackages
output_folder = "D:/Nationwide_Tsunami_Inundation/Processed_Assets"

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Function to process each asset type
def process_asset(asset_data, asset_name):
    # Create new columns to track the number of inundation polygons each asset intersects with
    asset_data["Exposure Count"] = 0
    asset_data["Inundation Events"] = [[] for _ in range(len(asset_data))]
    
    # Loop through each inundation polygon file
    for file_name in os.listdir(inundation_folder):
        if file_name.endswith(".gpkg"):
            print(file_name)
            # Extract the event name from the file name (e.g., "100y50p", "2500y84p")
            event_name = os.path.splitext(file_name)[0]
            
            # Load the inundation polygon
            inundation_path = os.path.join(inundation_folder, file_name)
            inundation_polygon = gpd.read_file(inundation_path)

            # Perform the spatial join to find intersections
            joined = gpd.sjoin(asset_data, inundation_polygon, predicate='intersects')

            if not joined.empty:
                # Increment the exposure count for each asset
                asset_data.loc[joined.index, "Exposure Count"] += 1
                
                # Record the inundation event name for each intersected asset
                for idx in joined.index:
                    asset_data.at[idx, "Inundation Events"].append(event_name)

    # Convert the Inundation Events list to a string for easier reading in QGIS
    asset_data["Inundation Events"] = asset_data["Inundation Events"].apply(lambda x: ', '.join(x))

    # Save the results as a GeoPackage
    output_file = os.path.join(output_folder, f"{asset_name}_Exposure.gpkg")
    asset_data.to_file(output_file, driver="GPKG")

    print(f"Processed and saved: {output_file}")

# Process each asset type and save the results
for asset_name, asset_data in assets.items():
    print(asset_name)
    process_asset(asset_data, asset_name)
