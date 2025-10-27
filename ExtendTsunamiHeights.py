# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 15:11:14 2024

@author: tatek
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from scipy.optimize import curve_fit

# Power model function
def power_model(x, a, b):
    return a * np.power(x, b)

# Function to fit models and interpolate the results
def fit_and_interpolate(flows, flow_values):
    popt, pcov = curve_fit(power_model, flows, flow_values, maxfev=10000)
    interpolated_values = {f'H{flow}y': power_model(flow, *popt) for flow in [250, 1500, 2000]}
    return interpolated_values

# Function to analyze the shapefile
def analyze_shapefile(shapefile_path):
    gdf = gpd.read_file(shapefile_path)
    flows = [100, 500, 1000, 2500]
    results_list = []

    for index, row in gdf.iterrows():
        sectn_name = row['SECTN_NAME']
        result = {'OBJECTID': row['OBJECTID'], 'SECTN_NAME': sectn_name}
        
        for percentile in ['50p', '84p']:
            flow_values = [row[f'H{flow}y{percentile}'] for flow in flows]
            
            interpolated_power = fit_and_interpolate(flows, flow_values)
            
            # Include original values for existing flows
            for flow in flows:
                result[f'H{flow}y{percentile}'] = row[f'H{flow}y{percentile}']
                
            # Include interpolated values for new return periods
            for key, value in interpolated_power.items():
                result[f'{key}{percentile}'] = value

        results_list.append(result)

    results_df = pd.DataFrame(results_list)
    
    # Merge results_df with gdf using concat to avoid column conflicts
    results_gdf = pd.concat([gdf.set_index(['OBJECTID', 'SECTN_NAME']), results_df.set_index(['OBJECTID', 'SECTN_NAME'])], axis=1).reset_index()

    # Remove duplicated columns if any
    results_gdf = results_gdf.loc[:, ~results_gdf.columns.duplicated()]

    # Define the correct order for the new columns
    new_cols_50p = [f'H{flow}y50p' for flow in [100, 250, 500, 1000, 1500, 2000, 2500]]
    new_cols_84p = [f'H{flow}y84p' for flow in [100, 250, 500, 1000, 1500, 2000, 2500]]

    # Ensure that all columns in new_cols are in results_gdf
    all_new_cols = new_cols_50p + new_cols_84p
    for col in all_new_cols:
        if col not in results_gdf.columns:
            results_gdf[col] = np.nan

    # Order columns correctly
    existing_cols = [col for col in results_gdf.columns if col not in all_new_cols and col not in ['OBJECTID', 'SECTN_NAME', 'geometry']]
    ordered_cols = ['OBJECTID', 'SECTN_NAME'] + existing_cols + new_cols_50p + new_cols_84p + ['geometry']
    results_gdf = results_gdf[ordered_cols]

    return results_gdf

# Example usage
shapefile_path = 'C:/Users/tatek/OneDrive/Desktop/National Run/TsunamiZones2021/Shapefiles2021/TsunamiHazard2021.shp'  # Update the path to your shapefile
results_gdf = analyze_shapefile(shapefile_path)
print(results_gdf.head())

# Save the results as a new shapefile
output_path = 'C:/Users/tatek/OneDrive/Desktop/National Run/TsunamiZones2021/Shapefiles2021/TsunamiHazard2021_Updated.shp'  # Update the path to your output shapefile
results_gdf.to_file(output_path)
