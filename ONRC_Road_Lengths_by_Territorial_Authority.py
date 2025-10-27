import os
import pandas as pd
import geopandas as gpd

# Set your main directory containing the territorial authority folders
main_dir = 'D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Clipped_Assets'

# Set the output directory where the merged files will be saved
output_dir = 'D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Roads/'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

all_roads = []

# Iterate through each territorial authority folder
for ta_folder in os.listdir(main_dir):
    ta_path = os.path.join(main_dir, ta_folder)
    
    # Ensure the folder exists and contains a 'Roads' subfolder
    roads_folder = os.path.join(ta_path, 'Roads')
    if os.path.exists(roads_folder):
        
        # Iterate through each .gpkg file in the 'Roads' subfolder
        for gpkg_file in os.listdir(roads_folder):
            if gpkg_file.endswith('.gpkg'):
                # Read the geopackage file
                gpkg_path = os.path.join(roads_folder, gpkg_file)
                gdf = gpd.read_file(gpkg_path)
                
                # Retain only the specified columns and geometry
                gdf = gdf[['ONRCClass', 'surfaceTyp', 'geometry']]
                
                # Combine "National" and "High Volume" into one category
                gdf['ONRCClass'] = gdf['ONRCClass'].replace(['National', 'High Volume'], 'National + High Volume')
                
                # Combine "Access" and "Low Volume" into one category
                gdf['ONRCClass'] = gdf['ONRCClass'].replace(['Access', 'Low Volume'], 'Access + Low Volume')
                
                # Extract the event from the filename (e.g., "Clipped_Roads_H100y50p.gpkg")
                event_name = gpkg_file.replace('Clipped_Roads_', '').replace('.gpkg', '')
                
                # Add columns for territorial authority and event
                gdf['Territorial_Authority'] = ta_folder
                gdf['Event'] = event_name
                
                # Append the GeoDataFrame to the list
                all_roads.append(gdf)

# After processing all territories, merge all the GeoDataFrames
if all_roads:
    merged_gdf = gpd.GeoDataFrame(pd.concat(all_roads, ignore_index=True))
    
    # Dissolve the GeoDataFrame based on Territorial_Authority and Event
    dissolved_gdf = merged_gdf.dissolve(by=['Territorial_Authority', 'Event', 'ONRCClass'], as_index=False)
    
    dissolved_gdf['Length_km'] = dissolved_gdf.geometry.length/1000
    
    # Define the output filename
    output_file = 'Merged_All_Territories_Roads.gpkg'
    output_path = os.path.join(output_dir, output_file)
    
    # Save the merged GeoDataFrame to a new .gpkg file
    dissolved_gdf.to_file(output_path, driver='GPKG')

print("Merging completed successfully!")
