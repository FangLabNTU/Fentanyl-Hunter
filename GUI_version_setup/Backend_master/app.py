from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import spectral_entropy
import joblib
from tqdm import tqdm
import os

app = Flask(__name__)

def process_id_logic(peak_table, nodes_table, pmd_table, similarity_threshold, ms_threshold):
    """ID_GUI 的核心处理逻辑"""
    # 移除 MSMS spectrum 列中的尾随冒号
    peak_table['MSMS spectrum'] = peak_table['MSMS spectrum'].str.rstrip(':')
    
    # 处理质谱数据的函数
    def process_spectrum(spectrum):
        if isinstance(spectrum, float):
            return {}
        return dict((float(mz.split(':')[0]), float(mz.split(':')[1])) 
                   for mz in spectrum.split(' '))
    
    # 创建 MSMS 字典
    peak_table['MSMS_dict'] = peak_table['MSMS spectrum'].apply(process_spectrum)
    
    # 计算中性损失
    peak_table['NL_spectrum'] = peak_table.apply(
        lambda row: {
            round(row['Precursor m/z'] - mz, 5): intensity 
            for mz, intensity in row['MSMS_dict'].items() 
            if row['Precursor m/z'] - mz > 0
        }, 
        axis=1
    )
    
    # 转换中性损失为字符串格式
    peak_table['NL_spectrum_str'] = peak_table['NL_spectrum'].apply(
        lambda x: ' '.join([f'{mz}:{intensity}' for mz, intensity in x.items()])
    )
    
    # 创建节点表
    nodetable1 = pd.DataFrame(columns=["precursor", "RT", "PeakID", "ms2_data", "NL_data"])
    
    # 处理每一行数据
    for _, row in peak_table.iterrows():
        if not pd.isna(row["MSMS spectrum"]):
            precursor = row["Precursor m/z"]
            ms2_data = row["MSMS spectrum"]
            PeakID = row["PeakID"]
            RT = row["RT (min)"]
            
            # 处理 MS2 数据
            ms2_df = pd.DataFrame([
                entry.split(':') for entry in ms2_data.split(" ")
            ], columns=["mz", "intensity"]).astype(float)
            
            clean_spectrum = spectral_entropy.clean_spectrum(
                ms2_df.to_numpy(), 
                max_mz=800, 
                noise_removal=0.01, 
                ms2_da=0.01
            )
            
            # 处理中性损失数据
            NL_data = row["NL_spectrum_str"]
            NL_df = pd.DataFrame([
                entry.split(':') for entry in NL_data.split()
            ], columns=["mz", "intensity"]).astype(float)
            
            clean_NL_spectrum = spectral_entropy.clean_spectrum(
                NL_df.to_numpy(), 
                max_mz=precursor, 
                noise_removal=0.01, 
                ms2_da=0.01
            )
            
            # 添加到节点表
            new_row = pd.DataFrame([{
                "precursor": precursor,
                "RT": RT,
                "PeakID": PeakID,
                "ms2_data": clean_spectrum,
                "NL_data": clean_NL_spectrum
            }])
            nodetable1 = pd.concat([nodetable1, new_row], ignore_index=True)
    
    # 移除缺失 ms2_data 的行
    nodetable1 = nodetable1.dropna(subset=['ms2_data'])
    
    # 计算相似度
    similarity_results = []
    max_index = max(nodetable1.index)
    
    # 只处理前两行数据
    for index_a, row_a in nodetable1.iterrows():
        if index_a >= 2:  # 只处理前两行数据
            break
            
        for index_b in range(index_a + 1, max_index + 1):
            if index_b in nodetable1.index:
                row_b = nodetable1.loc[index_b]
                
                # 计算基本信息
                mass_difference = row_b["precursor"] - row_a["precursor"]
                
                # 计算 MS2 相似度
                ms2_sim = spectral_entropy.all_similarity(
                    pd.DataFrame(row_a["ms2_data"], columns=["mz", "intensity"]).to_numpy(),
                    pd.DataFrame(row_b["ms2_data"], columns=["mz", "intensity"]).to_numpy(),
                    ms2_da=0.05
                )
                
                # 计算中性损失相似度
                nl_sim = spectral_entropy.all_similarity(
                    pd.DataFrame(row_a["NL_data"], columns=["mz", "intensity"]).to_numpy(),
                    pd.DataFrame(row_b["NL_data"], columns=["mz", "intensity"]).to_numpy(),
                    ms2_da=0.005
                )
                
                similarity_results.append({
                    "Precursor_a": row_a["precursor"],
                    "PeakID_a": row_a["PeakID"],
                    "Precursor_b": row_b["precursor"],
                    "PeakID_b": row_b["PeakID"],
                    "Mass_difference": mass_difference,
                    "MSforID distance version 1": ms2_sim.get("dot_product", 0),
                    "MSforID distance version 1_NL": nl_sim.get("dot_product", 0)
                })
    
    # 转换为 DataFrame
    result_df = pd.DataFrame(similarity_results)
    
    # 应用相似度阈值过滤
    result_df = result_df[result_df['MSforID distance version 1'] > similarity_threshold]
    
    # 添加反应和描述信息
    result_df['Reaction'] = None
    result_df['Description'] = None
    
    # 匹配 PMD 表中的信息
    for idx, row in result_df.iterrows():
        mass_diff = row['Mass_difference']
        matches = pmd_table[
            abs(pmd_table['Mass Difference (Da)'] - abs(mass_diff)) <= ms_threshold
        ]
        if not matches.empty:
            result_df.at[idx, 'Reaction'] = matches.iloc[0]['Reaction']
            result_df.at[idx, 'Description'] = matches.iloc[0]['Description']
    
    # 创建一个新列来确保一致的排序顺序
    def safe_sort(val):
        if isinstance(val, str):
            return float('inf')  
        return val  

    result_df['sorted_inchikeys'] = result_df.apply(
        lambda row: tuple(sorted([row['PeakID_a'], row['PeakID_b']], key=safe_sort)), axis=1
    )

    # 保留相同 sorted_inchikeys 中相似度最大的行
    result_df_max_similarity = result_df.loc[
        result_df.groupby(['sorted_inchikeys'])['MSforID distance version 1'].idxmax()
    ].reset_index(drop=True)

    # 删除临时列
    result_df = result_df_max_similarity.drop(columns=['sorted_inchikeys'])
    
    return result_df

def process_finder_logic(data, sn_threshold, area_threshold, mz_threshold, rt_threshold, best_rf_model):
    """Finder_GUI 的核心处理逻辑"""
    # 创建数据的深拷贝，避免 SettingWithCopyWarning
    data = data.copy()
    
    # 数据预处理
    data = data.dropna(subset=['MSMS spectrum'])
    
    # 使用 loc 进行赋值操作
    data.loc[:, 'Spectra'] = data['MSMS spectrum'].str.replace(' ', '\n').str.replace(':', ' ')
    data.loc[:, 'Comment'] = data['Comment'].astype(str)
    
    # 过滤数据
    mask = (data['Isotope'] == "M + 0") & (~data['Comment'].str.contains("found in higher mz's MsMs"))
    data = data[mask].copy()  # 使用 copy() 创建新的 DataFrame
    
    # 处理加合物
    data.loc[:, 'PeakID'] = data['PeakID'].astype(str)
    indices_to_drop = []
    
    for index, row in data.iterrows():
        if "adduct linked to" in row['Comment']:
            comment_values = row['Comment'].split(';')
            id_values = [
                value.split("adduct linked to ")[1].split('_')[0].strip() 
                for value in comment_values 
                if "adduct linked to" in value
            ]
            
            matching_rows = data[data['PeakID'].isin(id_values)]
            if not matching_rows.empty:
                combined_rows = pd.concat([row.to_frame().T, matching_rows])
                max_area = combined_rows['Area'].max()
                if row['Area'] < max_area:
                    indices_to_drop.append(index)
                    indices_to_drop.extend(
                        matching_rows[matching_rows['Area'] < max_area].index
                    )
    
    data = data.drop(indices_to_drop)
    data.reset_index(drop=True, inplace=True)
    
    # 应用阈值过滤
    data = data.query('`S/N` >= @sn_threshold and `Area` >= @area_threshold')
    data = data.sort_values('Precursor m/z')
    
    # 分组处理
    groups = []
    while not data.empty:
        group_mask = (
            (data['Precursor m/z'].sub(data.iloc[0]['Precursor m/z']).abs() <= mz_threshold) & 
            (data['RT (min)'].sub(data.iloc[0]['RT (min)']).abs() <= rt_threshold)
        )
        group = data[group_mask]
        largest_area_row = group.loc[group['Area'].idxmax()]
        groups.append(largest_area_row)
        data = data[~group_mask]
    
    peak_table = pd.DataFrame(groups)
    
    # 特征处理
    ms2int_threshold = 10.0
    mz_min = 50.0
    mz_max = 400.0
    num_bins = 3500
    
    # 初始化 m/z bins 矩阵
    mz_bins_matrix = np.zeros((len(peak_table), num_bins))
    
    for i, row in enumerate(peak_table.itertuples()):
        MS2_list = row.Spectra.split('\n')
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
        
        filtered_pairs = [
            (mz_val, int_val) 
            for mz_val, int_val in zip(mz, Relative_int) 
            if int_val >= ms2int_threshold and mz_min <= mz_val <= mz_max
        ]
        
        for mz_val, int_val in filtered_pairs:
            bin_index = int((mz_val - mz_min) / (mz_max - mz_min) * num_bins)
            bin_index = max(0, min(bin_index, num_bins - 1))
            mz_bins_matrix[i, bin_index] += int_val
    
    # 准备模型输入数据
    X = pd.DataFrame(
        mz_bins_matrix,
        columns=[f'bin_{i}' for i in range(num_bins)]
    )
    
    # 预测
    y_pred = best_rf_model.predict(X)
    y_proba = best_rf_model.predict_proba(X)[:, 1]
    
    # 添加预测结果
    peak_table['Predicted Label'] = y_pred
    peak_table['Prediction Probability'] = y_proba
    
    return peak_table

@app.route('/api/v1/id', methods=['POST'])
def process_id():
    try:
        data = request.get_json()
        
        # 参数验证
        required_params = ['file_path', 'similarity_threshold', 'ms_threshold']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # 从请求中获取参数
        file_path = data['file_path']
        Add_nodes = data.get('add_nodes', 0)
        similarity_threshold = float(data['similarity_threshold'])
        ms_threshold = float(data['ms_threshold'])  # m/z tolerance (Da)
        
        # 处理输出文件路径
        output_file = './ID/result1.xlsx'  # 默认路径
        if 'output_file' in data:
            if isinstance(data['output_file'], str) and data['output_file'].strip():
                output_file = data['output_file']
                # 如果是目录而不是文件，则在目录中添加默认文件名
                if output_file.endswith('\\') or output_file.endswith('/') or os.path.isdir(output_file):
                    if not output_file.endswith('\\') and not output_file.endswith('/'):
                        output_file += '\\'
                    output_file += 'result1.xlsx'
                print(f"Using custom output path: {output_file}")
            else:
                print(f"Warning: Invalid output_file value: {data['output_file']}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
        
        # 以下完全照抄 ID_GUI.py 的处理逻辑
        peak_table = pd.read_csv(file_path)
        peak_table = peak_table[peak_table['Predicted Label'] == 1]

        if Add_nodes == 1:
            Nodes_table_path = "./ID/Virtual_nodes.xlsx"
            Nodes_table = pd.read_excel(Nodes_table_path)
            peak_table = pd.concat([peak_table, Nodes_table], ignore_index=True)
            
        PMD_table_path = "./ID/PMD.xlsx"
        PMD_table = pd.read_excel(PMD_table_path)

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
                new_row = pd.DataFrame([{
                    "precursor": precursor, 
                    "RT": RT, 
                    "PeakID": PeakID,
                    "ms2_data": clean_spectrum, 
                    "NL_data": clean_NL_spectrum
                }])
                nodetable1 = pd.concat([nodetable1, new_row], ignore_index=True)
            
            # If 'MSMS spectrum' is empty
            if pd.isna(row["MSMS spectrum"]):
                precursor = row["Precursor m/z"]
                RT = row["RT (min)"]
                PeakID = row["PeakID"]
                nodetable1 = nodetable1.append({"precursor": precursor, "RT": RT, "PeakID": PeakID}, ignore_index=True)

        # Remove rows with missing 'ms2_data'
        nodetable1 = nodetable1.dropna(subset=['ms2_data'])

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
                    similarity_df = pd.concat([similarity_df, similarity_row], ignore_index=True)

        # Convert similarity score lists to DataFrames
        similarity_df1 = pd.DataFrame(similarity_df1)
        similarity_df2 = pd.DataFrame(similarity_df2)

        # Merge results
        result_df = pd.concat([similarity_df, similarity_df1, similarity_df2], axis=1)

        # Remove rows where PeakID_a and PeakID_b are equal
        result_df = result_df[result_df['PeakID_a'] != result_df['PeakID_b']]

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

        # Iterate through each row of result_df
        for idx, row in result_df.iterrows():
            mass_diff = row['Mass_difference']
            matches = PMD_table[abs(PMD_table['Mass Difference (Da)'] - abs(mass_diff)) <= ms_threshold]
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
        
        # 保存结果
        result_df.to_excel(output_file, index=False)
        
        # 限制返回的数据记录为前10条
        data_records = result_df.head(10).to_dict(orient='records')
        
        return jsonify({
            'status': 'success',
            'message': 'ID processing completed successfully',
            'output_file': output_file,
            'row_count': len(result_df),
            'data': data_records
        })
        
    except Exception as e:
        print(f"Error in process_id: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/finder', methods=['POST'])
def process_finder():
    try:
        # 打印原始请求数据
        print("Raw request data:")
        print(request.data)
        
        data = request.get_json()
        print("Parsed JSON data:")
        print(data)
        
        if 'output_file' in data:
            print(f"output_file type: {type(data['output_file'])}")
            print(f"output_file value: {data['output_file']}")
        else:
            print("output_file parameter not found")
        
        print("loading data...")
        
        # 参数验证
        required_params = ['file_path', 'sn_threshold', 'area_threshold', 'mz_threshold', 'rt_threshold']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        print("read model...")
        # 读取输入文件
        input_data = pd.read_csv(data['file_path'], sep="\t")
        
        print("loading model...")
        # 加载模型
        model_path = data.get('model_path', './Finder/Fentanyl_Finder.pkl')
        best_rf_model = joblib.load(model_path)
        
        # 执行处理逻辑
        print("handle logic...")
        result_df = process_finder_logic(
            input_data,
            float(data['sn_threshold']),
            float(data['area_threshold']),
            float(data['mz_threshold']),
            float(data['rt_threshold']),
            best_rf_model
        )
        
        # 保存结果
        print("save result...")
        
        # 获取输出文件路径
        output_file = './Finder/Predicted.csv'  # 默认路径
        if 'output_file' in data:
            if isinstance(data['output_file'], str) and data['output_file'].strip():
                output_file = data['output_file']
                # 如果是目录而不是文件，则在目录中添加默认文件名
                if output_file.endswith('\\') or output_file.endswith('/') or os.path.isdir(output_file):
                    if not output_file.endswith('\\') and not output_file.endswith('/'):
                        output_file += '\\'
                    output_file += 'Predicted.csv'
                print(f"Using custom output path: {output_file}")
            else:
                print(f"Warning: Invalid output_file value: {data['output_file']}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
        
        print(f"to csv at path: {output_file}")
        result_df.to_csv(output_file, index=False)
        
        # 限制返回的数据记录为前10条
        print("filter result...")
        data_records = result_df.head(10).to_dict(orient='records')
        
        return jsonify({
            'status': 'success',
            'message': 'Finder processing completed successfully',
            'output_file': output_file,
            'row_count': len(result_df),
            'data': data_records
        })
        
    except Exception as e:
        print(f"Error in process_finder: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

        
if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000,debug=True)
