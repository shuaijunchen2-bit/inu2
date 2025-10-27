import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

def clean_territorial_authority_names(df):
    # Replace underscores with spaces
    df['Territorial_Authority'] = df['Territorial_Authority'].str.replace('_', ' ')
    
    # Handle specific cases with special characters
    df['Territorial_Authority'] = df['Territorial_Authority'].replace({
        'Ōpōtiki District': 'Opotiki District',
        'Ōtorohanga District': 'Otorohanga District'
    })
    
    return df

def get_top_territories(merged_df, territorial_authorities_north_to_south, rankings_df, onrc_class):
    # Filter the DataFrame for the 2500y50p event
    event_2500y50p_df = merged_df[merged_df['Event'] == 'H2500y50p']

    # Rank the territories by total inundation and percentage for this ONRC class
    event_2500y50p_df['Rank_Total'] = event_2500y50p_df['Length_km'].rank(method='min', ascending=False)
    event_2500y50p_df['Rank_Percent'] = event_2500y50p_df['Percentage'].rank(method='min', ascending=False)
    
    # Combine ranks
    event_2500y50p_df['Combined_Rank'] = event_2500y50p_df[['Rank_Total', 'Rank_Percent']].mean(axis=1)
    
    # Sort by combined rank
    event_2500y50p_df = event_2500y50p_df.sort_values('Combined_Rank')

    # Select the top 12 territories based on the combined rank
    top_territories = event_2500y50p_df['Territorial_Authority'].unique()[:10].tolist()
    
    # Append rankings to the rankings DataFrame
    for _, row in event_2500y50p_df.iterrows():
        rankings_df.loc[row['Territorial_Authority'], f'{onrc_class}_Rank'] = row['Combined_Rank']
    
    # Return the intersection of top_territories and predefined order
    return [region for region in territorial_authorities_north_to_south if region in top_territories][:10]

def plot_top_infrastructure_comparison(gpkg_file_path, total_assets_csv_path, return_period_events, onrc_classes, ylabels, titles):
    # Predefined order of regions from North to South
    territorial_authorities_north_to_south = [
        'Southland District', 'Invercargill City', 'Dunedin City', 'Clutha District', 
        'Waitaki District', 'Waimate District', 'Timaru District', 'Ashburton District', 
        'Selwyn District', 'Christchurch City', 'Waimakariri District', 'Hurunui District', 
        'Westland District', 'Grey District', 'Buller District', 'Kaikoura District', 
        'Marlborough District', 'Nelson City', 'Tasman District', 'South Wairarapa District', 
        'Carterton District', 'Masterton District', 'Wellington City', 'Lower Hutt City', 
        'Porirua City', 'Kapiti Coast District', 'Horowhenua District', 'Tararua District', 
        'Manawatu District', 'Rangitikei District', 'Whanganui District', 'South Taranaki District', 
        'New Plymouth District', 'Wairoa District', 'Napier City', 'Hastings District', 
        "Central Hawke's Bay District", 'Gisborne District', 'Opotiki District', 'Whakatane District', 
        'Tauranga City', 'Western Bay of Plenty District', 'Waitomo District', 'Otorohanga District', 
        'Waikato District', 'Hauraki District', 'Thames-Coromandel District', 'Auckland', 
        'Kaipara District', 'Whangarei District', 'Far North District'
    ]
    
    # Initialize a DataFrame to store rankings
    rankings_df = pd.DataFrame(index=territorial_authorities_north_to_south)
    
    fig, axs = plt.subplots(3, 2, figsize=(16, 22))  # 3 rows, 2 columns
    axs = axs.flatten()  # Flatten the array of axes for easy iteration

    for ax, onrc_class, ylabel, subplot_title in zip(axs, onrc_classes, ylabels, titles):
        # Load the data into DataFrames
        inundation_df = gpd.read_file(gpkg_file_path)
        total_assets_df = pd.read_csv(total_assets_csv_path)
        
        inundation_df = clean_territorial_authority_names(inundation_df)
        total_assets_df = clean_territorial_authority_names(total_assets_df)
        
        # Filter the data for the specific ONRCClass
        inundation_df = inundation_df[inundation_df['ONRCClass'] == onrc_class]

        # Merge the two DataFrames on the 'Territorial_Authority' column to calculate percentages
        merged_df = pd.merge(inundation_df, total_assets_df[['Territorial_Authority', 'ONRCClass', 'Total_Length_km']], 
                             on=['Territorial_Authority', 'ONRCClass'], suffixes=('', '_Total'))

        # Calculate the percentage of assets inundated
        merged_df['Percentage'] = (merged_df['Length_km'] / merged_df['Total_Length_km']) * 100
        
        # Determine the top territories for this specific ONRC class
        top_territories = get_top_territories(merged_df, territorial_authorities_north_to_south, rankings_df, onrc_class)
        
        # Filter the merged DataFrame to include only the top territories
        filtered_df = merged_df[merged_df['Territorial_Authority'].isin(top_territories)].copy()
        
        # Ensure the regions are ordered from North to South
        filtered_df['Territorial_Authority'] = pd.Categorical(filtered_df['Territorial_Authority'], categories=territorial_authorities_north_to_south, ordered=True)
        filtered_df.sort_values('Territorial_Authority', inplace=True)
        
        # Total width of all bars for each region, adjusted to allow gaps
        total_width = 0.8  
        num_events = len(return_period_events) // 2  # Assuming there are an equal number of 50p and 84p events
        bar_width = total_width / num_events
        gap_width = 0.06  # Larger gap between regions
        inter_event_gap = 0.02  # Small gap between return period events
        bar_width -= inter_event_gap  # Adjust bar width to include the gap

        # Adjusted color map to be less bright
        colors = plt.cm.autumn(np.linspace(0.2, 0.8, num_events))

        # Create a secondary x-axis for percentages
        ax2 = ax.twiny()
        
        unique_handles_labels = {}

        # Iterate over each region
        for i, region in enumerate(filtered_df['Territorial_Authority'].unique()):
            # For each region, get the subset of the DataFrame
            region_df = filtered_df[filtered_df['Territorial_Authority'] == region]
            
            # Sort the DataFrame by the new categorical columns
            region_df = region_df.sort_values(by=['Event'], ascending=[False])

            # Start position for the first bar of the region
            start_position = i * (total_width + gap_width)

            # Initialize lists for line plot
            x_positions_50 = []
            y_percentages_50 = []
            x_positions_84 = []
            y_percentages_84 = []
            
            # Iterate over each event pair
            for j in range(num_events):
                # Calculate the bar position
                bar_position = start_position + (j * (bar_width + inter_event_gap))

                # 50th percentile event
                event_50 = return_period_events[j*2 + 1]  # 50p events are in the even indices
                value_50 = region_df[region_df['Event'] == event_50]['Length_km'].sum() if not region_df[region_df['Event'] == event_50].empty else 0
                bar_50 = ax.barh(bar_position, value_50, bar_width, color=colors[j], alpha=0.5)
                unique_handles_labels[event_50] = bar_50

                # 84th percentile event, stacked
                event_84 = return_period_events[j*2]  # 84p events are in the odd indices
                value_84 = region_df[region_df['Event'] == event_84]['Length_km'].sum() if not region_df[region_df['Event'] == event_84].empty else 0
                bar_84 = ax.barh(bar_position, value_84 - value_50, bar_width, left=value_50, color=colors[j], alpha=1)
                unique_handles_labels[event_84] = bar_84
                
                # Collect data for the percentage line plot
                x_positions_50.append(start_position + (j * (bar_width + inter_event_gap)) + (bar_width / 2))  # Align with bar center
                y_percentages_50.append(region_df[region_df['Event'] == event_50]['Percentage'].sum() if not region_df[region_df['Event'] == event_50].empty else 0)
                x_positions_84.append(start_position + (j * (bar_width + inter_event_gap)) + (bar_width / 2))  # Align with bar center
                y_percentages_84.append(region_df[region_df['Event'] == event_84]['Percentage'].sum() if not region_df[region_df['Event'] == event_84].empty else 0)
            
            # Plot percentage lines with points for the region
            ax2.plot(y_percentages_50, x_positions_50, marker='o', linestyle='-', color='grey', alpha=0.5)
            ax2.plot(y_percentages_84, x_positions_84, marker='o', linestyle='-', color='black', alpha=0.5)

        # Customize the plot
        ax.set_xlabel(ylabel, fontsize=15)
        ax.set_ylim(-gap_width, len(filtered_df['Territorial_Authority'].unique()) * (total_width + gap_width) - gap_width)
        ax.set_xlim(0, filtered_df['Length_km'].max() * 1.05)  # Adjust x limits for asset counts/lengths
        ax2.set_xlabel('Percent of Territorial Authority assets (%)', fontsize=15)
        ax2.set_xlim(0, filtered_df['Percentage'].max() * 1.05)  # Set x limits for percentage axis
        ax.tick_params(axis='x', labelsize=14)
        ax2.tick_params(axis='x', labelsize=14)
        
        # Set the y-axis labels for this subplot in the predefined North to South order
        ax.set_yticks(ticks=np.arange(len(filtered_df['Territorial_Authority'].unique())) * (total_width + gap_width) + (total_width / 2))
        ax.set_yticklabels(filtered_df['Territorial_Authority'].unique(), fontsize=15)
        
        # Add title for each subplot
        ax.set_title(subplot_title, fontsize=20)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    
    fig.savefig('D:/Nationwide_Tsunami_Inundation/Plots/ONRC_Class_Territory_Exposure.pdf', bbox_inches='tight')
    fig.savefig('D:/Nationwide_Tsunami_Inundation/Plots/ONRC_Class_Territory_Exposure.jpeg', dpi=300, bbox_inches='tight')
    
    plt.show()

# Example usage
gpkg_file_path = 'D:/Nationwide_Tsunami_Inundation/Territorial_Authority_Roads/Merged_All_Territories_Roads.gpkg'
total_assets_csv_path = 'D:/Nationwide_Tsunami_Inundation/Infrastructure/Roads_ONRCClass_Lengths_By_TA.csv'

# Return period events, pairing 50p and 84p events in reverse order
return_period_events = [
    "H100y50p", "H100y84p",
    "H250y50p", "H250y84p",
    "H500y50p", "H500y84p",
    "H1000y50p", "H1000y84p",
    "H1500y50p", "H1500y84p",
    "H2000y50p", "H2000y84p",
    "H2500y50p", "H2500y84p"
]

return_period_events = return_period_events[::-1]

# Specify the asset types, y-axis labels, and subplot titles you want to plot
onrc_classes = [
    'National + High Volume',
    'Regional',
    'Arterial',
    'Primary Collector',
    'Secondary Collector',
    'Access + Low Volume'
]

ylabels = ['Length (km)', 'Length (km)', 'Length (km)', 'Length (km)', 'Length (km)', 'Length (km)']
titles = [
    'a) National + High Volume',
    'b) Regional',
    'c) Arterial',
    'd) Primary Collector',
    'e) Secondary Collector',
    'f) Access + Low Volume'
]

plot_top_infrastructure_comparison(gpkg_file_path, total_assets_csv_path, return_period_events, onrc_classes, ylabels, titles)
