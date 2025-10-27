import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Load your DataFrame
df = pd.read_csv('D:/Nationwide_Tsunami_Inundation/Clipped_Land_Covers_Regions/Combined_Clipped_Land_Cover_Regions.csv')

# Define the events
events = ['H100y50p', 'H500y50p', 'H2500y50p']

events_title = ['a)', 'b)', 'c)']

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

# Pastel color maps
pastel_colors = {
    'Bare & urban open': plt.cm.Blues,
    'Low vegetation': plt.cm.Greens,
    'Tall vegetation & scrub': plt.cm.Oranges,
    'Built area': '#FFD700'  # Use a specific yellow color code for Built area
}

# Function to generate shades of a pastel color map
def generate_shades(colormap, num_shades, start=0.1, end=0.9):
    if isinstance(colormap, str):
        return [colormap] * num_shades  # If colormap is a single color, repeat it
    return [colormap(start + (end - start) * (i / num_shades)) for i in range(num_shades)]

# Generate pastel shades for each land cover type
land_cover_to_color = {}
for group, covers in groups.items():
    shades = generate_shades(pastel_colors[group], len(covers), start=0.2, end=0.8)
    land_cover_to_color.update(dict(zip(covers, shades)))

# Convert the columns to strings and then concatenate
df['Event'] = 'H' + df['Return_Period'].astype(str) + 'y' + df['Percentile'].astype(str) + 'p'

# Pivot the DataFrame so that land cover types become columns
df_pivoted = df.pivot_table(index=['Region', 'Event'], columns='LandCoverType', values='total_area_km2', fill_value=0).reset_index()

# Prepare the plot
fig, axes = plt.subplots(1, len(events), figsize=(24, 12), sharey=True)

legend_handles = set()

for i, event in enumerate(events):
    event_title = events_title[i]
    
    df_event = df_pivoted[df_pivoted['Event'] == event].copy()

    # Retain 'Region' column separately and ensure it is of string type
    df_event['Region'] = pd.Categorical(df_event['Region'], categories=regions_order, ordered=True)
    df_event = df_event.sort_values('Region')

    # Dynamically filter columns to exclude those that are not in the DataFrame
    available_columns = [col for col in groups['Built area'] + groups['Tall vegetation & scrub'] + groups['Low vegetation'] + groups['Bare & urban open'] if col in df_event.columns]
    
    # Create a separate DataFrame for land cover columns and keep 'Region'
    df_land_cover = df_event[['Region'] + available_columns]

    # Calculate the total area for normalization
    df_land_cover['Total Area'] = df_land_cover[available_columns].sum(axis=1)
    
    # Normalize these land cover columns to ensure the percentage doesn't exceed 100
    df_normalized = df_land_cover[available_columns].div(df_land_cover['Total Area'], axis=0) * 100

    # Ensure the 'Other' column exists
    df_normalized['Other'] = 0
    
    # Move small percentages to 'Other' for each row, but exclude 'Built-up Area (settlement)'
    non_built_up_columns = [col for col in available_columns if col != 'Built-up Area (settlement)']
    df_normalized['Other'] += df_normalized[non_built_up_columns].apply(lambda row: row[row < 2.5].sum(), axis=1)
    
    # Set values less than 2.5% to 0, but exclude 'Built-up Area (settlement)'
    df_normalized[non_built_up_columns] = df_normalized[non_built_up_columns].applymap(lambda x: 0 if x < 2.5 else x)

    # Reassign 'Region' as an index
    df_normalized['Region'] = df_event['Region'].values
    df_normalized = df_normalized.set_index('Region')

    # Filter available_columns to only those present in df_normalized
    available_columns_for_plot = [col for col in available_columns + ['Other'] if col in df_normalized.columns]
    
    # Generate colors for the columns to plot, with grey for 'Other'
    colors_event = [land_cover_to_color.get(col, '#cccccc') if col != 'Other' else '#cccccc' for col in available_columns_for_plot]

    # Adjust the spacing between bars by setting bar width and gaps
    bar_width = 0.75  # Increase this value to make bars thicker and reduce spacing
    gap_width = 0.15  # Decrease this value to reduce the space between regions

    # Plot the horizontal stacked bar chart without the legend
    df_normalized[available_columns_for_plot].plot(kind='barh', stacked=True, ax=axes[i], color=colors_event, width=bar_width)
    
    # Increase font size for x-axis label and remove the y-axis label while keeping region names
    axes[i].set_xlabel('%', fontsize=22)
    axes[i].set_ylabel('')  # Remove the y-axis label
    axes[i].set_title(event_title, fontsize=24)  # Increase font size of the title
    
    # Adjust tick parameters for both axes
    axes[i].set_xlim(0, 100)  # Limit the x-axis to 100
    axes[i].tick_params(axis='x', labelsize=20)
    axes[i].tick_params(axis='y', labelsize=20)  # Increase font size for region names

    # Collect legend handles for the used columns
    for col in available_columns_for_plot:
        # Check if the column has any value above 2.5% in the normalized DataFrame
        if (df_normalized[col] > 2.5).any() or col == 'Built-up Area (settlement)':
            legend_handles.add((Line2D([0], [0], color=land_cover_to_color.get(col, '#cccccc'), lw=10), col.replace('_', ' ')))

# Add bold (and optionally underlined) group headings in the legend
fig_legend, ax_legend = plt.subplots(figsize=(12, 1.6))
legend_elements = []

# Modify group headings to be bold and optionally underlined
for group in ['Built area', 'Tall vegetation & scrub', 'Low vegetation', 'Bare & urban open']:
    # Group title as bold
    legend_elements.append(Line2D([0], [0], color='white', label=r'$\mathbf{' + group.replace(' ', '\ ') + '}$', lw=0))
    for col in groups[group]:
        if col in [label for _, label in legend_handles]:
            legend_elements.append(Line2D([0], [0], color=land_cover_to_color.get(col, '#cccccc'), lw=10, label=col.replace('_', ' ')))

legend_elements.append(Line2D([0], [0], color='#cccccc', lw=10, label='Other'))

fig_legend.legend(handles=legend_elements, loc='center', ncol=4, fontsize=12, columnspacing=1.7, handletextpad=1)
ax_legend.axis('off')

# Remove the legend from the main plots
for ax in axes:
    ax.get_legend().remove()

plt.tight_layout()

fig.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Land_Cover_Percent.pdf', bbox_inches='tight')
fig.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Land_Cover_Percent.jpeg', dpi=400, bbox_inches='tight')

fig_legend.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Land_Cover_Percent_Legend.pdf', bbox_inches='tight')
fig_legend.savefig('D:/Nationwide_Tsunami_Inundation/Plots/Land_Cover_Percent_Legend.jpeg', dpi=400, bbox_inches='tight')

plt.show()
