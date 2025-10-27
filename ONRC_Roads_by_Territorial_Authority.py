import geopandas as gpd
import pandas as pd

# Load the shapefiles
roads_gdf = gpd.read_file('D:/Nationwide_Tsunami_Inundation/Infrastructure/nz-roads-ONRC-classification/nz-roads.shp')
ta_gdf = gpd.read_file('D:/Nationwide_Tsunami_Inundation/statsnz-new-zealand-4layers-SHP/territorial-authority-2023-generalised/territorial-authority-2023-generalised.shp')

# Ensure both shapefiles are in the same CRS
roads_gdf = roads_gdf.to_crs(ta_gdf.crs)

# Perform a spatial join to determine which roads are within each territorial authority
joined_gdf = gpd.sjoin(roads_gdf, ta_gdf, how='inner', op='intersects')

# Calculate the length of each road segment
joined_gdf['Length'] = joined_gdf.geometry.length

# Combine "National" and "High Volume" into one category
joined_gdf['ONRCClass'] = joined_gdf['ONRCClass'].replace(['National', 'High Volume'], 'National + High Volume')

# Combine "Access" and "Low Volume" into one category
joined_gdf['ONRCClass'] = joined_gdf['ONRCClass'].replace(['Access', 'Low Volume'], 'Access + Low Volume')

# Group by Territorial Authority and the combined ONRCClass, then sum the lengths
lengths_df = joined_gdf.groupby(['TA2023_V_1', 'ONRCClass'])['Length'].sum().reset_index()

# Save the results to a DataFrame
lengths_df = pd.DataFrame(lengths_df)

# Print or save the dataframe as needed
print(lengths_df)

# Optionally, save the dataframe to a CSV file
lengths_df.to_csv('D:/Nationwide_Tsunami_Inundation/Infrastructure/Roads_ONRCClass_Lengths_By_TA.csv', index=False)
