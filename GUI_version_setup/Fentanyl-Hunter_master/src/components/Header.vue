<script setup lang="ts">
// Header组件，显示应用标题和帮助按钮
import { ref } from 'vue';
import HelpModal from './HelpModal.vue';

const showHelpModal = ref(false);

const toggleHelpModal = () => {
  showHelpModal.value = !showHelpModal.value;
};
</script>

<template>
  <el-menu mode="horizontal" :ellipsis="false" class="header">
    <div class="logo-container">
      <img src="../assets/icon.ai.jpg" alt="Fentanyl-Hunter Logo" class="logo" />
      <h1>Fentanyl-Hunter</h1>
    </div>
    <div class="flex-grow" />
    <div class="nav-links">
      <el-button type="primary" plain size="medium" @click="toggleHelpModal" class="help-btn">
        <span class="help-text">Help</span>
      </el-button>
      <HelpModal :is-open="showHelpModal" @close="showHelpModal = false" />
    </div>
  </el-menu>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  height: 60px;
  border-bottom: 1px solid #f0f0f0;
}

.logo-container {
  display: flex;
  align-items: center;
  margin-left: 20px;
}

.logo {
  height: 40px;
  width: 40px;
  margin-right: 10px;
}

h1 {
  font-size: 24px;
  margin: 0;
  color: #333;
}

.nav-links {
  margin-right: 20px;
}

.help-btn {
  font-weight: 600;
  width: 80px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.help-text {
  font-size: 16px;
}

.flex-grow {
  flex-grow: 1;
}
</style>