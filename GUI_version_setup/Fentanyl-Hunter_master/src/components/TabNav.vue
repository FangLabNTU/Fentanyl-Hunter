<script setup lang="ts">
import { ref } from 'vue';

const activeTab = ref('finder');

defineExpose({ activeTab });
</script>

<template>
  <el-tabs v-model="activeTab" class="tab-nav" type="card">
    <el-tab-pane label="Fentanyl Finder" name="finder"></el-tab-pane>
    <el-tab-pane label="Fentanyl ID" name="id"></el-tab-pane>
  </el-tabs>
</template>

<style scoped>
.tab-nav {
  margin-bottom: 20px;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__item.is-active) {
  font-weight: bold;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 20px;
  height: 40px;
  line-height: 40px;
}
</style>