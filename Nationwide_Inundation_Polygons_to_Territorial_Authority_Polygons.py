import geopandas as gpd
import os
import time

# Define paths
nationwide_polygons_dir = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons_Nationwide"
territorial_authorities_shp = "D:/Nationwide_Tsunami_Inundation/statsnz-new-zealand-4layers-SHP/territorial-authority-2023-generalised/territorial-authority-2023-generalised.shp"
output_root_dir = "D:/Nationwide_Tsunami_Inundation/Inundation_Polygons_Territorial_Authority"

# Step 2: Load the territorial authorities shapefile
ta_gdf = gpd.read_file(territorial_authorities_shp)

# Step 3: Loop through each territorial authority
for index, ta_row in ta_gdf.iterrows():
    ta_name = ta_row['TA2023_V_1']  # Replace 'TA_NAME' with the correct column name in your shapefile
    ta_geometry = ta_row.geometry
    
    # Create a subfolder for each territorial authority
    ta_folder = os.path.join(output_root_dir, ta_name.replace(" ", "_"))
    os.makedirs(ta_folder, exist_ok=True)
    
    # Step 4: Loop through each nationwide polygon file
    for polygon_file in os.listdir(nationwide_polygons_dir):
        if polygon_file.endswith(".gpkg"):
            scenario_name = polygon_file.replace(".gpkg", "").replace("Nationwide_Inundation_", "")
            polygon_path = os.path.join(nationwide_polygons_dir, polygon_file)
            
            # Load the nationwide polygon
            nationwide_gdf = gpd.read_file(polygon_path)
            
            # Clip the nationwide polygon by the current territorial authority
            clipped_gdf = gpd.clip(nationwide_gdf, ta_geometry)
            
            # Step 5: Check if the clipped GeoDataFrame is empty and save if not
            if not clipped_gdf.empty:
                output_path = os.path.join(ta_folder, f"{scenario_name}_{ta_name}_Inundation_Polygon.gpkg")
                clipped_gdf.to_file(output_path, driver="GPKG")
                print(f"Saved clipped polygon for {scenario_name} in {ta_name}")
            else:
                print(f"No intersection for {scenario_name} in {ta_name}, skipping.")
