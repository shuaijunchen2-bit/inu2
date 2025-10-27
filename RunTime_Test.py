# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 15:19:04 2024

@author: OEM
"""

import os
import pandas as pd

# Define the root directory containing subfolders with CSV files
root_dir = "D:/Nationwide_Tsunami_Inundation/FABDEM_Latest_Inundation_Results"

# Create an empty DataFrame to hold all the merged data
mmerged_df = pd.DataFrame()

# Step 1: Loop through each subfolder in the root directory
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".csv"):
            # Step 2: Construct the full file path
            file_path = os.path.join(subdir, file)
            
            # Step 3: Extract the segment name from the filename
            segment_name = os.path.splitext(file)[0].replace('_', ' ').replace(' Data', '')
            
            # Step 4: Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            
            # Step 5: Add a new column to the DataFrame with the segment name
            df['Segment Name'] = segment_name
            
            # Step 6: Append the data to the merged DataFrame
            mmerged_df = pd.concat([mmerged_df, df], ignore_index=True)

# Define the root directory containing subfolders with CSV files
root_dir = "D:/Nationwide_Tsunami_Inundation/Latest_Inundation_Results"

# Create an empty DataFrame to hold all the merged data
merged_df = pd.DataFrame()

# Step 1: Loop through each subfolder in the root directory
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".csv"):
            # Step 2: Construct the full file path
            file_path = os.path.join(subdir, file)
            
            # Step 3: Extract the segment name from the filename
            segment_name = os.path.splitext(file)[0].replace('_', ' ').replace(' Data', '')
            
            # Step 4: Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            
            # Step 5: Add a new column to the DataFrame with the segment name
            df['Segment Name'] = segment_name
            
            # Step 6: Append the data to the merged DataFrame
            merged_df = pd.concat([merged_df, df], ignore_index=True)

# Combine the two DataFrames
combined_df = pd.concat([merged_df, mmerged_df])

# Identify duplicates based on specific columns and store them in a separate DataFrame
duplicates_df = combined_df[combined_df.duplicated(subset=['Return_Period', 'Percentile', 'Segment Name'], keep=False)]

# Remove duplicates from the original DataFrame
combined_df1 = combined_df.drop_duplicates(subset=['Return_Period', 'Percentile', 'Segment Name'])

# Optional: Reset the index of both DataFrames if needed
duplicates_df = duplicates_df.reset_index(drop=True)
combined_df1 = combined_df1.reset_index(drop=True)

output_file = "D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv"
combined_df1.to_csv(output_file, index=False)

# Step 1: Convert the 'Run_Time' column to a Timedelta object and then to seconds
combined_df1.loc[:, 'Run_Time'] = pd.to_timedelta(combined_df1['Run_Time']).dt.total_seconds()

# Step 2: Group by 'Return_Period' and 'Percentile' and sum the 'Run_Time' in seconds
summed_runtime_df = combined_df1.groupby(['Return_Period', 'Percentile']).agg({'Run_Time': 'sum'}).reset_index()

# Step 3: Display or save the result
print(summed_runtime_df)