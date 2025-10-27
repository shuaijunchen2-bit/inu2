# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 10:51:25 2024

@author: OEM
"""

import os
import pandas as pd

# Define the root directory containing subfolders with CSV files
root_dir = "D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Clipped_Assets"

# Create an empty DataFrame to hold all the merged data
merged_df = pd.DataFrame()

# Step 1: Loop through each subfolder in the root directory
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".csv"):
            # Step 2: Construct the full file path
            file_path = os.path.join(subdir, file)
            
            # Step 3: Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            
            # Step 4: Append the data to the merged DataFrame
            merged_df = pd.concat([merged_df, df], ignore_index=True)

# Step 5: Save the merged DataFrame to a single CSV file
output_file = "D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Clipped_Assets/Combined_Territorial_Authority_Clipped_Assets.csv"
merged_df.to_csv(output_file, index=False)

print(f"Merged CSV file saved to {output_file}")
