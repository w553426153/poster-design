<!--
 * @Author: ShawnPhang
 * @Date: 2022-02-11 18:48:23
 * @Description: 照片图库 Form:Unsplash无版权图片
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @LastEditTime: 2024-08-14 18:50:09
-->
<template>
  <div class="wrap">
    <div class="upload-panel"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop.prevent="handleDrop"
    >
      <div :class="['drop-zone', { 'drop-zone--active': dragActive }]">
        <i class="iconfont icon-upload" />
        <p class="title">上传图片</p>
        <p class="desc">点击选择文件或拖拽图片到此处</p>
        <el-button type="primary" plain @click="triggerFile">选择图片</el-button>
        <input ref="fileInput" type="file" accept="image/*" multiple class="file-input" @change="handleSelect" />
      </div>
      <ul v-if="recentImages.length" class="recent-list">
        <li v-for="item in recentImages" :key="item.id" class="recent-item" @click="insertImage(item)">
          <img :src="item.src" alt="recent" />
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useControlStore, useCanvasStore, useWidgetStore } from '@/store'
import { storeToRefs } from 'pinia'
import wImageSetting from '../../widgets/wImage/wImageSetting'

const fileInput = ref<HTMLInputElement | null>(null)
const controlStore = useControlStore()
const widgetStore = useWidgetStore()
const { dPage } = storeToRefs(useCanvasStore())
const dragActive = ref(false)
const recentImages = reactive<{ id: string; src: string }[]>([])

const triggerFile = () => {
  fileInput.value?.click()
}

const handleSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (files) {
    handleFiles(files)
    ;(event.target as HTMLInputElement).value = ''
  }
}

const handleDrop = (event: DragEvent) => {
  dragActive.value = false
  const files = event.dataTransfer?.files
  if (files) {
    handleFiles(files)
  }
}

const handleFiles = (files: FileList) => {
  Array.from(files)
    .filter((file) => file.type.startsWith('image/'))
    .forEach((file) => processFile(file))
}

const processFile = async (file: File) => {
  const dataUrl = await readFile(file)
  const { width, height } = await getImageSize(dataUrl)

  controlStore.setShowMoveable(false)
  const setting = JSON.parse(JSON.stringify(wImageSetting))
  setting.width = width
  setting.height = height
  setting.imgUrl = dataUrl
  const { width: pW, height: pH } = dPage.value
  setting.left = pW / 2 - width / 2
  setting.top = pH / 2 - height / 2
  widgetStore.addWidget(setting)

  recentImages.unshift({ id: crypto.randomUUID(), src: dataUrl })
  if (recentImages.length > 6) {
    recentImages.pop()
  }
}

const insertImage = (item: { id: string; src: string }) => {
  processFileFromDataUrl(item.src)
}

const processFileFromDataUrl = async (src: string) => {
  const { width, height } = await getImageSize(src)
  controlStore.setShowMoveable(false)
  const setting = JSON.parse(JSON.stringify(wImageSetting))
  setting.width = width
  setting.height = height
  setting.imgUrl = src
  const { width: pW, height: pH } = dPage.value
  setting.left = pW / 2 - width / 2
  setting.top = pH / 2 - height / 2
  widgetStore.addWidget(setting)
}

const readFile = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const getImageSize = (src: string): Promise<{ width: number; height: number }> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.width, height: img.height })
    img.onerror = reject
    img.src = src
  })
}
</script>

<style lang="less" scoped>
.wrap {
  width: 100%;
  height: 100%;
  padding: 1rem;
  box-sizing: border-box;
}

.upload-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
}

.drop-zone {
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  text-align: center;
  padding: 2rem 1rem;
  transition: all 0.3s ease;
  color: #606266;
}

.drop-zone--active {
  border-color: #409eff;
  background: #f0f6ff;
}

.drop-zone .iconfont {
  font-size: 40px;
  color: #409eff;
}

.drop-zone .title {
  font-size: 18px;
  margin: 0.5rem 0;
}

.drop-zone .desc {
  margin-bottom: 1rem;
}

.file-input {
  display: none;
}

.recent-list {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0;
  padding: 0;
  list-style: none;
}

.recent-item {
  width: 70px;
  height: 70px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
}

.recent-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
