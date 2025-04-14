# %%
import pandas as pd
import numpy as np
import spectral_entropy    #https://github.com/FangLabNTU/SpectralEntropy
import re

######################
# Load the peak table from an Excel file
file_path = "./ID/Predicted.csv"

output_file = "./ID/result1.xlsx"

# parameters
Add_nodes = 0

similarity_threshold = 0.5

ms_threshold = 0.1  # m/z tolerance (Da).

##########
#Fen nodes check
peak_table = pd.read_csv(file_path)
peak_table = peak_table[peak_table['Predicted Label'] == 1]

if Add_nodes == 1:
    Nodes_table_path = "./ID/Virtual_nodes.xlsx"
    
# Assuming Nodes_table is loaded from the specified path
    Nodes_table = pd.read_excel(Nodes_table_path)

# Combine peak_table with Nodes_table using pd.concat
    peak_table = pd.concat([peak_table, Nodes_table], ignore_index=True)
    
PMD_table_path = "./ID/PMD.xlsx"
PMD_table = pd.read_excel(PMD_table_path)
########

# Remove trailing ':' from the 'MSMS spectrum' column
peak_table['MSMS spectrum'] = peak_table['MSMS spectrum'].str.rstrip(':')

# Function to process the MS/MS spectrum and return a dictionary
def process_spectrum(spectrum):
    if isinstance(spectrum, float):
        return {}
    return dict((float(mz.split(':')[0]), float(mz.split(':')[1])) for mz in spectrum.split(' '))

# Apply the function to create 'MSMS_dict'
peak_table['MSMS_dict'] = peak_table['MSMS spectrum'].apply(process_spectrum)

# Calculate neutral loss and store in 'NL_spectrum'
peak_table['NL_spectrum'] = peak_table.apply(lambda row: {round(row['Precursor m/z'] - mz, 5): intensity for mz, intensity in row['MSMS_dict'].items() if row['Precursor m/z'] - mz > 0}, axis=1)

# Convert the 'NL_spectrum' into a string format
peak_table['NL_spectrum_str'] = peak_table['NL_spectrum'].apply(lambda x: ' '.join([f'{mz}:{intensity}' for mz, intensity in x.items()]))

# Create a new DataFrame to store processed data
nodetable1 = pd.DataFrame(columns=["precursor", "RT", "PeakID", "ms2_data", "NL_data"])

# Iterate over the rows in the peak table
for index, row in peak_table.iterrows():
    # If 'MSMS spectrum' is not empty
    if not pd.isna(row["MSMS spectrum"]):
        precursor = row["Precursor m/z"]
        ms2_data = row["MSMS spectrum"]
        PeakID = row["PeakID"]
        
        # Convert MS/MS spectrum data to DataFrame
        ms2_df = pd.DataFrame([entry.split(':') for entry in ms2_data.split(" ")], columns=["mz", "intensity"])
        ms2_df["mz"] = ms2_df["mz"].astype(float)
        ms2_df["intensity"] = ms2_df["intensity"].astype(float)
        
        # Clean the spectrum using spectral_entropy library
        clean_spectrum = spectral_entropy.clean_spectrum(ms2_df.to_numpy(), max_mz=800, noise_removal=0.01, ms2_da=0.01)
        RT = row["RT (min)"]
        
        # Process neutral loss spectrum
        NL_data = row["NL_spectrum_str"]
        NL_df = pd.DataFrame([entry.split(':') for entry in NL_data.split()], columns=["mz", "intensity"])
        NL_df["mz"] = NL_df["mz"].astype(float)
        NL_df["intensity"] = NL_df["intensity"].astype(float)
        
        clean_NL_spectrum = spectral_entropy.clean_spectrum(NL_df.to_numpy(), max_mz=precursor, noise_removal=0.01, ms2_da=0.01)
        
        # Append to nodetable1 DataFrame
        # Assuming clean_spectrum and clean_NL_spectrum are calculated before this step
        new_row = pd.DataFrame([{"precursor": precursor, "RT": RT, "PeakID": PeakID, 
                             "ms2_data": clean_spectrum, "NL_data": clean_NL_spectrum}])

# Concatenate the new row to nodetable1
        nodetable1 = pd.concat([nodetable1, new_row], ignore_index=True)

    
    # If 'MSMS spectrum' is empty
    if pd.isna(row["MSMS spectrum"]):
        precursor = row["Precursor m/z"]
        RT = row["RT (min)"]
        PeakID = row["PeakID"]
        nodetable1 = nodetable1.append({"precursor": precursor, "RT": RT, "PeakID": PeakID}, ignore_index=True)

# Remove rows with missing 'ms2_data'
nodetable1 = nodetable1.dropna(subset=['ms2_data'])


# %%

# Create an empty DataFrame to store similarity scores
similarity_df = pd.DataFrame(columns=["Precursor_a", "PeakID_a", "Precursor_b", "PeakID_b", "Mass_difference"])
similarity_df1 = []
similarity_df2 = []

# Iterate through all possible combinations to calculate similarity
max_index = max(nodetable1.index)

# Only loop through the first two rows with other rows
for index_a, row_a in nodetable1.iterrows():
    if index_a >= 2:  # Only process the first two rows
        break

    for index_b in range(index_a + 1, max_index + 1):
        if index_b in nodetable1.index:
            row_b = nodetable1.loc[index_b]
            Precursor_a = row_a["precursor"]
            Precursor_b = row_b["precursor"]
            Mass_difference = Precursor_b - Precursor_a
            PeakID_a = row_a["PeakID"]
            ms2_data_a = row_a["ms2_data"]
            NL_data_a = row_a["NL_data"]
            PeakID_b = row_b["PeakID"]
            ms2_data_b = row_b["ms2_data"]
            NL_data_b = row_b["NL_data"]

            # Convert MS2 data to DataFrame
            ms2_df_a = pd.DataFrame(ms2_data_a, columns=["mz", "intensity"])
            NL_df_a = pd.DataFrame(NL_data_a, columns=["mz", "intensity"])
            ms2_df_b = pd.DataFrame(ms2_data_b, columns=["mz", "intensity"])
            NL_df_b = pd.DataFrame(NL_data_b, columns=["mz", "intensity"])

            # Ensure data types are float
            for df in [ms2_df_a, NL_df_a, ms2_df_b, NL_df_b]:
                df["mz"] = df["mz"].astype(float)
                df["intensity"] = df["intensity"].astype(float)

            # Calculate similarity
            all_dist = spectral_entropy.all_similarity(ms2_df_a.to_numpy(), ms2_df_b.to_numpy(), ms2_da=0.05)
            similarity_values1 = {spectral_entropy.methods_name[dist_name]: value for dist_name, value in all_dist.items()}
            similarity_df1.append(similarity_values1)

            all_dist = spectral_entropy.all_similarity(NL_df_a.to_numpy(), NL_df_b.to_numpy(), ms2_da=0.005)
            similarity_values2 = {spectral_entropy.methods_name[dist_name] + "_NL": value for dist_name, value in all_dist.items()}
            similarity_df2.append(similarity_values2)

            # Assuming similarity_df is a DataFrame and similarity_values contains the data
            similarity_row = pd.DataFrame([{
                "Precursor_a": Precursor_a,
                "PeakID_a": PeakID_a,
                "Precursor_b": Precursor_b,
                "PeakID_b": PeakID_b,
                "Mass_difference": Mass_difference
            }])

# Concatenate the new row to similarity_df
            similarity_df = pd.concat([similarity_df, similarity_row], ignore_index=True)

# Convert similarity score lists to DataFrames
similarity_df1 = pd.DataFrame(similarity_df1)
similarity_df2 = pd.DataFrame(similarity_df2)

# Merge results
result_df = pd.concat([similarity_df, similarity_df1, similarity_df2], axis=1)

# Remove rows where PeakID_a and PeakID_b are equal
result_df = result_df[result_df['PeakID_a'] != result_df['PeakID_b']]


# %%
# Step 2.0: Further processing and assigning molecular formulas
# Keep the first 5 columns
columns_to_keep = result_df.columns[:5].tolist()

# Check for additional columns and add them to the list
additional_columns = ['MSforID distance version 1', 'MSforID distance version 1_NL']
for col in additional_columns:
    if col in result_df.columns:
        columns_to_keep.append(col)
    else:
        raise KeyError(f"Column {col} not found in the DataFrame.")

# Retain only the required columns
result_df = result_df[columns_to_keep]
result_df = result_df[result_df['MSforID distance version 1'] > similarity_threshold]

# Add 'Reaction' and 'Description' columns to result_df
result_df['Reaction'] = None
result_df['Description'] = None

# Iterate through the 'Mass_difference' column in result_df
# Iterate through each row of result_df
for idx, row in result_df.iterrows():
    mass_diff = row['Mass_difference']
    
    # Find matching rows in PMD_table
    matches = PMD_table[abs(PMD_table['Mass Difference (Da)'] - abs(mass_diff)) <= ms_threshold]
    
    # If matching rows are found, assign 'Reaction' and 'Description' to result_df
    if not matches.empty:
        result_df.at[idx, 'Reaction'] = matches.iloc[0]['Reaction']
        result_df.at[idx, 'Description'] = matches.iloc[0]['Description']

# Create a new column to ensure consistent order of inchikey1 and inchikey2
def safe_sort(val):
    if isinstance(val, str):
        return float('inf')  
    return val  

result_df['sorted_inchikeys'] = result_df.apply(
    lambda row: tuple(sorted([row['PeakID_a'], row['PeakID_b']], key=safe_sort)), axis=1
)


# Retain the rows with the maximum similarity for the same sorted_inchikeys
result_df_max_similarity = result_df.loc[
    result_df.groupby(['sorted_inchikeys'])['MSforID distance version 1'].idxmax()
].reset_index(drop=True)

# Drop the temporary column
result_df = result_df_max_similarity.drop(columns=['sorted_inchikeys'])
result_df.to_excel(output_file, index=False)


