# %%
import pandas as pd
import numpy as np
import joblib
from tqdm import tqdm

################## 
# Read the Met-fentanyl.txt file into a DataFrame    
file_path = './Finder/Met-fentanyl.txt'   

# Export the results to a new CSV file
output_file = "./Finder/Predicted.csv"

# Clean MS1 with thresholds
sn_threshold = 3  # S/N threshold
area_threshold = 10000  # Area threshold

# Remove duplicate peaks based on thresholds
mz_threshold = 0.005
rt_threshold = 0.2

############

# Load the best model 
best_rf_model = joblib.load('./Finder/Fentanyl_Finder.pkl')

##############
data = pd.read_csv(file_path, sep="\t")  # Adjust separator if necessary

# Remove rows where 'MSMS spectrum' is empty
data = data.dropna(subset=['MSMS spectrum'])

# Create 'Spectra' column by replacing line breaks and colons
data['Spectra'] = data['MSMS spectrum'].str.replace(' ', '\n').str.replace(':', ' ')

# Ensure 'Comment' is a string
data['Comment'] = data['Comment'].astype(str)

# Filter for isotope and remove unwanted comments
data = data[(data['Isotope'] == "M + 0") & 
            (~data['Comment'].str.contains("found in higher mz's MsMs"))]

# Handle adducts
data['PeakID'] = data['PeakID'].astype(str)
for index, row in data.iterrows():
    if "adduct linked to" in row['Comment']:
        comment_values = row['Comment'].split(';')
        id_values = [value.split("adduct linked to ")[1].split('_')[0].strip() for value in comment_values if "adduct linked to" in value]
        
        # Filter matching rows
        matching_rows = data[data['PeakID'].isin(id_values)]
        if not matching_rows.empty:
            combined_rows = pd.concat([row.to_frame().T, matching_rows])
            max_area = combined_rows['Area'].max()
            if row['Area'] < max_area:
                data = data.drop(index)
                matching_rows_to_remove = matching_rows[matching_rows['Area'] < max_area].index
                data = data.drop(matching_rows_to_remove)

# Reset index
data.reset_index(drop=True, inplace=True)


data = data.query('`S/N` >= @sn_threshold and `Area` >= @area_threshold')


data = data.sort_values('Precursor m/z')

# Group by thresholds and keep maximum Area
groups = []
while not data.empty:
    group_mask = (data['Precursor m/z'].sub(data.iloc[0]['Precursor m/z']).abs() <= mz_threshold) & \
                 (data['RT (min)'].sub(data.iloc[0]['RT (min)']).abs() <= rt_threshold)
    group = data[group_mask]
    largest_area_row = group.loc[group['Area'].idxmax()]
    groups.append(largest_area_row)
    data = data[~group_mask]

# Result DataFrame
peak_table = pd.DataFrame(groups)


# %%

# Read the data
data = peak_table
data['Spectra'] = data['Spectra'].apply(lambda x: x.split('\n'))

# Define parameters
ms2int_threshold = 10.0
mz_min = 50.0
mz_max = 400.0
num_bins = 3500

# Data preprocessing
data_processed = data.copy()

# Initialize m/z bins matrix
mz_bins_matrix = np.zeros((len(data_processed), num_bins))

for i, row in tqdm(enumerate(data_processed.itertuples()), total=len(data_processed), desc=f"Processing rows for num_bins = {num_bins}"):
    MS2_list = row.Spectra
    mz = []
    Relative_int = []
    for pair in MS2_list:
        if pair:
            try:
                mz_val, intensity_val = pair.split()
                mz.append(float(mz_val))
                Relative_int.append(float(intensity_val))
            except ValueError:
                continue

    filtered_pairs = [(mz_val, int_val) for mz_val, int_val in zip(mz, Relative_int) if int_val >= ms2int_threshold and mz_min <= mz_val <= mz_max]
    for mz_val, int_val in filtered_pairs:
        bin_index = int((mz_val - mz_min) / (mz_max - mz_min) * num_bins)
        bin_index = max(0, min(bin_index, num_bins - 1))
        mz_bins_matrix[i, bin_index] += int_val

# Convert m/z bins matrix to DataFrame and merge into data_processed
mz_bins_df = pd.DataFrame(mz_bins_matrix, columns=[f'bin_{i}' for i in range(num_bins)])
data_processed = pd.concat([data_processed.reset_index(drop=True), mz_bins_df.reset_index(drop=True)], axis=1)

# Drop the original 'Spectra' column
data_processed.drop('Spectra', axis=1, inplace=True)

# List of columns to drop
columns_to_drop = [
    'PeakID', 'Title', 'Scans', 'RT left(min)', 'RT (min)', 
    'RT right (min)', 'Precursor m/z', 'Height', 'Area', 
    'Model masses', 'Adduct', 'Isotope', 'Comment', 
    'Reference RT', 'Reference m/z', 'Formula', 'Ontology', 
    'InChIKey', 'SMILES', 'Annotation tag (VS1.0)', 
    'RT matched', 'm/z matched', 'MS/MS matched', 
    'RT similarity', 'Dot product', 'Reverse dot product', 
    'Fragment presence %', 'Total score', 'S/N', 'MS1 isotopes', 
    'MSMS spectrum'
]

# Drop the specified columns from the DataFrame
X = data_processed.drop(columns=columns_to_drop, axis=1)

# Make predictions
y_pred = best_rf_model.predict(X)
y_proba = best_rf_model.predict_proba(X)[:, 1]

# Add predictions to the processed data
data_processed['Predicted Label'] = y_pred
data_processed['Prediction Probability'] = y_proba

# Drop columns starting with 'bin_'
data_processed = data_processed.drop(columns=data_processed.filter(like='bin_').columns)


data_processed.to_csv(output_file, index=False)


# %%



