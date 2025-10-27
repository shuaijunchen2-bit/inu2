import geopandas as gpd
import pandas as pd
import os
import re
import time
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection

# List of regions to process
Regions_of_Files = [
    'Southland', 'Otago', 'Canterbury', 'West Coast', 'Marlborough', 'Nelson', 'Tasman', 
    'Wellington', 'Manawatu-Whanganui', 'Taranaki', 'Hawke\'s Bay', 'Gisborne', 
    'Bay of Plenty', 'Waikato', 'Auckland', 'Northland'
]

# Define the path to the base directories
base_inundation_directory = 'D:/Nationwide_Tsunami_Inundation/Inundation_Polygons'
base_landcover_shapefile_path = 'D:/Nationwide_Tsunami_Inundation/lris-lcdb-v50-land-cover-database-version-50-mainland-new-zealand-SHP/Nationwide_Land_Covers/Merged_Nationwide_Land_Covers.shp'
base_output_directory = 'D:/Nationwide_Tsunami_Inundation/Clipped_Land_Covers_Regions'

# Ensure the base output directory exists
os.makedirs(base_output_directory, exist_ok=True)

# Regex pattern to extract return period and percentile
pattern = r"Entire_H(?P<return_period>\d+)y(?P<percentile>\d+)p_Inundation_Polygon"

# Load the land cover shapefile
landcover_gdf = gpd.read_file(base_landcover_shapefile_path)

# Function to ensure geometries are Polygon or MultiPolygon
def ensure_polygon_or_multipolygon(gdf):
    def convert_geometry(geom):
        if isinstance(geom, (Polygon, MultiPolygon)):
            return geom
        elif isinstance(geom, GeometryCollection):
            # Extract only polygons or multipolygons from the GeometryCollection
            polygons = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
            if len(polygons) == 1:
                return polygons[0]
            elif len(polygons) > 1:
                return MultiPolygon(polygons)
        return None  # Return None if geometry is not Polygon or MultiPolygon

    gdf['geometry'] = gdf['geometry'].apply(convert_geometry)
    return gdf.dropna(subset=['geometry'])

# Process each region
for Region in Regions_of_Files:
    # Reset the cumulative dataframe for the new region
    cumulative_results_df = pd.DataFrame()

    # Define the paths for the current region
    inundation_directory = os.path.join(base_inundation_directory, f"{Region}_region")
    output_directory = os.path.join(base_output_directory, f"{Region}_region")
    
    # Ensure the output directory exists for the current region
    os.makedirs(output_directory, exist_ok=True)
    
    # List all the inundation GPKG files for the current region
    inundation_files = [f for f in os.listdir(inundation_directory) if f.endswith('.gpkg')]
    
    # Process each inundation file in the current region
    for inundation_file in inundation_files:
        inundation_path = os.path.join(inundation_directory, inundation_file)
        inundation_gdf = gpd.read_file(inundation_path)

        # Ensure both GeoDataFrames are in the same CRS
        if landcover_gdf.crs != inundation_gdf.crs:
            inundation_gdf = inundation_gdf.to_crs(landcover_gdf.crs)

        # Extract return period and percentile from filename
        match = re.search(pattern, inundation_file)
        if match:
            return_period = match.group("return_period")
            percentile = match.group("percentile")
        else:
            print(f"Filename {inundation_file} does not match expected pattern.")
            continue
        
        # Clip the land cover data by the inundation polygon
        clipped_landcover = gpd.clip(landcover_gdf, inundation_gdf)
        clipped_landcover = clipped_landcover[['Name_2018', 'Class_2018', 'Roughness_', 'geometry']]
        
        # Ensure geometries are either Polygon or MultiPolygon
        clipped_landcover = ensure_polygon_or_multipolygon(clipped_landcover)
        
        # If the clipped GeoDataFrame is empty, skip further processing
        if clipped_landcover.empty:
            print(f"No overlap found for {inundation_file} in {Region}.")
            continue

        # Calculate area for each feature in km² and append it as a new column
        clipped_landcover['Area_km2'] = clipped_landcover.area / 1e6  # Convert m² to km²
        
        # Construct the output file path for clipped land cover
        file_name = f'Clipped_{Region}_LandCover_{os.path.splitext(inundation_file)[0]}.gpkg'
        clipped_output_path = os.path.join(output_directory, file_name)
        
        # Debug: Print the constructed output path
        print(f"Saving clipped land cover to: {clipped_output_path}")
        
        # Save the clipped land cover to a new GeoPackage file with area information
        try:
            clipped_landcover.to_file(clipped_output_path, driver="GPKG")
        except Exception as e:
            print(f"Error saving {clipped_output_path}: {e}")
            continue
        
        # Calculate the total area of each land cover type within the inundation zone
        landcover_areas = []
        total_area_km2_all_landcover = clipped_landcover['Area_km2'].sum()
        
        for landcover_type in clipped_landcover['Name_2018'].unique():
            landcover_type_gdf = clipped_landcover[clipped_landcover['Name_2018'] == landcover_type]
            total_area_km2 = landcover_type_gdf['Area_km2'].sum()
            landcover_areas.append({
                'Region': Region,
                'inundation_file': inundation_file,
                'Return_Period': return_period,
                'Percentile': percentile,
                'LandCoverType': landcover_type,
                'total_area_km2': total_area_km2
            })
        
        # Add the total area of all land cover as a separate row
        landcover_areas.append({
            'Region': Region,
            'inundation_file': inundation_file,
            'Return_Period': return_period,
            'Percentile': percentile,
            'LandCoverType': 'Total All Land Cover',
            'total_area_km2': total_area_km2_all_landcover
        })
        
        # Append the results to the cumulative dataframe
        results_df = pd.DataFrame(landcover_areas)
        cumulative_results_df = pd.concat([cumulative_results_df, results_df], ignore_index=True)

        # Print the results
        print(f"Results for {inundation_file} in {Region}:")
        for landcover_area in landcover_areas:
            print(f"Land cover type: {landcover_area['LandCoverType']}, Total area (km²): {landcover_area['total_area_km2']}")
    
    # Save the cumulative results for the current region to a CSV file
    cumulative_results_csv_path = os.path.join(output_directory, f'Cumulative_Results_{Region}.csv')
    cumulative_results_df.to_csv(cumulative_results_csv_path, index=False)

    print(f"Cumulative results saved to {cumulative_results_csv_path} for region {Region}")

