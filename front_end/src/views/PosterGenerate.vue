<template>
  <div class="poster-generate modal-mode">
    <aside class="side-panel">
      <div class="panel-header">
        <h3>模版库</h3>
        <span class="subtitle">点击图片引用风格</span>
      </div>
      
      <el-tabs v-model="activeTab" class="poster-tabs" stretch>
        <el-tab-pane
          v-for="category in posterCategories"
          :key="category.id"
          :name="category.id"
          :label="category.name"
        >
          <div 
            class="tab-content-scroll"
            v-infinite-scroll="loadMore"
            :infinite-scroll-distance="50"
            :infinite-scroll-immediate="true"
          >
            <div class="example-grid">
              <div
                v-for="example in displayedExamples"
                :key="example.id"
                class="example-card"
                :class="{ 
                  disabled: !canAddMoreImages,
                  active: referenceImages.some(img => img.remote === example.cover) 
                }"
                @click="handleExampleSelect(example)"
              >
                <div class="card-image">
                  <img :src="example.cover" :alt="example.title" loading="lazy" />
                  <div class="card-overlay">
                    <span class="use-btn">引用</span>
                  </div>
                </div>
                <p class="card-title">{{ example.title }}</p>
              </div>
            </div>
            
            <div class="scroll-status">
              <span v-if="displayedExamples.length >= (currentCategory?.examples.length || 0)" class="no-more">
                - 到底了 -
              </span>
              <span v-else class="loading-more">
                <el-icon class="is-loading"><Loading /></el-icon> 加载中...
              </span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </aside>

    <section class="chat-panel">
      <div ref="messageContainer" class="messages">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', message.role]"
        >
          <template v-if="message.type === 'loading'">
            <div class="bubble loading-state">
              <div class="loading-icon">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
              <div class="loading-content">
                <span class="loading-text">{{ message.content }}</span>
                <div class="loading-bar"></div>
              </div>
            </div>
          </template>
          
          <template v-else-if="message.type === 'text'">
            <div class="bubble text-bubble">
              {{ message.content }}
            </div>
          </template>
          
          <template v-else>
            <div class="bubble image-bubble">
              <div class="img-wrapper">
                <img :src="message.content" alt="chat image" />
              </div>
              <div class="img-actions-grid">
                <el-button 
                  class="action-btn" 
                  icon="Download" 
                  size="small" 
                  plain 
                  @click="downloadImage(message.content)"
                >
                  下载
                </el-button>
                <el-button 
                  class="action-btn" 
                  type="primary" 
                  icon="Plus" 
                  size="small" 
                  @click="addToCanvas(message.content)"
                >
                  添加到画布
                </el-button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="reference-strip" v-if="mode === 'reference'">
        <div class="strip-head">
          <div>引用区 <span class="count">{{ referenceImages.length }}/{{ MAX_REFERENCE_IMAGES }}</span></div>
          <span class="strip-note">引用来自模板，底图来自上传</span>
        </div>
        <div v-if="referenceImages.length" class="reference-list">
          <div class="reference-chip" v-for="img in referenceImages" :key="img.id">
            <img :src="img.src" alt="reference" />
            <div class="chip-info">
              <span class="chip-label" :class="img.kind">{{ img.kind === 'reference' ? '引用' : '底图' }}</span>
              <span class="chip-title">{{ img.title || '未命名图片' }}</span>
            </div>
            <div class="chip-remove" @click.stop="removeReference(img.id)">
              <el-icon><Close /></el-icon>
            </div>
          </div>
        </div>
        <p v-else class="reference-empty">从左侧模板或上传底图添加图片（最多两张）。</p>
      </div>

      <div class="chat-input">
        <div class="mode-toolbar inside">
          <div class="mode-title">模式</div>
          <div class="mode-row">
            <el-select v-model="mode" size="small" class="mode-select">
              <el-option v-for="opt in modeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
            <template v-if="mode === 'text'">
              <el-popover placement="bottom-start" trigger="click" width="360">
                <template #reference>
                  <button class="summary-pill outlined">
                    <span class="pill-ratio">{{ format.ratio }}</span>
                    <span class="pill-divider"></span>
                    <span class="pill-size">{{ formatSummary }}</span>
                  </button>
                </template>
                <div class="format-panel">
                  <div class="format-section">
                    <p>选择比例</p>
                    <div class="ratio-options">
                      <el-button
                        v-for="ratio in ratios"
                        :key="ratio"
                        size="small"
                        :type="ratio === format.ratio ? 'primary' : 'default'"
                        @click="selectRatio(ratio)"
                      >
                        {{ ratio }}
                      </el-button>
                    </div>
                  </div>
                  <div class="format-section size-inputs">
                    <p>尺寸 (px)</p>
                    <div class="size-row">
                      <el-input-number v-model="format.width" :min="256" :max="4096" />
                      <span>×</span>
                      <el-input-number v-model="format.height" :min="256" :max="4096" />
                    </div>
                  </div>
                </div>
              </el-popover>
            </template>
            <template v-else-if="mode === 'reference'">
              <el-button
                class="upload-btn-outlined"
                :loading="uploading"
                :disabled="uploading || !canAddMoreImages"
                @click="triggerImage"
              >
                <el-icon><UploadFilled /></el-icon>
                上传图片
              </el-button>
            </template>
          </div>
        </div>
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            class="fixed-textarea"
            resize="none"
            :placeholder="mode === 'art' ? '描述你想生成的艺术字效果' : '描述你想要的海报或提出问题'"
          />
        </div>
        <div class="chat-actions">
          <input ref="imageInput" class="hidden-input" type="file" accept="image/*" @change="handleImageSelect" />
          <el-button
            type="primary"
            @click="sendMessage"
            :loading="sending"
            :disabled="sending || !canSend"
          >
            发送
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
// 导入依赖
import posterTemplates from '@/assets/data/poster_templates.json'
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, UploadFilled, Loading, Download, Plus } from '@element-plus/icons-vue' // 记得导入新图标
import appConfig from '@/config'
import apiRequest from '@/utils/axios'
import { createPosterTask, getPosterTask } from '@/api/poster'
import { useRouter } from 'vue-router'
import { useWidgetStore } from '@/store'
import wImageSetting from '@/components/modules/widgets/wImage/wImageSetting'
import eventBus from '@/utils/plugins/eventBus'

// 类型定义
interface ChatMessage {
  id: string
  role: 'user' | 'ai'
  type: 'text' | 'image' | 'loading' // 新增 loading 类型
  content: string
}

interface PosterExample {
  id: string
  title: string
  cover: string
}

interface PosterTemplate {
  url: string
  title: string
  type: string
}

type ImageKind = 'reference' | 'base'

interface SelectedPosterImage {
  id: string
  src: string
  remote: string
  title?: string
  kind: ImageKind
  fileKey?: string
  ossUrl?: string
  source: 'template' | 'upload'
}

// 常量定义
const MAX_REFERENCE_IMAGES = 2
const BATCH_SIZE = 10
const POLL_INTERVAL = 3000 // 稍微缩短轮询间隔，提升感知
const DEFAULT_OSS_FOLDER = 'poster/base'
const apiHost = appConfig.API_URL && appConfig.API_URL.trim().length
  ? appConfig.API_URL
  : (typeof window !== 'undefined' ? window.location.origin : '')
const apiBase = apiHost.replace(/\/$/, '')

const categoryOrder = ['产品类', '品牌类', '节气类', '艺术字']

const buildPosterCategories = () => {
  const groups: Record<string, PosterExample[]> = {
    产品类: [],
    品牌类: [],
    节气类: [],
  }
  ;(posterTemplates as PosterTemplate[]).forEach((tpl, idx) => {
    if (groups[tpl.type]) {
      groups[tpl.type].push({ id: `${tpl.type}-${idx}`, title: tpl.title, cover: tpl.url })
    }
  })
  return categoryOrder.map((type) => ({
    id: type,
    name: type,
    examples: groups[type] || [],
  }))
}

const messages = reactive<ChatMessage[]>([
  { id: crypto.randomUUID(), role: 'ai', type: 'text', content: '你好，我是海报生成助手。告诉我你的想法或上传参考图，我会给出建议。' },
])

const inputText = ref('')
const modeOptions = [
  { label: '文生图', value: 'text' },
  { label: '参考图生成', value: 'reference' },
  { label: '艺术字生成', value: 'art' },
]
const mode = ref<'text' | 'reference' | 'art'>('text')
const ratios = ['21:9', '16:9', '3:2', '4:3', '1:1', '3:4', '2:3', '9:16']
const ratioSizeMap: Record<string, { width: number; height: number }> = {
  '1:1': { width: 2048, height: 2048 },
  '4:3': { width: 2304, height: 1728 },
  '3:2': { width: 2496, height: 1664 },
  '16:9': { width: 2560, height: 1440 },
  '21:9': { width: 3024, height: 1296 },
}
const format = reactive({
  ratio: '16:9',
  width: 1024,
  height: 768,
})
const sending = ref(false)
const uploading = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const messageContainer = ref<HTMLDivElement | null>(null)
const referenceImages = ref<SelectedPosterImage[]>([])
const pollTimer = ref<number | null>(null)

const posterCategories = reactive(buildPosterCategories())
const activeTab = ref(posterCategories[0]?.id || '产品类')

const limitMap = reactive<Record<string, number>>({})
posterCategories.forEach((cat) => (limitMap[cat.id] = BATCH_SIZE))

const currentCategory = computed(() => posterCategories.find((cat) => cat.id === activeTab.value))

const displayedExamples = computed(() => {
  const cat = currentCategory.value
  if (!cat) return []
  const limit = limitMap[cat.id] || BATCH_SIZE
  return cat.examples.slice(0, limit)
})

const canAddMoreImages = computed(() => referenceImages.value.length < MAX_REFERENCE_IMAGES)
const canSend = computed(() => {
  const text = inputText.value.trim()
  if (mode.value === 'reference') {
    return !!(text || referenceImages.value.length)
  }
  return !!text
})

watch(mode, (val) => {
  if (val !== 'reference') {
    referenceImages.value = []
  }
})

watch(activeTab, (val) => {
  if (!limitMap[val]) {
    limitMap[val] = BATCH_SIZE
  }
})

const formatSummary = computed(() => `${format.width}×${format.height}px`)

const selectRatio = (ratio: string) => {
  format.ratio = ratio
  if (ratioSizeMap[ratio]) {
    format.width = ratioSizeMap[ratio].width
    format.height = ratioSizeMap[ratio].height
  }
}
const router = useRouter()
const widgetStore = useWidgetStore()

const appendMessage = (message: ChatMessage) => {
  messages.push(message)
  nextTick(() => {
    messageContainer.value?.scrollTo({ top: messageContainer.value.scrollHeight, behavior: 'smooth' })
  })
  return message.id
}

const updateMessageContent = (id: string, content: string) => {
  const target = messages.find((msg) => msg.id === id)
  if (target) target.content = content
}

const ensureImageQuota = () => {
  if (!canAddMoreImages.value) {
    ElMessage.warning(`引用区最多只能放 ${MAX_REFERENCE_IMAGES} 张图片`)
    return false
  }
  return true
}

const addImageToStrip = (payload: Omit<SelectedPosterImage, 'id'>) => {
  referenceImages.value.unshift({ ...payload, id: crypto.randomUUID() })
  referenceImages.value = referenceImages.value.slice(0, MAX_REFERENCE_IMAGES)
}

const handleExampleSelect = (example: PosterExample) => {
  if (!ensureImageQuota()) return
  if (mode.value !== 'reference') {
    ElMessage.warning('此模式下不需要参考图，请切换到参考图生成')
    return
  }
  const hasTemplate = referenceImages.value.some((img) => img.source === 'template')
  if (hasTemplate) {
    ElMessage.warning('模板参考图只能选择一张，请上传底图')
    return
  }
  addImageToStrip({ src: example.cover, remote: example.cover, title: example.title, kind: 'reference', source: 'template' })
}

const triggerImage = () => {
  if (!ensureImageQuota()) return
  imageInput.value?.click()
}

const handleImageSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = input?.files
  if (!files || !files[0]) return
  if (!ensureImageQuota()) {
    input.value = ''
    return
  }
  uploading.value = true
  try {
    const { preview, remote, fileKey } = await uploadBaseImage(files[0])
    const hasTemplate = referenceImages.value.some((img) => img.source === 'template')
    const kind: ImageKind = mode.value === 'reference' && hasTemplate ? 'base' : 'reference'
    addImageToStrip({ src: preview, remote, title: files[0].name, kind, fileKey, source: 'upload' })
  } catch (error) {
    ElMessage.error(formatError(error))
  } finally {
    uploading.value = false
    if (input) input.value = ''
  }
}

const removeReference = (id: string) => {
  referenceImages.value = referenceImages.value.filter((img) => img.id !== id)
}

const loadMore = () => {
  const cat = currentCategory.value
  if (!cat) return
  
  const total = cat.examples.length
  const currentLimit = limitMap[cat.id]
  
  if (currentLimit < total) {
    limitMap[cat.id] = Math.min(currentLimit + BATCH_SIZE, total)
  }
}

const sendMessage = async () => {
  const trimmed = inputText.value.trim()
  if (!trimmed && !referenceImages.value.length) {
    ElMessage.warning('请输入内容或选择参考图')
    return
  }
  if (sending.value) return
  sending.value = true
  const snapshot = referenceImages.value.map((img) => ({ ...img }))
  try {
    await syncBaseImagesToOss(snapshot)
    if (trimmed) {
      appendMessage({ id: crypto.randomUUID(), role: 'user', type: 'text', content: trimmed })
    }
    snapshot.forEach((img) => {
      appendMessage({ id: crypto.randomUUID(), role: 'user', type: 'image', content: img.src })
    })

    const payload = {
      prompt: trimmed || '根据当前参考图片生成海报',
      references: snapshot.filter((img) => img.kind === 'reference').map((img) => img.remote),
      base_images: snapshot
        .filter((img) => img.kind === 'base')
        .map((img) => img.ossUrl || img.remote),
    }

    // 插入 loading 状态消息
    const statusId = appendMessage({
      id: crypto.randomUUID(),
      role: 'ai',
      type: 'loading', // 使用 loading 类型
      content: '正在提交任务...',
    })

    const resp = await createPosterTask(payload)
    const successCode = resp.code === 0 || resp.code === 200 || resp.stat === 1
    
    if (!successCode) {
      // 失败时将 loading 消息转为错误提示文本
      updateMessageContent(statusId, resp.message || '任务创建失败')
      const target = messages.find(m => m.id === statusId)
      if(target) target.type = 'text'
      throw new Error(resp.message || '任务创建失败')
    }

    const directUrls = resp.data?.image_urls || resp.image_urls
    if (directUrls?.length) {
      // 立即完成：更新 loading 消息为文本，并追加图片
      updateMessageContent(statusId, '生成完成，已返回预览。')
      const target = messages.find(m => m.id === statusId)
      if(target) target.type = 'text'
      
      directUrls.forEach((url) => appendMessage({ id: crypto.randomUUID(), role: 'ai', type: 'image', content: url }))
      sending.value = false
      referenceImages.value = []
      return
    }

    const taskId = resp.data?.task_id
    if (!taskId) {
      updateMessageContent(statusId, '系统异常：任务ID缺失')
      const target = messages.find(m => m.id === statusId)
      if(target) target.type = 'text'
      throw new Error('任务ID缺失')
    }
    
    // 任务创建成功，进入轮询，保持 loading 状态
    updateMessageContent(statusId, '正在排队中...')
    startPollingTask(taskId, statusId)
  } catch (error) {
    sending.value = false
    ElMessage.error(formatError(error))
  } finally {
    inputText.value = ''
  }
}

const uploadBaseImage = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiRequest<{ status: string; file_path?: string; message?: string }>('api/files/upload', formData, 'post')
  if (!response || response.status !== 'success' || !response.file_path) {
    throw new Error(response?.message || '上传失败')
  }
  const preview = await fileToDataUrl(file)
  return {
    preview,
    remote: `${apiBase}/api/files/${response.file_path}`,
    fileKey: response.file_path,
  }
}

const statusTextMap: Record<string, string> = {
  in_queue: '前方排队中...',
  generating: 'AI正在绘制...',
  processing: '努力生成中...',
  running: '正在处理细节...',
  pending: '等待调度...',
}

const clearPolling = () => {
  if (pollTimer.value) {
    window.clearTimeout(pollTimer.value)
    pollTimer.value = null
  }
}

const startPollingTask = (taskId: string, statusMessageId: string) => {
  clearPolling()
  const poll = async () => {
    try {
      const resp = await getPosterTask(taskId)
      if (resp.code !== 0) {
        throw new Error(resp.message || '查询失败')
      }
      const status = resp.data?.status || 'unknown'
      
      // 成功
      if (['done', 'success', 'finished'].includes(status)) {
        // 将 loading 状态改为文本提示
        updateMessageContent(statusMessageId, '生成完成！')
        const target = messages.find(m => m.id === statusMessageId)
        if(target) target.type = 'text'
        
        const urls = resp.data?.image_urls || []
        if (urls.length) {
          urls.forEach((url) => {
            appendMessage({ id: crypto.randomUUID(), role: 'ai', type: 'image', content: url })
          })
        } else {
          appendMessage({ id: crypto.randomUUID(), role: 'ai', type: 'text', content: '任务完成，但暂未获取到图片。' })
        }
        sending.value = false
        referenceImages.value = []
        clearPolling()
        return
      }
      
      // 失败
      if (['failed', 'error', 'timeout'].includes(status)) {
        updateMessageContent(statusMessageId, '生成失败，请稍后重试。')
        const target = messages.find(m => m.id === statusMessageId)
        if(target) target.type = 'text'
        sending.value = false
        clearPolling()
        return
      }
      
      // 继续轮询，更新 loading 提示文案
      updateMessageContent(statusMessageId, statusTextMap[status] || `状态: ${status}`)
      pollTimer.value = window.setTimeout(poll, POLL_INTERVAL)
    } catch (error) {
      updateMessageContent(statusMessageId, `查询失败：${formatError(error)}`)
      const target = messages.find(m => m.id === statusMessageId)
      if(target) target.type = 'text'
      sending.value = false
      clearPolling()
    }
  }
  poll()
}

const fileToDataUrl = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const formatError = (error: unknown) => (error instanceof Error ? error.message : String(error))

const syncBaseImagesToOss = async (images: SelectedPosterImage[]) => {
  const pending = images.filter((img) => img.kind === 'base' && !img.ossUrl && img.fileKey)
  if (!pending.length) return
  for (const img of pending) {
    const resp = await apiRequest<{ status: string; oss_url?: string; message?: string }>(
      'api/files/upload-oss',
      { file_path: img.fileKey, remote_path: DEFAULT_OSS_FOLDER },
      'post',
    )
    if (!resp || resp.status !== 'success' || !resp.oss_url) {
      throw new Error(resp?.message || 'OSS上传失败')
    }
    img.ossUrl = resp.oss_url
    const target = referenceImages.value.find((item) => item.id === img.id)
    if (target) {
      target.ossUrl = resp.oss_url
    }
  }
}

const downloadImage = async (url: string) => {
  try {
    const res = await fetch(url)
    const blob = await res.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `poster-${Date.now()}.png`
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (error) {
    ElMessage.error(formatError(error))
  }
}

const addToCanvas = async (url: string) => {
  const route = router.currentRoute.value
  if (route.name !== 'Home') {
    await router.push({ name: 'Home' })
  }
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.src = url
  img.onload = () => {
    const setting = JSON.parse(JSON.stringify(wImageSetting))
    setting.url = url
    setting.imgUrl = url
    setting.width = img.width
    setting.height = img.height
    widgetStore.addWidget(setting, { toTop: true })
    eventBus.emit('closePosterGenerate')
    ElMessage.success('已添加到画布')
  }
  img.onerror = () => ElMessage.error('加载图片失败')
}

onBeforeUnmount(() => {
  clearPolling()
})
</script>

<style scoped lang="less">
.poster-generate {
  display: flex;
  height: 75vh;
  background: #f3f5f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
.poster-generate.modal-mode {
  height: calc(90vh - 40px);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.08);
}

/* --- 左侧侧边栏 --- */
.side-panel {
  width: 320px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #ebedf0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.panel-header {
  padding: 1.25rem 1.5rem 0.5rem;
  flex-shrink: 0;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1f2d3d;
  }
  .subtitle {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    display: block;
  }
}

.poster-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 0.5rem;
  
  :deep(.el-tabs__header) {
    margin: 0 1.5rem 10px;
    border-bottom: none;
    
    .el-tabs__nav-wrap::after {
      height: 1px;
      background-color: #f0f2f5;
    }
    
    .el-tabs__item {
      font-size: 14px;
      color: #606266;
      padding: 0 10px;
      height: 40px;
      
      &.is-active {
        color: #409eff;
        font-weight: 600;
      }
    }
  }

  :deep(.el-tabs__content) {
    flex: 1;
    padding: 0;
    overflow: hidden;
  }
  
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.tab-content-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 0 1.5rem 1.5rem;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background-color: transparent;
    border-radius: 3px;
  }
  &:hover::-webkit-scrollbar-thumb {
    background-color: rgba(144, 147, 153, 0.3);
  }
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding-top: 4px;
}

.example-card {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  .card-image {
    position: relative;
    width: 100%;
    padding-top: 133%;
    background: #f5f7fa;
    
    img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }
    
    .card-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0,0,0,0.3);
      opacity: 0;
      transition: opacity 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2;
      
      .use-btn {
        background: rgba(255,255,255,0.95);
        color: #333;
        font-size: 12px;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        transform: translateY(10px);
        transition: transform 0.2s ease;
      }
    }
  }

  .card-title {
    margin: 0;
    padding: 8px 4px;
    font-size: 13px;
    color: #333;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: center;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    
    .card-image img {
      transform: scale(1.05);
    }
    .card-overlay {
      opacity: 1;
      .use-btn {
        transform: translateY(0);
      }
    }
  }

  &.disabled {
    opacity: 0.5;
    filter: grayscale(0.6);
    cursor: not-allowed;
    &:hover {
      transform: none;
      box-shadow: none;
      .card-overlay { opacity: 0; }
    }
  }
  
  &.active {
    box-shadow: 0 0 0 2px #409eff;
  }
}

.scroll-status {
  text-align: center;
  padding: 20px 0;
  color: #c0c4cc;
  font-size: 12px;
  
  .loading-more {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
}

/* --- 右侧聊天区 --- */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-width: 0;
}

.messages {
  flex: 1;
  padding: 2rem;
  background: #f9fafc;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  display: flex;
  width: 100%;
  
  &.user {
    justify-content: flex-end;
    .bubble {
      background: linear-gradient(135deg, #409eff, #337ecc);
      color: #fff;
      border-bottom-right-radius: 2px;
      box-shadow: 0 4px 10px rgba(64, 158, 255, 0.2);
    }
  }
  &.ai {
    justify-content: flex-start;
    .bubble {
      background: #ffffff;
      color: #333;
      border: 1px solid #eef0f2;
      border-bottom-left-radius: 2px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
  }
}
.mode-select {
  width: 100px;
}
.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

/* Loading 气泡样式 */
.bubble.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border: 1px solid #e6e8eb;
  background: #fff;
  color: #606266;
  position: relative;
  overflow: hidden;
}

/* 脉冲背景效果 */
.bubble.loading-state::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(64, 158, 255, 0.06), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.loading-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.loading-text {
  font-weight: 500;
  color: #303133;
}

/* 图片气泡样式优化 */
.bubble.image-bubble {
  padding: 8px;
  background: #fff;
  border: 1px solid #ebedf0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.img-wrapper {
  border-radius: 8px;
  overflow: hidden;
  background: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
}

.bubble img {
  display: block;
  max-width: 220px; /* 限制最大宽度 */
  max-height: 300px;
  object-fit: contain;
  border-radius: 6px;
  transition: transform 0.3s;
}

.img-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 8px;
  padding: 0 2px 2px;
}

.action-btn {
  width: 100%;
  margin: 0 !important;
  height: 32px;
}

/* --- 引用区优化 (Fix Issue 1) --- */
.reference-strip {
  background: #ffffff;
  border-top: 1px solid #e4e7ed;
  padding: 12px 20px;
  
  .strip-head {
    margin-bottom: 10px;
    .count { color: #409eff; }
  }
}

.reference-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.reference-chip {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #dcdfe6;
  padding: 6px;
  padding-right: 36px; /* 给关闭按钮留位置 */
  border-radius: 8px;
  position: relative;
  width: 200px; /* 固定宽度，或者 max-width */
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  
  img {
    width: 48px;
    height: 48px;
    border-radius: 6px;
    object-fit: cover; /* 关键：防止变形 */
    flex-shrink: 0;
    background: #f5f7fa;
    border: 1px solid #f0f0f0;
  }
  
  .chip-info {
    margin-left: 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    overflow: hidden; /* 配合 text-overflow */
    flex: 1;
  }
  
  .chip-label {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 4px;
    align-self: flex-start;
    font-weight: 600;
    
    &.reference { background: #ecf5ff; color: #409eff; }
    &.base { background: #f0f9eb; color: #67c23a; }
  }
  
  .chip-title {
    font-size: 12px;
    color: #333;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }
  
  .chip-remove {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    cursor: pointer;
    color: #909399;
    transition: all 0.2s;
    
    &:hover {
      background: #fef0f0;
      color: #f56c6c;
    }
  }
}

.reference-empty {
  font-size: 12px;
  color: #999;
}

/* --- 输入区 --- */
.chat-input {
  padding: 1rem 2rem 2rem;
  background: #fff;
  border-top: 1px solid #f2f3f5;
}

.mode-toolbar {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  
  .mode-title {
    font-weight: 600;
    color: #303133;
    margin-right: 12px;
    font-size: 13px;
  }
  
  .mode-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.summary-pill {
  background: #2f323a;
  border: 1px solid #3f434d;
  color: #fff;
  border-radius: 10px;
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  
  &.outlined {
    background: #fff;
    color: #111;
    border: 1px solid #dcdfe6;
  }
}

.upload-btn-outlined {
  border: 1px solid #dcdfe6;
  color: #606266;
  background: #fff;
  border-radius: 10px;
  padding: 6px 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  
  &:hover {
    border-color: #409eff;
    color: #409eff;
  }
}

.input-area {
  position: relative;
  
  :deep(.el-textarea__inner) {
    background: #f5f7fa;
    border: none;
    border-radius: 12px;
    padding: 12px;
    font-size: 14px;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.03);
    transition: background 0.2s;
    height: 82px !important;
    
    &:focus {
      background: #fff;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.03), 0 0 0 1px #409eff;
    }
  }
}

.chat-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  
  :deep(.el-button--primary) {
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
    
    &:disabled {
      box-shadow: none;
    }
  }
}

.hidden-input {
  display: none;
}

.format-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem;
}
.format-section {
  background: #f9fafc;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 0.75rem;
}
.format-section p {
  margin: 0 0 0.5rem;
  font-size: 12px;
  color: #606266;
  font-weight: 600;
}
.ratio-options {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}
.size-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>