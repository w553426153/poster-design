<!--
 * @Author: ShawnPhang
 * @Date: 2022-01-10 14:57:53
 * @Description: Psd文件解析
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @LastEditTime: 2025-01-15 22:05:57
-->
<template>
  <div class="psd-container">
    <div class="header">
      <h1>PSD 文件处理工具</h1>
      <p>上传 PSD 文件以移除文本图层并处理图像</p>
    </div>
    
    <div class="content">
      <PSDUploader @processed="onProcessed" />
    </div>
    
    <div class="features">
      <h2>功能特点</h2>
      <el-row :gutter="20">
        <el-col :span="8" v-for="(feature, index) in features" :key="index">
          <el-card class="feature-card">
            <div class="feature-icon">
              <el-icon :size="32">
                <component :is="feature.component" />
              </el-icon>
            </div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Document, Picture, Download } from '@element-plus/icons-vue'
import PSDUploader from '@/components/PSDUploader.vue'
import { useRouter } from 'vue-router'
import { useCanvasStore, useWidgetStore } from '@/store'
import { wTextSetting } from '@/components/modules/widgets/wText/wTextSetting'
import wImageSetting from '@/components/modules/widgets/wImage/wImageSetting'
import { getFileUrl } from '@/api/psd'

// 走后端接口封装：页面仅负责展示与上传，处理逻辑由 PSDUploader + src/api/psd.ts 调用后端 /api/psd/process
type TFeature = { title: string; description: string; component: any }
const features: TFeature[] = [
  {
    title: 'PSD 解析（后端）',
    description: '由后端统一解析与处理，结果可下载',
    component: Document
  },
  {
    title: '智能去文字',
    description: '后端使用 OCR 检测并移除文本图层',
    component: Picture
  },
  {
    title: '多种格式导出',
    description: '支持 PNG、JPG 等图片格式导出',
    component: Download
  }
]

const router = useRouter()
const pageStore = useCanvasStore()
const widgetStore = useWidgetStore()

const types: any = {
  text: wTextSetting,
  image: wImageSetting,
}

function onProcessed(res: any) {
  try {
    const data = res?.canvas
    if (!data) return
    const { width, height, background, clouds } = data
    // 设置画布
    pageStore.setDPage(Object.assign(pageStore.dPage, {
      width,
      height,
      backgroundColor: background?.color || '#ffffff00',
      backgroundImage: background?.image_url ? getFileUrl(background.image_url) : ''
    }))
    // 清空并注入图层
    widgetStore.setDWidgets([])
    for (let i = 0; i < (clouds?.length || 0); i++) {
      const x: any = clouds[i]
      const raw = JSON.parse(JSON.stringify(types[x.type])) || {}
      delete x.type
      if (x.image_url) x.imgUrl = getFileUrl(x.image_url)
      widgetStore.addWidget(Object.assign(raw, x))
    }
    // 跳转到主编辑页
    router.push('/home')
  } catch (e) {
    console.error('Render canvas failed:', e)
  }
}
</script>

<style scoped>
.psd-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 1rem;
  font-weight: 600;
}

.header p {
  font-size: 1.1rem;
  color: #666;
  margin: 0;
}

.content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.features {
  margin-top: 3rem;
}

.features h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #2c3e50;
  font-size: 1.8rem;
}

.feature-card {
  height: 100%;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: none;
  border-radius: 10px;
  padding: 1.5rem;
  background: #f9fafc;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e6f7ff;
  border-radius: 50%;
  color: #1890ff;
}

.feature-card h3 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  color: #2c3e50;
}

.feature-card p {
  color: #666;
  line-height: 1.5;
  margin: 0;
}

/* Responsive adjustments */
@media (max-width: 992px) {
  .psd-container {
    padding: 1rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .feature-card {
    margin-bottom: 1rem;
  }
}

@media (max-width: 768px) {
  .header {
    padding: 1.5rem 1rem;
  }
  
  .header h1 {
    font-size: 1.75rem;
  }
  
  .content {
    padding: 1.5rem;
  }
}

/* Animation for the upload area */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.el-upload-dragger) {
  animation: fadeIn 0.5s ease-out;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 3rem 1.5rem;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #1890ff;
  background-color: #f5f9ff;
}
</style>

<style lang="less" scoped>
@import url('@/assets/styles/design.less');
.uploader {
  position: absolute;
  z-index: 999;
  left: 50%;
  transform: translate(-50%, -50%);
  top: 50%;
  &__box {
    color: #666666;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
  }
}
.v-tips {
  padding: 0 1rem;
  font-size: 15px;
  color: #666666;
}
</style>
