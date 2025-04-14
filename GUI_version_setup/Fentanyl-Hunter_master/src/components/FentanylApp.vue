<script setup lang="ts">
import { ref, watch } from 'vue';
import Header from './Header.vue';
import TabNav from './TabNav.vue';
import FentanylFinder from './FentanylFinder.vue';
import FentanylID from './FentanylID.vue';

const tabNavRef = ref<{ activeTab: string } | null>(null);
const activeTab = ref('finder');

// 监听标签页变化
watch(() => tabNavRef.value?.activeTab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab;
  }
});
</script>

<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header" height="auto" style="padding: 0;">
        <Header />
      </el-header>
      <el-main class="main-content">
        <TabNav ref="tabNavRef" />
        <div class="tab-content">
          <FentanylID v-if="activeTab === 'id'" />
          <FentanylFinder v-else-if="activeTab === 'finder'" />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  background-color: #fff;
}

.app-header {
  padding: 0;
}

.main-content {
  padding: 20px;
}

.tab-content {
  padding: 20px;
  background-color: transparent;
}
</style>