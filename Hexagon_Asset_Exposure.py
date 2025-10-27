import geopandas as gpd
import os

# Load the hexagon grid
hexagon_grid = gpd.read_file(r"D:\Nationwide_Tsunami_Inundation\Methodology_Article_Variables\NZ_Hexagons.shp")

# Folder where merged nationwide assets are stored
assets_folder = r"D:\Nationwide_Tsunami_Inundation\National_Clipped_Assets"

# Define asset types and their geometry types
asset_types = {
    "Roads": "line",       # Lines (including multilines)
    "Buildings": "polygon", # Polygons
    "Rails": "line",       # Lines
    "Bridges": "count",    # Count as number of bridges within each hexagon
    "Airports": "polygon",  # Polygons
    "Hospitals": "polygon", # Polygons
    "Schools": "polygon",   # Polygons
    "Tanks": "polygon"      # Polygons
}

# List of inundation scenarios to process
inundation_events = [
    "100y50p", "100y84p",
    "250y50p", "250y84p",
    "500y50p", "500y84p",
    "1000y50p", "1000y84p",
    "1500y50p", "1500y84p",
    "2000y50p", "2000y84p",
    "2500y50p", "2500y84p"
]

# Loop through each inundation scenario
for event in inundation_events:
    for asset, geom_type in asset_types.items():
        asset_file = os.path.join(assets_folder, f"{asset}_{event}_National.gpkg")
        
        if os.path.exists(asset_file):
            # Load the asset data
            asset_gdf = gpd.read_file(asset_file)
            asset_gdf = asset_gdf.to_crs(hexagon_grid.crs)
            
            if geom_type == 'line':
                # Calculate the total length of line assets (including multilines) within each hexagon
                hexagon_grid[f'{asset}_{event}_Length'] = hexagon_grid.geometry.apply(
                    lambda hex_geom: asset_gdf[asset_gdf.intersects(hex_geom)].length.sum()
                )
            elif geom_type == 'polygon':
                # Calculate the total number of polygon assets within each hexagon
                hexagon_grid[f'{asset}_{event}_Count'] = hexagon_grid.geometry.apply(
                    lambda hex_geom: asset_gdf[asset_gdf.intersects(hex_geom)].shape[0]
                )
            elif geom_type == 'count':
                # Count the number of line assets (like bridges) within each hexagon
                hexagon_grid[f'{asset}_{event}_Count'] = hexagon_grid.geometry.apply(
                    lambda hex_geom: asset_gdf[asset_gdf.intersects(hex_geom)].shape[0]
                )

# Correct the output file path by removing the duplicated directory
output_file = r"D:\Nationwide_Tsunami_Inundation\Methodology_Article_Variables\NZ_Hexagons_with_All_Assets.gpkg"

# Save the updated hexagon grid with the original column names as a GeoPackage (GPKG)
hexagon_grid.to_file(output_file, driver='GPKG')

print(f"Hexagon grid with asset data saved to {output_file}")