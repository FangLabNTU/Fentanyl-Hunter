import os
import sys
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import spectral_entropy
import joblib
from tqdm import tqdm
import webbrowser
from threading import Timer

def resource_path(relative_path):
    """获取资源的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    # 确保路径中的斜杠方向一致
    relative_path = relative_path.replace('/', os.sep).replace('\\', os.sep)
    if relative_path.startswith('./'):
        relative_path = relative_path[2:]
    
    return os.path.join(base_path, relative_path)

app = Flask(__name__)

# 这里是您原来的process_id_logic和process_finder_logic函数
# ... (保持不变)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Mass Spectrometry Analysis API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
                pre { background: #f5f5f5; padding: 10px; }
                .status { color: #4CAF50; }
            </style>
        </head>
        <body>
            <h1>Mass Spectrometry Analysis API</h1>
            <div class="status">Server is running...</div>
            
            <div class="endpoint">
                <h2>Finder API</h2>
                <p>Endpoint: <code>/api/v1/finder</code></p>
                <p>Method: POST</p>
                <p>Example Request:</p>
                <pre>
{
    "file_path": "./Finder/Met-fentanyl.txt",
    "output_file": "./Finder/Predicted.csv",
    "sn_threshold": 3,
    "area_threshold": 10000,
    "mz_threshold": 0.005,
    "rt_threshold": 0.2
}
                </pre>
            </div>

            <div class="endpoint">
                <h2>ID API</h2>
                <p>Endpoint: <code>/api/v1/id</code></p>
                <p>Method: POST</p>
                <p>Example Request:</p>
                <pre>
{
    "file_path": "./ID/Predicted.csv",
    "output_file": "./ID/result1.xlsx",
    "similarity_threshold": 0.5,
    "ms_threshold": 0.1,
    "add_nodes": 1,
    "nodes_table_path": "./ID/Virtual_nodes.xlsx",
    "pmd_table_path": "./ID/PMD.xlsx"
}
                </pre>
            </div>
        </body>
    </html>
    """

@app.route('/api/v1/id', methods=['POST'])
def process_id():
    try:
        data = request.get_json()
        
        required_params = ['file_path', 'similarity_threshold', 'ms_threshold']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # 修改文件路径处理
        file_path = resource_path(data['file_path'])
        output_path = resource_path(data.get('output_file', 'ID/result1.xlsx'))
        nodes_path = resource_path(data.get('nodes_table_path', 'ID/Virtual_nodes.xlsx'))
        pmd_path = resource_path(data.get('pmd_table_path', 'ID/PMD.xlsx'))
        
        # 添加路径检查和错误处理
        if not os.path.exists(file_path):
            return jsonify({'error': f'Input file not found: {file_path}'}), 404
        if not os.path.exists(nodes_path):
            return jsonify({'error': f'Nodes file not found: {nodes_path}'}), 404
        if not os.path.exists(pmd_path):
            return jsonify({'error': f'PMD file not found: {pmd_path}'}), 404
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 读取输入文件
        peak_table = pd.read_csv(file_path)
        peak_table = peak_table[peak_table['Predicted Label'] == 1]
        
        # 处理节点表
        if data.get('add_nodes', 1) == 1:
            nodes_table = pd.read_excel(nodes_path)
            peak_table = pd.concat([peak_table, nodes_table], ignore_index=True)
        
        # 读取 PMD 表
        pmd_table = pd.read_excel(pmd_path)
        
        # 执行处理逻辑
        result_df = process_id_logic(
            peak_table,
            nodes_table if data.get('add_nodes', 1) == 1 else None,
            pmd_table,
            float(data['similarity_threshold']),
            float(data['ms_threshold'])
        )
        
        # 保存结果
        result_df.to_excel(output_path, index=False)
        
        return jsonify({
            'status': 'success',
            'message': 'ID processing completed successfully',
            'output_file': output_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/finder', methods=['POST'])
def process_finder():
    try:
        data = request.get_json()
        
        required_params = ['file_path', 'sn_threshold', 'area_threshold', 'mz_threshold', 'rt_threshold']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # 修改文件路径处理
        file_path = resource_path(data['file_path'])
        output_path = resource_path(data.get('output_file', 'Finder/Predicted.csv'))
        model_path = resource_path('Finder/Fentanyl_Finder.pkl')
        
        # 添加路径检查和错误处理
        if not os.path.exists(file_path):
            return jsonify({'error': f'Input file not found: {file_path}'}), 404
        if not os.path.exists(model_path):
            return jsonify({'error': f'Model file not found: {model_path}'}), 404
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        input_data = pd.read_csv(file_path, sep="\t")
        best_rf_model = joblib.load(model_path)
        
        result_df = process_finder_logic(
            input_data,
            float(data['sn_threshold']),
            float(data['area_threshold']),
            float(data['mz_threshold']),
            float(data['rt_threshold']),
            best_rf_model
        )
        
        result_df.to_csv(output_path, index=False)
        
        return jsonify({
            'status': 'success',
            'message': 'Finder processing completed successfully',
            'output_file': output_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(host='127.0.0.1', port=5000) 