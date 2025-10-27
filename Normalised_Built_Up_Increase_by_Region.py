# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 10:17:46 2024

@author: OEM
"""

import pandas as pd
import matplotlib.pyplot as plt
import itertools

# Load your DataFrame
df = pd.read_csv('D:/Nationwide_Tsunami_Inundation/Clipped_Land_Covers_Regions/Combined_Clipped_Land_Cover_Regions.csv')

# Define the events
events = ['H100y50p', 'H250y50p', 'H500y50p', 'H1000y50p', 'H1500y50p', 'H2000y50p', 'H2500y50p']

# Define custom labels for the x-axis
custom_labels = ['100', '250', '500', '1000', '1500', '2000', '2500']

# Define the order of regions from south to north
regions_order = [
    'Southland', 'Otago', 'Canterbury', 'West Coast', 'Marlborough', 'Nelson', 'Tasman', 
    'Wellington', 'Manawatu-Whanganui', 'Taranaki', 'Hawke\'s Bay', 'Gisborne', 
    'Bay of Plenty', 'Waikato', 'Auckland', 'Northland'
]

# Define land covers to exclude
exclude_land_covers = [
    'Estuarine Open Water', 'River', 'Lake or Pond', 'Harbour', 'Not Land', 'Total All Land Cover'
]

# Remove unwanted land covers from the DataFrame
df = df[~df['LandCoverType'].isin(exclude_land_covers)]

# Define groups and their corresponding land covers
groups = {
    'Bare & urban open': ['Urban Parkland/Open Space', 'Surface Mine or Dump', 'Sand or Gravel', 'Gravel or Rock', 'Landslide', 'Transport Infrastructure'],
    'Low vegetation': ['Alpine Grass/Herbfield', 'Sub Alpine Shrubland', 'Short-rotation Cropland', 'Orchard, Vineyard or Other Peren', 'High Producing Exotic Grassland', 'Low Producing Grassland', 'Depleted Grassland', 'Tall Tussock Grassland'],
    'Tall vegetation & scrub': ['Fernland', 'Flaxland', 'Gorse and/or Broom', 'Manuka and/or Kanuka', 'Broadleaved Indigenous Hardwoods', 'Deciduous Hardwoods', 'Mixed Exotic Shrubland', 'Matagouri or Grey Scrub', 'Forest - Harvested', 'Indigenous Forest', 'Exotic Forest'],
    'Built area': ['Built-up Area (settlement)']
}

# Convert the columns to strings and then concatenate
df['Event'] = 'H' + df['Return_Period'].astype(str) + 'y' + df['Percentile'].astype(str) + 'p'

# Pivot the DataFrame so that land cover types become columns
df_pivoted = df.pivot_table(index=['Region', 'Event'], columns='LandCoverType', values='total_area_km2', fill_value=0).reset_index()

# Initialize an empty list to store the normalized dataframes for each event
all_data = []

# Loop through each event to normalize the land cover data
for event in events:
    df_event = df_pivoted[df_pivoted['Event'] == event].copy()

    # Ensure 'Region' is categorical and ordered
    df_event['Region'] = pd.Categorical(df_event['Region'], categories=regions_order, ordered=True)
    df_event = df_event.sort_values('Region')
    # Reassign 'Region' as an index and add the 'Event' column
    df_event['Region'] = df_event['Region'].values
    df_event['Event'] = event
    df_event = df_event.set_index(['Region', 'Event'])
    all_data.append(df_event)
    
df_all_data = pd.concat(all_data)   
df_all_adjusted = df_all_data[['Built-up Area (settlement)']].copy()

# Normalize the data so that the value at the 2500y event is 100%
for region in df_all_adjusted.index.get_level_values('Region').unique():
    # Isolate data for the current region
    region_df = df_all_adjusted.loc[region].copy()  # This isolates the region-level data
    
    # Check if the region has data for the 2500y event
    if 'H2500y50p' in region_df.index:
        # Get the value of Built-up Area (settlement) for the 2500y event
        value_2500y = region_df.loc['H2500y50p', 'Built-up Area (settlement)']
        
        # Ensure we don't divide by 0 or NaN
        if pd.notna(value_2500y) and value_2500y > 0:
            # Normalize the data for all events for this region
            region_df['Built-up Area (settlement)'] = (region_df['Built-up Area (settlement)'] / value_2500y) * 100
            
            # Reassign the normalized values back to the main DataFrame, using both Region and Event index
            for event in region_df.index:
                df_all_adjusted.loc[(region, event), 'Built-up Area (settlement)'] = region_df.loc[event, 'Built-up Area (settlement)']

# Initialize an empty dictionary to store lists of values for each region
region_values = {}

# Loop through each region and event to collect values into lists
for (region, event), row in df_all_adjusted.iterrows():
    if region not in region_values:
        region_values[region] = {}
    region_values[region][event] = row['Built-up Area (settlement)']

# Convert the dictionary to a DataFrame, where each region has a list of values for the events
df_region_values = pd.DataFrame.from_dict(region_values, orient='index')

# Add each event as a column for easier plotting
for event in events:
    df_region_values[event] = df_region_values.apply(lambda x: x[event], axis=1)

# Define a list of line styles and markers to ensure each region looks different
line_styles = ['-', '--', '-.', ':']
markers = ['o', 's', 'D', '^', 'v', 'P', '*', 'X', 'd']

# Create a list of all combinations of line styles and markers
styles = list(itertools.product(line_styles, markers))
colors = plt.cm.tab20.colors  # Use a colormap with sufficient colors

plt.figure(figsize=(18, 9))

# Convert custom_labels to numerical values for proper scaling on the x-axis
x_values = [100, 250, 500, 1000, 1500, 2000, 2500]

# Plot each region with a unique combination of line style, marker, and color
for i, (region, data) in enumerate(df_region_values.iterrows()):
    style, marker = styles[i % len(styles)]
    color = colors[i % len(colors)]
    plt.plot(x_values, data, linestyle=style, marker=marker, color=color, label=region, linewidth=3, markersize=13, alpha=0.9)

plt.xlabel('Return Period (year)', fontsize=20)
plt.ylabel('Built-up Inundation Area Normalised (%)', fontsize=20)
plt.xticks(x_values, fontsize=16)  # Set x-ticks with the numerical x_values
plt.yticks(fontsize=16)
plt.grid(True)

# Add a legend at the bottom with 8 columns
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=8, fontsize=15, columnspacing=0.4, frameon=False)

plt.tight_layout()

plt.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Built-Up_Normalised_2500_Adjusted.pdf', bbox_inches='tight')
plt.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Built-Up_Normalised_2500_Adjusted.jpeg', dpi=300, bbox_inches='tight')

plt.show()
