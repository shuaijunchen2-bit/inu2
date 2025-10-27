# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 17:01:00 2024

@author: OEM
"""

import geopandas as gpd
import os

# Load territorial authority boundaries
ta_boundaries = gpd.read_file("D:/Nationwide_Tsunami_Inundation/statsnz-new-zealand-4layers-SHP/territorial-authority-2023-generalised/territorial-authority-2023-generalised.shp").to_crs("EPSG:2193")

# Load national infrastructure data
road_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/nz-roads.shp").to_crs("EPSG:2193")
building_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-building-outlines/nz-building-outlines.shp").to_crs("EPSG:2193")
rail_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-railway-centrelines-topo-150k/nz-railway-centrelines-topo-150k.shp").to_crs("EPSG:2193")
bridge_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/lds-nz-bridge-centrelines-topo-150k-SHP/nz-bridge-centrelines-topo-150k.shp").to_crs("EPSG:2193")
airport_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-airport-polygons-topo-150k/nz-airport-polygons-topo-150k.shp").to_crs("EPSG:2193")
hospital_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-hospital/nz-hospital.shp").to_crs("EPSG:2193")
school_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-schools/nz-schools.shp").to_crs("EPSG:2193")
tank_data = gpd.read_file("D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-tank-polygons-topo-150k/nz-tank-polygons-topo-150k.shp").to_crs("EPSG:2193")

# Create a dictionary to store the results
results = {}

# Function to aggregate data by territorial authority
def aggregate_by_ta(ta_boundaries, infrastructure_data, column_name, is_line=False):
    # Perform spatial join
    joined = gpd.sjoin(infrastructure_data, ta_boundaries, how="inner", op='intersects')
    
    if is_line:
        # Calculate the total length for line data
        aggregated = joined.groupby("TA2023_V_1").apply(lambda x: x.length.sum())
    else:
        # Calculate the total count for point or polygon data
        aggregated = joined.groupby("TA2023_V_1").size()
    
    # Store results in the dictionary
    results[column_name] = aggregated

# Aggregate road lengths by territorial authority
aggregate_by_ta(ta_boundaries, road_data, "Road_Length_m", is_line=True)

# Aggregate rail lengths by territorial authority
aggregate_by_ta(ta_boundaries, rail_data, "Rail_Length_m", is_line=True)

# Aggregate building counts by territorial authority
aggregate_by_ta(ta_boundaries, building_data, "Building_Count")

# Aggregate bridge counts by territorial authority
aggregate_by_ta(ta_boundaries, bridge_data, "Bridge_Count")

# Aggregate airport counts by territorial authority
aggregate_by_ta(ta_boundaries, airport_data, "Airport_Count")

# Aggregate hospital counts by territorial authority
aggregate_by_ta(ta_boundaries, hospital_data, "Hospital_Count")

# Aggregate school counts by territorial authority
aggregate_by_ta(ta_boundaries, school_data, "School_Count")

# Aggregate tank counts by territorial authority
aggregate_by_ta(ta_boundaries, tank_data, "Tank_Count")

# Combine the results into a single GeoDataFrame
results_df = ta_boundaries[["TA2023_V_1"]].copy()

for key, value in results.items():
    results_df = results_df.merge(value.rename(key), left_on="TA2023_V_1", right_index=True, how="left")

# Save the results as a GeoPackage
output_file = "D:/Nationwide_Tsunami_Inundation/Infrastructure_TA_Aggregates.csv"
results_df.to_csv(output_file)

print(f"Results saved to {output_file}")
