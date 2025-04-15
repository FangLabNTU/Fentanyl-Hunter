<script setup lang="ts">


defineProps<{
  isOpen: boolean
}>();

const emit = defineEmits<{
  'close': []
}>();

const closeModal = () => {
  emit('close');
};
</script>

<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Help Documentation</h2>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <div class="help-content">
          <h3>Fentanyl-Hunter</h3>

          <div class="section">
            <h4>About</h4>
            <p>Fentanyl-Hunter is a specialized program designed for the screening and annotation of compounds within
              the fentanyl family using MS/MS data. This platform is capable of identifying fentanyl, its analogues, and
              metabolites in both biological and environmental samples.</p>
          </div>

          <div class="section">
            <h4>Key Components</h4>
            <p>The platform is composed of two main modules:</p>
            <ul>
              <li><strong>Fentanyl_Finder</strong> – Screens MS features related to fentanyls.</li>
              <li><strong>Fentanyl_ID</strong> – Provides auxiliary structure annotation.</li>
            </ul>
            <p>Both modules are implemented entirely in Python.</p>
          </div>

          <div class="section">
            <h4>Additional Information</h4>
            <p>Additional information and a tutorial can be found in the research article titled:</p>
            <p class="citation">"Machine Learning and Multilayer Molecular Network-Assisted Screening Hunts Unknown
              Fentanyl Compounds with Global Prevalence" (In preparation)</p>
            <p>and the Fentanyl-Hunter GitHub Repository:</p>
            <p><a href="https://github.com/FangLabNTU/Fentanyl-Hunter"
                target="_blank">https://github.com/FangLabNTU/Fentanyl-Hunter</a></p>
            <p>This version improves the flow and clarity of the sentence while maintaining the key information.</p>
          </div>

          <div class="section">
            <h4>Developer Contact Information</h4>
            <ul>
              <li><strong>Changzhi Shi</strong>: czshi22@m.fudan.edu.cn, FangLab, Fudan University</li>
              <li><strong>Wanli Li</strong>: liwanli425@163.com, Shanghai Anti-Doping Laboratory (SAL), Shanghai
                University of Sport</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 90vh;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #000;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(90vh - 70px);
}

.help-content {
  line-height: 1.6;
}

.help-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
  text-align: center;
  font-size: 24px;
  font-weight: bold;
}

.section {
  margin-bottom: 25px;
}

.section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #42b983;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  font-size: 18px;
}

.section p {
  margin: 10px 0;
}

.section a {
  color: #4da6ff;
  text-decoration: none;
  word-break: break-all;
}

.section a:hover {
  text-decoration: underline;
}

.citation {
  font-style: italic;
  color: #555;
  margin: 10px 0;
  padding-left: 15px;
  border-left: 3px solid #42b983;
}

ol,
ul {
  margin: 10px 0;
  padding-left: 20px;
}

li {
  margin-bottom: 8px;
}

li strong {
  color: #2c3e50;
}
</style>