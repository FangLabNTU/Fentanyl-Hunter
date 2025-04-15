<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox, ElTable, ElTableColumn, ElDialog } from 'element-plus';
import 'element-plus/es/components/message/style/css';
import 'element-plus/es/components/message-box/style/css';
import 'element-plus/es/components/table/style/css';
import 'element-plus/es/components/table-column/style/css';
import 'element-plus/es/components/dialog/style/css';

const peakFilePath = ref('');
const snThreshold = ref(3);
const areaThreshold = ref(10000);
const mzThreshold = ref(0.005);
const rtThreshold = ref(0.2);
const outputDirectory = ref('');
const outputFileName = 'Predicted.csv';
const isProcessing = ref(false);
const statusMessage = ref('');
const progressPercentage = ref(0);
const showProgress = ref(false);
const resultData = ref<any[]>([]);
const showResultDialog = ref(false);
const jsonInput = ref(''); // 用于测试直接输入JSON的字段
const showDevTools = ref(false); // 控制开发工具是否显示

// 尝试检测是否为开发环境
const isDev = (): boolean => {
  try {
    // 尝试使用Vue的环境变量
    if (import.meta && import.meta.env && import.meta.env.DEV !== undefined) {
      return import.meta.env.DEV === true;
    }
    // 如果上面的方法不可用，使用window.location检查
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1' ||
           window.location.hostname.includes('192.168.');
  } catch (e) {
    // 发生错误时，默认为false
    console.warn('检测开发环境失败，默认为生产环境', e);
    return false;
  }
};

// 组件挂载时，自动设置开发工具显示状态
onMounted(() => {
  showDevTools.value = isDev();
});

const browse = async (type: string) => {
  try {
    if (type === 'peak') {
      const filters: { name: string; extensions: string[] }[] = [
        { name: 'Text Files', extensions: ['txt'] }
      ];
      const filePath = await (window as any).electronAPI.selectFile({ filters });
      if (filePath) {
        peakFilePath.value = filePath;
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

// 处理数据中的NaN值，将其转换为更友好的显示
const processDataForDisplay = (data: any[]) => {
  return data.map(item => {
    const processedItem: Record<string, any> = {};
    
    for (const key in item) {
      // 检查值是否为NaN，如果是则转换为'-'
      processedItem[key] = item[key] === null || (typeof item[key] === 'number' && isNaN(item[key])) 
        ? '-' 
        : item[key];
    }
    
    return processedItem;
  });
};

// 处理JSON字符串中的NaN值，将其替换为空字符串
const sanitizeJsonString = (jsonString: string): string => {
  // 替换各种形式的NaN值
  let sanitized = jsonString;
  
  // 替换独立的NaN
  sanitized = sanitized.replace(/:\s*NaN\s*([,}])/g, ': "" $1');
  
  // 替换小写形式的"nan"
  sanitized = sanitized.replace(/:\s*"nan"\s*([,}])/g, ': "" $1');
  
  // 替换nan（不带引号）
  sanitized = sanitized.replace(/:\s*nan\s*([,}])/g, ': "" $1');
  
  // 替换带前后空格的NaN
  sanitized = sanitized.replace(/:\s*"[\s]*NaN[\s]*"\s*([,}])/g, ': "" $1');
  
  // 替换null为空字符串（如果需要的话）
  // sanitized = sanitized.replace(/:\s*null\s*([,}])/g, ': "" $1');
  
  console.log('JSON已预处理，替换NaN值为空字符串');
  return sanitized;
};

// 创建一个自定义的JSON解析器，处理NaN值
const safeJSONParse = (jsonString: string): any => {
  try {
    // 首先尝试使用标准方法解析
    return JSON.parse(jsonString);
  } catch (e) {
    console.warn('标准JSON解析失败，尝试预处理后再解析', e);
    
    try {
      // 如果标准方法失败，尝试预处理后再解析
      const sanitizedJson = sanitizeJsonString(jsonString);
      return JSON.parse(sanitizedJson);
    } catch (e2) {
      console.error('预处理后解析仍然失败', e2);
      throw e2; // 重新抛出错误
    }
  }
};

// 专门处理后端API响应的函数
const extractDataFromResponse = (responseData: any): any[] | null => {
  // 如果是字符串，先尝试安全解析
  if (typeof responseData === 'string') {
    try {
      // 使用安全解析方法
      responseData = safeJSONParse(responseData);
      console.log('成功将JSON字符串解析为对象');
    } catch (e) {
      console.error('解析JSON字符串失败:', e);
      return null;
    }
  }
  
  // 检查是否有data属性，并且是数组
  if (responseData?.data && Array.isArray(responseData.data)) {
    console.log('从response.data提取数组，长度:', responseData.data.length);
    return responseData.data;
  }
  
  // 检查自身是否是数组
  if (Array.isArray(responseData)) {
    console.log('响应本身是数组，长度:', responseData.length);
    return responseData;
  }
  
  // 搜索对象中的所有属性，查找第一个是数组的属性
  if (responseData && typeof responseData === 'object') {
    for (const key in responseData) {
      if (Array.isArray(responseData[key]) && responseData[key].length > 0) {
        console.log(`在response.${key}中找到数组，长度:`, responseData[key].length);
        return responseData[key];
      }
    }
  }
  
  // 没有找到任何数组数据
  console.warn('在响应中未找到任何数组数据');
  return null;
};

// 显示结果对话框的函数
const showResultsDialog = async () => {
  if (resultData.value.length > 0) {
    console.log('Showing dialog with data records:', resultData.value.length);
    showResultDialog.value = true;
    
    // 等待Vue更新DOM
    await nextTick();
    
    // 强制DOM更新以确保表格正确显示
    setTimeout(() => {
      console.log('Dialog should be visible now with', resultData.value.length, 'records');
    }, 100);
  } else {
    console.warn('Attempted to show dialog but no data available');
    ElMessage.warning('No data available to display');
  }
};

const startProcess = async () => {
  if (!peakFilePath.value || !outputDirectory.value) {
    ElMessage.warning('Please select input file and output directory');
    return;
  }

  try {
    isProcessing.value = true;
    statusMessage.value = 'Processing...';
    
    // 开始模拟进度
    const progressInterval = simulateProgress();

    // 记录请求开始时间
    console.log('Sending request to finder API...');
    
    // 先处理文件路径
    const outputPath = await (window as any).electronAPI.joinPath(outputDirectory.value, outputFileName);
    console.log('Output file path:', outputPath);
    
    const response = await axios.post('http://127.0.0.1:5000/api/v1/finder', {
      file_path: peakFilePath.value,
      sn_threshold: snThreshold.value,
      area_threshold: areaThreshold.value,
      mz_threshold: mzThreshold.value,
      rt_threshold: rtThreshold.value,
      output_file: outputPath
    });

    // 请求完成后，进度到100%
    clearInterval(progressInterval);
    progressPercentage.value = 100;
    
    // 添加更详细的日志输出
    console.log('API Response received:', response.status, response.statusText);
    console.log('Response data type:', typeof response.data);
    
    // 处理可能的字符串响应
    let processedResponseData = response.data;
    if (typeof response.data === 'string') {
      try {
        // 使用安全解析方法
        processedResponseData = safeJSONParse(response.data);
        console.log('成功将JSON字符串解析为对象');
      } catch (e) {
        console.error('解析JSON字符串失败:', e);
      }
    }
    
    // 使用处理后的响应数据
    console.log('Response data keys:', processedResponseData ? Object.keys(processedResponseData) : 'No data');
    console.log('Response data:', processedResponseData);
    
    // 添加更多详细日志用于调试数据结构
    console.log('Full response data structure:', JSON.stringify(processedResponseData, null, 2));
    if (processedResponseData && typeof processedResponseData === 'object') {
      // 检查数据属性是否存在
      if ('data' in processedResponseData) {
        console.log('Data property exists with type:', typeof processedResponseData.data);
        console.log('Is data property an array:', Array.isArray(processedResponseData.data));
        console.log('Data property length:', Array.isArray(processedResponseData.data) ? processedResponseData.data.length : 'not an array');
        if (Array.isArray(processedResponseData.data) && processedResponseData.data.length > 0) {
          console.log('First item in data array:', processedResponseData.data[0]);
        }
      } else {
        console.log('No "data" property found in response data');
      }
    }
    
    console.log('Response status:', processedResponseData?.status);
    console.log('Response message:', processedResponseData?.message);
    console.log('Has data property:', processedResponseData?.data ? 'Yes' : 'No');
    console.log('Data property type:', processedResponseData?.data ? typeof processedResponseData.data : 'N/A');
    console.log('Is data an array:', processedResponseData?.data ? Array.isArray(processedResponseData.data) : 'N/A');
    console.log('Type of status:', typeof processedResponseData?.status);
    
    // 短暂延迟后显示成功信息
    setTimeout(() => {
      // 使用专门的函数提取数据
      const extractedData = extractDataFromResponse(processedResponseData);
      
      if (extractedData && extractedData.length > 0) {
        console.log(`Processing ${extractedData.length} records`);
        resultData.value = processDataForDisplay(extractedData);
        console.log('Data processed successfully:', resultData.value.length, 'records');
        
        // 成功处理数据后立即更新状态消息
        statusMessage.value = processedResponseData?.message || 'Processing completed successfully!';
        
        // 显示成功消息并设置回调以显示结果对话框
        ElMessageBox.alert(statusMessage.value, 'Success', {
          confirmButtonText: 'OK',
          type: 'success',
          center: true,
          callback: () => {
            // 当用户点击OK按钮时显示结果表格
            console.log('About to show results dialog with', resultData.value.length, 'records');
            showResultsDialog();
          }
        });
      } else {
        console.warn('No data found after extraction attempt');
        // 如果没有找到数据但状态是成功，仍然显示成功消息
        if (processedResponseData?.status === 'success' || response.status === 200) {
          statusMessage.value = processedResponseData?.message || 'Processing completed successfully!';
          ElMessage.success(statusMessage.value);
        } else {
          statusMessage.value = `Failed to process data: No data found in response`;
          ElMessage.warning(statusMessage.value);
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
    // 尝试从错误对象获取错误消息
    let errorMsg = 'Unknown error';
    
    if (error.response?.data?.error) {
      // API返回的错误
      errorMsg = error.response.data.error;
    } else if (error.message) {
      // JavaScript错误对象的消息
      errorMsg = error.message;
    }
    
    statusMessage.value = `Failed: ${errorMsg}`;
    ElMessage.error(errorMsg);
  } finally {
    isProcessing.value = false;
  }
};

// 处理直接输入的JSON字符串（用于测试）
const processJsonInput = () => {
  if (!jsonInput.value.trim()) {
    ElMessage.warning('请输入JSON数据');
    return;
  }

  try {
    // 使用安全解析方法
    const parsedData = safeJSONParse(jsonInput.value);
    console.log('成功解析JSON');
    
    // 提取数据
    const extractedData = extractDataFromResponse(parsedData);
    
    if (extractedData && extractedData.length > 0) {
      console.log(`处理${extractedData.length}条记录`);
      resultData.value = processDataForDisplay(extractedData);
      statusMessage.value = '成功处理JSON数据';
      
      // 显示结果对话框
      showResultsDialog();
    } else {
      statusMessage.value = '未能从JSON中提取数据';
      ElMessage.warning(statusMessage.value);
    }
  } catch (e) {
    console.error('处理JSON输入失败:', e);
    statusMessage.value = `处理失败: ${e}`;
    ElMessage.error(statusMessage.value);
  }
};
</script>

<template>
  <div class="id-container">
    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Data path</div>
      </template>
      <div class="input-group">
        <span class="input-label">Peak table file (.txt) path:</span>
        <div class="file-input">
          <el-input v-model="peakFilePath" readonly placeholder="Select file..." />
          <el-button type="primary" @click="browse('peak')" plain>Browse</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="section">
      <template #header>
        <div class="section-title">Peak cleaning parameters</div>
      </template>
      <div class="parameters-box">
        <el-card shadow="hover" class="parameter-group">
          <template #header>
            <div class="parameter-title">Noise remove</div>
          </template>
          <div class="input-group">
            <span class="input-label">S/N threshold:</span>
            <el-input-number v-model="snThreshold" :min="0" :step="1" controls-position="right" />
          </div>
          <div class="input-group">
            <span class="input-label">Minimum peak area:</span>
            <el-input-number v-model="areaThreshold" :min="0" :step="1000" controls-position="right" />
          </div>
        </el-card>

        <el-card shadow="hover" class="parameter-group">
          <template #header>
            <div class="parameter-title">Duplicates remove</div>
          </template>
          <div class="input-group">
            <span class="input-label">MS1 tolerance:</span>
            <el-input-number v-model="mzThreshold" :min="0" :max="1" :step="0.001" :precision="3" controls-position="right" />
          </div>
          <div class="input-group">
            <span class="input-label">Retention time tolerance:</span>
            <el-input-number v-model="rtThreshold" :min="0" :step="0.1" :precision="1" controls-position="right" />
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

    <!-- 开发测试区域：JSON直接输入 -->
    <el-card v-if="showDevTools" shadow="never" class="section dev-section">
      <template #header>
        <div class="section-title">
          开发测试工具 
          <el-switch 
            v-model="showDevTools" 
            active-text="显示" 
            inactive-text="隐藏"
            inline-prompt
            size="small"
            style="margin-left: 10px;"
          />
        </div>
      </template>
      <div class="dev-tools">
        <el-input
          v-model="jsonInput"
          type="textarea"
          placeholder="粘贴需要测试的JSON数据..."
          :rows="5"
          resize="both"
        />
        <div class="dev-buttons">
          <el-button type="primary" @click="processJsonInput">处理JSON</el-button>
          <el-button @click="jsonInput = ''">清空</el-button>
        </div>
      </div>
    </el-card>

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
        :type="statusMessage.toLowerCase().includes('failed') ? 'error' : 'success'"
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
.id-container {
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

/* 开发测试区域样式 */
.dev-section {
  margin-top: 20px;
  border: 1px dashed #e6a23c;
  background-color: #fdf6ec;
}

.dev-tools {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dev-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

/* 响应式布局 */
@media screen and (max-width: 768px) {
  .parameters-box {
    flex-direction: column; /* 在小屏幕上恢复为纵向排列 */
  }
  
  .parameter-group {
    width: 100%; /* 小屏幕上占满宽度 */
  }
  
  .input-label {
    min-width: 100%; /* 标签占满一行 */
    margin-bottom: 5px;
  }
  
  .parameter-group .el-input-number {
    width: 100%; /* 输入框占满宽度 */
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