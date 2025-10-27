import geopandas as gpd
import pandas as pd
import os
import time

time.sleep(3600)

# Define the root directory containing the region subfolders
root_dir = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons"

# Define the return periods and percentiles
return_periods = [100, 250, 500, 1000, 1500, 2000, 2500]
percentiles = [50, 84]

# Step 1: Loop through each scenario
for rp in return_periods:
    for p in percentiles:
        scenario_name = f"H{rp}y{p}p"
        
        # Create an empty GeoDataFrame to hold merged polygons for the scenario
        scenario_gdf = gpd.GeoDataFrame()

        # Step 2: Loop through each region folder
        for region_folder in os.listdir(root_dir):
            region_path = os.path.join(root_dir, region_folder)

            if os.path.isdir(region_path):
                # Step 3: Find the file that contains the scenario name
                for file in os.listdir(region_path):
                    if scenario_name in file and file.endswith(".gpkg"):
                        file_path = os.path.join(region_path, file)
                        
                        # Read the gpkg file for the current scenario
                        gdf = gpd.read_file(file_path)

                        # Merge the polygons in the scenario
                        scenario_gdf = gpd.GeoDataFrame(pd.concat([scenario_gdf, gdf], ignore_index=True))

        # Step 4: Dissolve the scenario polygons into a single polygon
        if not scenario_gdf.empty:
            dissolved_gdf = scenario_gdf.dissolve()

            # Step 5: Save the dissolved nationwide polygon for the scenario
            output_path = f"D:/Nationwide_Tsunami_Inundation/Inundation_Polygons/Nationwide_Inundation_{scenario_name}.gpkg"
            dissolved_gdf.to_file(output_path, driver="GPKG")

            print(f"Nationwide inundation polygon for scenario {scenario_name} created and dissolved successfully.")
        else:
            print(f"No files found for scenario {scenario_name}.")
