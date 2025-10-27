import geopandas as gpd
import os

# Define the root folder containing territorial subfolders
root_folder = r"D:\Nationwide_Tsunami_Inundation\Territorial_Authority_Clipped_Assets"

# List of inundation events
inundation_events = [
    "100y50p", "100y84p",
    "250y50p", "250y84p",
    "500y50p", "500y84p",
    "1000y50p", "1000y84p",
    "1500y50p", "1500y84p",
    "2000y50p", "2000y84p",
    "2500y50p", "2500y84p"
    ]  # Add all events as needed

# List of asset types
asset_types = ["Roads", "Buildings", "Rails", "Bridges", "Airports", "Hospitals", "Schools", "Tanks"]

# Output folder to save merged national assets
output_folder = r"D:\Nationwide_Tsunami_Inundation\National_Clipped_Assets"

# Loop through each inundation event
for event in inundation_events:
    for asset in asset_types:
        national_gdf = None  # Initialize an empty GeoDataFrame to hold the merged data

        # Loop through each territorial authority subfolder
        for ta_subfolder in os.listdir(root_folder):
            ta_folder_path = os.path.join(root_folder, ta_subfolder)
            asset_folder_path = os.path.join(ta_folder_path, asset)

            # Check if the asset folder exists
            if os.path.exists(asset_folder_path):
                # Locate the gpkg file for the current event
                gpkg_file = os.path.join(asset_folder_path, f"Clipped_{asset}_H{event}.gpkg")
                
                # Check if the gpkg file exists
                if os.path.exists(gpkg_file):
                    # Read the gpkg file
                    gdf = gpd.read_file(gpkg_file)

                    # Merge with the national GeoDataFrame
                    if national_gdf is None:
                        national_gdf = gdf
                    else:
                        national_gdf = national_gdf.append(gdf, ignore_index=True)

        # After merging all territorial authority data for the current asset and event
        if national_gdf is not None:
            # Save the merged national asset file
            output_gpkg = os.path.join(output_folder, f"{asset}_{event}_National.gpkg")
            national_gdf.to_file(output_gpkg, driver="GPKG")

print("Merging complete!")
