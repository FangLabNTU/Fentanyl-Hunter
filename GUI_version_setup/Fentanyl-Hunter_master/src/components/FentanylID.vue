<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox, ElTable, ElTableColumn, ElDialog } from 'element-plus';
import 'element-plus/es/components/message/style/css';
import 'element-plus/es/components/message-box/style/css';
import 'element-plus/es/components/table/style/css';
import 'element-plus/es/components/table-column/style/css';
import 'element-plus/es/components/dialog/style/css';

const inputFilePath = ref('');
const addVirtualNodes = ref(false);
const similarityThreshold = ref(0.5);
const massThreshold = ref(0.1);
const outputDirectory = ref('');
const baseFileName = 'result';

// 动态计算输出文件名
const outputFileName = computed(() => {
  return addVirtualNodes.value 
    ? `${baseFileName}_add_virtual_fentanyl_node.xlsx`
    : `${baseFileName}.xlsx`;
});

const isProcessing = ref(false);
const statusMessage = ref('');
const progressPercentage = ref(0);
const showProgress = ref(false);
const resultData = ref<any[]>([]);
const showResultDialog = ref(false);

const browse = async (type: string) => {
  try {
    if (type === 'input') {
      const filters: { name: string; extensions: string[] }[] = [
        { name: 'CSV Files', extensions: ['csv'] }
      ];
      const filePath = await (window as any).electronAPI.selectFile({ filters });
      if (filePath) {
        inputFilePath.value = filePath;
      }
    } else if (type === 'output') {
      const dirPath = await (window as any).electronAPI.selectSaveDirectory();
      if (dirPath) {
        outputDirectory.value = dirPath;
      }
    }
  } catch (error) {
    console.error('Error selecting path:', error);
    ElMessage.error('Failed to select path');
  }
};

// 模拟进度增加
const simulateProgress = () => {
  progressPercentage.value = 0;
  showProgress.value = true;
  
  // 模拟进度增加，最多到95%
  const interval = setInterval(() => {
    if (progressPercentage.value < 95) {
      // 进度增加速度随机，模拟真实处理
      const increment = Math.random() * 5 + 1;
      progressPercentage.value = Math.min(95, progressPercentage.value + increment);
    } else {
      clearInterval(interval);
    }
  }, 300);

  return interval;
};

const startProcess = async () => {
  if (!inputFilePath.value || !outputDirectory.value) {
    ElMessage.warning('Please select input file and output directory');
    return;
  }

  try {
    isProcessing.value = true;
    statusMessage.value = 'Processing...';
    
    // 开始模拟进度
    const progressInterval = simulateProgress();

    // 先处理文件路径
    const outputPath = await (window as any).electronAPI.joinPath(outputDirectory.value, outputFileName.value);
    console.log('Output file path:', outputPath);

    const response = await axios.post('http://127.0.0.1:5000/api/v1/id', {
      file_path: inputFilePath.value,
      add_nodes: addVirtualNodes.value ? 1 : 0,
      similarity_threshold: similarityThreshold.value,
      ms_threshold: massThreshold.value,
      output_file: outputPath
    });

    // 请求完成后，进度到100%
    clearInterval(progressInterval);
    progressPercentage.value = 100;
    
    // 更详细的API响应日志
    console.log('API Response received:', response.status, response.statusText);
    console.log('Response data type:', typeof response.data);
    console.log('Response data keys:', response.data ? Object.keys(response.data) : 'No data');
    console.log('Response data:', response.data);
    console.log('Response status:', response.data?.status);
    console.log('Response message:', response.data?.message);
    console.log('Has data property:', response.data?.data ? 'Yes' : 'No');
    console.log('Data property type:', response.data?.data ? typeof response.data.data : 'N/A');
    console.log('Is data an array:', response.data?.data ? Array.isArray(response.data.data) : 'N/A');
    
    // 短暂延迟后显示成功信息
    setTimeout(() => {
      // 更详细地检查和处理数据
      let dataToProcess = null;
      
      // 检查各种可能的数据结构情况
      if (response.data?.data && Array.isArray(response.data.data)) {
        console.log('Found data array in response.data.data');
        dataToProcess = response.data.data;
      } else if (Array.isArray(response.data)) {
        console.log('Found data array directly in response.data');
        dataToProcess = response.data;
      } else if (response.data && typeof response.data === 'object') {
        // 尝试从对象中查找数组属性
        for (const key in response.data) {
          if (Array.isArray(response.data[key]) && response.data[key].length > 0) {
            console.log(`Found data array in response.data.${key}`);
            dataToProcess = response.data[key];
            break;
          }
        }
      }
      
      // 如果找到了数据，处理它
      if (dataToProcess && dataToProcess.length > 0) {
        console.log(`Processing ${dataToProcess.length} records`);
        resultData.value = dataToProcess;
        console.log('Data processed successfully:', resultData.value.length, 'records');
      } else {
        console.warn('Could not find any data array in the response');
      }
      
      // 确定是否成功的更宽松逻辑
      const isSuccess = 
        response.status === 200 || 
        (response.data && (
          response.data.status === 'success' || 
          response.data.status?.toString().toLowerCase() === 'success' ||
          (dataToProcess && dataToProcess.length > 0)
        ));
      
      if (isSuccess) {
        // 使用API返回的消息或默认成功消息
        statusMessage.value = response.data?.message || 'Processing completed successfully!';
        
        ElMessageBox.alert(statusMessage.value, 'Success', {
          confirmButtonText: 'OK',
          type: 'success',
          center: true,
          callback: () => {
            // 当用户点击OK按钮时，如果有数据则显示结果表格
            console.log('Dialog OK button clicked. Data records:', resultData.value.length);
            showResultsDialog(); // 使用专门的函数显示对话框
          }
        });
      } else {
        console.error('Response indicates failure. Status:', response.data?.status);
        // 即使状态不是success，如果有message也尝试显示
        if (response.data?.message) {
          statusMessage.value = response.data.message;
          ElMessage.warning(statusMessage.value);
        } else {
          statusMessage.value = `Failed: ${response.data?.error || 'Unknown error'}`;
          ElMessage.error(response.data?.error || 'Processing failed');
        }
      }
      // 延迟隐藏进度条
      setTimeout(() => {
        showProgress.value = false;
      }, 500);
    }, 500);
    
  } catch (error: any) {
    // 如果发生错误，进度停止
    progressPercentage.value = 0;
    showProgress.value = false;
    
    console.error('Error processing:', error);
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
    statusMessage.value = `Failed: ${errorMsg}`;
    ElMessage.error(errorMsg);
  } finally {
    isProcessing.value = false;
  }
};

// 显示结果对话框的函数
const showResultsDialog = async () => {
  if (resultData.value.length > 0) {
    console.log('Showing dialog with data records:', resultData.value.length);
    showResultDialog.value = true;
    await nextTick();
    console.log('Dialog should be visible now');
  } else {
    console.warn('Attempted to show dialog but no data available');
  }
};
</script>

<template>
  <div class="finder-container">
    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Data path</div>
      </template>
      <div class="input-group">
        <span class="input-label">Fentanyl nodes file (.csv) path:</span>
        <div class="file-input">
          <el-input v-model="inputFilePath" readonly placeholder="Select file..." />
          <el-button type="primary" @click="browse('input')" plain>Browse</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Settings</div>
      </template>
      <div class="checkbox-group">
        <el-checkbox v-model="addVirtualNodes" label="Add virtual fentanyl nodes" />
      </div>
    </el-card>

    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Multilayer molecular network parameters</div>
      </template>
      <div class="parameters-box">
        <el-card shadow="hover" class="parameter-group">
          <template #header>
            <div class="parameter-title">Spectral similarity</div>
          </template>
          <div class="input-group">
            <span class="input-label">Score cut off:</span>
            <el-input-number v-model="similarityThreshold" :min="0" :max="1" :step="0.1" :precision="1" controls-position="right" />
          </div>
        </el-card>

        <el-card shadow="hover" class="parameter-group">
          <template #header>
            <div class="parameter-title">Paired mass distances</div>
          </template>
          <div class="input-group">
            <span class="input-label">Mass tolerance:</span>
            <el-input-number v-model="massThreshold" :min="0" :max="1" :step="0.01" :precision="2" controls-position="right" />
          </div>
        </el-card>
      </div>
    </el-card>

    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Output path</div>
      </template>
      <div class="input-group">
        <span class="input-label">Result directory:</span>
        <div class="file-input">
          <el-input v-model="outputDirectory" readonly placeholder="Select directory..." />
          <el-button type="primary" @click="browse('output')" plain>Browse</el-button>
        </div>
      </div>
    </el-card>

    <div class="action-buttons">
      <el-button 
        type="primary" 
        @click="startProcess"
        :loading="isProcessing"
        size="large">
        {{ isProcessing ? 'Processing...' : 'Start' }}
      </el-button>
    </div>

    <!-- 进度条 -->
    <div class="progress-container" v-if="showProgress">
      <el-progress 
        :percentage="progressPercentage" 
        :status="progressPercentage === 100 ? 'success' : ''" 
        :stroke-width="20"
        :show-text="true">
        <span class="progress-text">{{ progressPercentage < 100 ? 'Processing...' : 'Completed!' }}</span>
      </el-progress>
    </div>

    <div class="status-bar" v-if="statusMessage && !showProgress">
      <el-alert
        :title="statusMessage"
        :type="statusMessage.includes('Failed') ? 'error' : 'success'"
        :closable="false"
        center
        show-icon
      />
    </div>
    
    <!-- 结果数据对话框 -->
    <el-dialog
      v-model="showResultDialog"
      @update:modelValue="val => showResultDialog = val"
      title="Results"
      width="90%"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      :append-to-body="true"
      :destroy-on-close="false"
    >
      <template #default>
      <div v-if="resultData.length > 0">
        <div class="dialog-info">
          <span>Total <strong>{{ resultData.length }}</strong> records</span>
        </div>
        <el-table :data="resultData" height="500" style="width: 100%" border stripe>
          <el-table-column
            v-for="(_, key) in resultData[0]"
            :key="key.toString()"
            :prop="key.toString()"
            :label="key.toString()"
            :min-width="120"
            show-overflow-tooltip
          />
        </el-table>
      </div>
      <div v-else class="no-data">
        <p>No data to display</p>
      </div>
      </template>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="showResultDialog = false">Close</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.finder-container {
  padding: 20px;
  text-align: left;
  background: transparent;
}

.section {
  margin-bottom: 20px;
  background: #fff;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.parameters-box {
  padding: 15px;
  background: transparent;
  border: none;
  display: flex;
  flex-direction: row;
  gap: 20px;
  flex-wrap: wrap;
}

.parameter-group {
  margin-bottom: 0;
  flex: 1;
  min-width: 300px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.parameter-group:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.parameter-title {
  font-weight: bold;
  color: #333;
}

.input-group {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.input-label {
  min-width: 160px;
  color: #606266;
  font-weight: normal;
}

.parameter-group .el-input-number {
  width: calc(100% - 170px);
  max-width: 200px;
}

.file-input {
  display: flex;
  flex: 1;
  gap: 10px;
}

.checkbox-group {
  padding: 10px;
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
  margin-bottom: 20px;
}

.progress-container {
  margin: 20px 0;
}

.progress-text {
  font-size: 14px;
  font-weight: bold;
}

.status-bar {
  margin-top: 20px;
}

.dialog-info {
  margin-bottom: 15px;
  font-size: 14px;
  color: #606266;
}

.no-data {
  text-align: center;
  padding: 30px;
  color: #909399;
  font-size: 16px;
}

/* 响应式布局 */
@media screen and (max-width: 768px) {
  .parameters-box {
    flex-direction: column;
  }
  
  .parameter-group {
    width: 100%;
  }
  
  .input-label {
    min-width: 100%;
    margin-bottom: 5px;
  }
  
  .parameter-group .el-input-number {
    width: 100%;
    max-width: none;
  }
  
  .file-input {
    flex-direction: column;
    width: 100%;
  }
  
  .file-input .el-button {
    margin-top: 10px;
  }
}
</style>