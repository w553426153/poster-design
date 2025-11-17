<template>
  <div class="poster-generate-wrap">
    <div class="header">海报生成</div>
    <div class="content">
      <div class="input-group">
        <label for="poster-request">输入需求：</label>
        <textarea
          id="poster-request"
          v-model="state.requestText"
          placeholder="请输入您想要生成的海报需求，例如：科技感的电子产品发布会海报"
          rows="4"
        ></textarea>
      </div>
      <div class="button-group">
        <button class="generate-btn" @click="generatePoster" :disabled="state.generating">
          {{ state.generating ? '生成中...' : '生成海报' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'

const state = reactive({
  requestText: '',
  generating: false
})

const generatePoster = () => {
  if (!state.requestText.trim()) {
    alert('请输入海报生成需求')
    return
  }
  
  state.generating = true
  
  // 这里可以调用实际的API来生成海报
  // 模拟API调用
  setTimeout(() => {
    console.log('生成海报请求:', state.requestText)
    state.generating = false
    alert('海报生成成功！')
  }, 2000)
}
</script>

<style lang="less" scoped>
.poster-generate-wrap {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
  
  .header {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #333;
  }
  
  .content {
    .input-group {
      margin-bottom: 20px;
      
      label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: #555;
      }
      
      textarea {
        width: 100%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        resize: vertical;
        box-sizing: border-box;
        
        &:focus {
          outline: none;
          border-color: #409eff;
        }
      }
    }
    
    .button-group {
      text-align: center;
      
      .generate-btn {
        padding: 10px 20px;
        background-color: #409eff;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover:not(:disabled) {
          background-color: #337ecc;
        }
        
        &:disabled {
          background-color: #a0cfff;
          cursor: not-allowed;
        }
      }
    }
  }
}
</style>