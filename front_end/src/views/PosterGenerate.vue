<template>
  <div class="poster-generate modal-mode">
    <aside class="side-panel">
      
      <el-tabs v-model="activeTab" class="poster-tabs">
        <el-tab-pane
          v-for="category in posterCategories"
          :key="category.id"
          :name="category.id"
          :label="category.name"
        >
          <div class="tab-content-scroll">
            <div class="example-grid">
              <div
                v-for="example in displayedExamples"
                :key="example.id"
                class="example-card"
                :class="{ disabled: !canAddMoreImages }"
                :title="!canAddMoreImages ? '最多只能添加两张图片' : '点击引用该模板'"
                @click="handleExampleSelect(example)"
              >
                <img :src="example.cover" :alt="example.title" />
                <p>{{ example.title }}</p>
              </div>
            </div>
            <div class="pagination" v-if="totalPages > 1">
              <el-button size="small" @click="changePage(-1)" :disabled="currentPage <= 1">上一页</el-button>
              <span>{{ currentPage }} / {{ totalPages }}</span>
              <el-button size="small" @click="changePage(1)" :disabled="currentPage >= totalPages">下一页</el-button>
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
          <div class="bubble">
            <template v-if="message.type === 'text'">
              {{ message.content }}
            </template>
            <template v-else>
              <img :src="message.content" alt="chat image" />
              <div class="img-actions">
                <el-button text size="small" @click="downloadImage(message.content)">下载</el-button>
                <el-button text type="primary" size="small" @click="addToCanvas(message.content)">添加到画布</el-button>
              </div>
            </template>
          </div>
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
            <el-icon class="chip-close" @click.stop="removeReference(img.id)">
              <Close />
            </el-icon>
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
import { Close, UploadFilled } from '@element-plus/icons-vue'
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
  type: 'text' | 'image'
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
const TEMPLATES_PER_PAGE = 6
const POLL_INTERVAL = 5000
const DEFAULT_OSS_FOLDER = 'poster/base'
const apiHost = appConfig.API_URL && appConfig.API_URL.trim().length
  ? appConfig.API_URL
  : (typeof window !== 'undefined' ? window.location.origin : '')
const apiBase = apiHost.replace(/\/$/, '')

const categoryOrder = ['产品类', '品牌类', '节气类']

// 构建海报分类数据
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

// 响应式数据
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
const pageMap = reactive<Record<string, number>>({})
posterCategories.forEach((cat) => (pageMap[cat.id] = 1))

// 计算属性
const currentCategory = computed(() => posterCategories.find((cat) => cat.id === activeTab.value))
const currentPage = computed(() => (currentCategory.value ? pageMap[currentCategory.value.id] : 1))
const totalPages = computed(() => {
  const examples = currentCategory.value?.examples || []
  return Math.max(1, Math.ceil(examples.length / TEMPLATES_PER_PAGE))
})
const displayedExamples = computed(() => {
  const cat = currentCategory.value
  if (!cat) return []
  const page = currentPage.value
  const start = (page - 1) * TEMPLATES_PER_PAGE
  return cat.examples.slice(start, start + TEMPLATES_PER_PAGE)
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

// 消息处理函数
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

// 图片引用区处理
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

// 分页处理
const changePage = (delta: number) => {
  const cat = currentCategory.value
  if (!cat) return
  const next = currentPage.value + delta
  if (next >= 1 && next <= totalPages.value) {
    pageMap[cat.id] = next
  }
}

// 发送消息与任务处理
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

    const resp = await createPosterTask(payload)
    const successCode = resp.code === 0 || resp.code === 200 || resp.stat === 1
    if (!successCode) {
      throw new Error(resp.message || '任务创建失败')
    }
    const directUrls = resp.data?.image_urls || resp.image_urls
    if (directUrls?.length) {
      appendMessage({ id: crypto.randomUUID(), role: 'ai', type: 'text', content: '生成完成，已返回预览。' })
      directUrls.forEach((url) => appendMessage({ id: crypto.randomUUID(), role: 'ai', type: 'image', content: url }))
      sending.value = false
      referenceImages.value = []
      return
    }
    const taskId = resp.data?.task_id
    if (!taskId) {
      throw new Error('任务ID缺失')
    }
    const statusId = appendMessage({
      id: crypto.randomUUID(),
      role: 'ai',
      type: 'text',
      content: '已提交生成任务，正在排队…',
    })
    startPollingTask(taskId, statusId)
  } catch (error) {
    sending.value = false
    ElMessage.error(formatError(error))
  } finally {
    inputText.value = ''
  }
}

// 图片上传相关
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

// 任务轮询相关
const statusTextMap: Record<string, string> = {
  in_queue: '排队中',
  generating: '生成中',
  processing: '生成中',
  running: '生成中',
  pending: '排队中',
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
      if (['done', 'success', 'finished'].includes(status)) {
        updateMessageContent(statusMessageId, '生成完成，已返回预览。')
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
      if (['failed', 'error', 'timeout'].includes(status)) {
        updateMessageContent(statusMessageId, '生成失败，请稍后重试。')
        sending.value = false
        clearPolling()
        return
      }
      updateMessageContent(statusMessageId, `任务${statusTextMap[status] || status}，请稍候…`)
      pollTimer.value = window.setTimeout(poll, POLL_INTERVAL)
    } catch (error) {
      updateMessageContent(statusMessageId, `查询失败：${formatError(error)}`)
      sending.value = false
      clearPolling()
    }
  }
  poll()
}

// 工具函数
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

// 图片操作
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

// 组件卸载前清理
onBeforeUnmount(() => {
  clearPolling()
})
</script>

<style scoped lang="less">
.poster-generate {
  display: flex;
  height: 70vh;
  background: #f5f6f8;
}
.poster-generate.modal-mode {
  height: calc(90vh - 60px);
}
.side-panel {
  width: 35%;
  min-width: 360px; /* 增加最小宽度，确保卡片显示空间 */
  background: #ffffff;
  border-right: 1px solid #e7e7e7;
  padding: 1.5rem; /* 优化内边距 */
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow: hidden;
}
.side-panel .desc {
  color: #777;
  line-height: 1.6;
}
.quota-tip {
  font-size: 12px;
  color: #666;
  background: #f6f7fb;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.quota-tip span {
  color: #999;
}
.poster-tabs {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.poster-tabs :deep(.el-tabs__header) {
  flex-shrink: 0; /* 防止 tab 头部被压缩 */
}
.poster-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.poster-tabs :deep(.el-tab-pane) {
  height: 100%; 
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.tab-content-scroll {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-height: 0;
  padding: 0.5rem 0; /* 统一内边距 */
}

.example-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  padding: 0.5rem;
  align-content: start;
}

/* 优化卡片样式 */
.example-card {
  border: 1px solid #e8eaec;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  background: #ffffff;
  height: 100%;
  min-height: 220px; /* 固定最小高度，确保卡片整齐 */
  transition: none; /* 移除过渡效果 */
}

/* 彻底移除hover效果 */
.example-card:hover {
  transform: none;
  box-shadow: none;
}

.example-card.disabled {
  opacity: 0.45;
  pointer-events: none;
}

.example-card img {
  width: 100%;
  aspect-ratio: 3 / 4; /* 保持稳定比例 */
  object-fit: cover;
  display: block;
  border-bottom: 1px solid #f0f0f0;
}

.example-card p {
  margin: 0;
  padding: 0.75rem;
  font-size: 13px;
  color: #444;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 2.5em; /* 固定标题区域高度 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin: 1rem 0.5rem; /* 与网格内边距对齐 */
  flex-shrink: 0;
}
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.messages {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.message {
  display: flex;
}
.message.user {
  justify-content: flex-end;
}
.message.ai {
  justify-content: flex-start;
}
.bubble {
  max-width: 60%;
  padding: 0.9rem 1rem;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.message.user .bubble {
  background: #409eff;
  color: #fff;
}
.bubble img {
  max-width: 260px;
  border-radius: 8px;
}
.img-actions {
  margin-top: 0.4rem;
  display: flex;
  gap: 0.5rem;
}
.reference-strip {
  padding: 0.8rem 1.5rem;
  background: #fff;
  border-top: 1px solid #e7e7e7;
  border-bottom: 1px solid #e7e7e7;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.strip-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}
.strip-head .count {
  margin-left: 0.35rem;
  font-weight: 600;
  color: #333;
}
.strip-note {
  font-size: 12px;
  color: #999;
}
.reference-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.reference-chip {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: #f5f6f8;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 12px;
  min-width: 0;
}
.reference-chip img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
.chip-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.chip-label {
  font-size: 11px;
  padding: 0 6px;
  border-radius: 999px;
  color: #fff;
  align-self: flex-start;
}
.chip-label.reference {
  background: #409eff;
}
.chip-label.base {
  background: #67c23a;
}
.chip-title {
  font-size: 12px;
  color: #444;
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chip-close {
  font-size: 14px;
  cursor: pointer;
  color: #999;
}
.reference-empty {
  font-size: 12px;
  color: #999;
}
.mode-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
}
.mode-toolbar.inside {
  padding: 0 0 0.75rem;
}
.mode-title {
  font-size: 13px;
  color: #666;
}
.mode-select {
  width: 160px;
}
.format-summary {
  padding: 0 0 0.5rem;
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
}
.summary-pill .pill-ratio {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.pill-divider {
  width: 1px;
  height: 14px;
  background: rgba(255,255,255,0.35);
  display: inline-block;
}
.summary-pill .pill-size {
  font-weight: 600;
}
.summary-pill.outlined {
  background: #fff;
  color: #111;
  border: 1px solid #111;
}
.upload-btn-outlined {
  border: 1px solid #111;
  color: #111;
  background: #fff;
  border-radius: 10px;
  padding: 6px 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.format-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: #fff;
  color: #111;
  border-radius: 12px;
  border: 1px solid #dcdfe6;
  padding: 0.75rem;
}
.format-section {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 0.75rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.format-section p {
  margin: 0 0 0.5rem;
  font-size: 12px;
  color: #333;
}
.ratio-options {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem;
}
.ratio-options :deep(.el-button) {
  background: #fff;
  border: 1px solid #dcdfe6;
  color: #333;
}
.ratio-options :deep(.el-button.is-active),
.ratio-options :deep(.el-button.el-button--primary) {
  background: #4a90e2;
  border-color: #4a90e2;
  color: #fff;
}
.size-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.size-row span {
  color: #333;
  font-size: 12px;
}
.size-row :deep(.el-input-number__increase),
.size-row :deep(.el-input-number__decrease) {
  background: #f5f7fa;
  border-color: #dcdfe6;
  color: #333;
}
.chat-input {
  padding: 1rem 1.5rem 1.5rem;
  border-top: 1px solid #e7e7e7;
  background: #fff;
}
.input-area .fixed-textarea :deep(.el-textarea__inner) {
  height: 82px !important;
  overflow-y: auto;
}
.chat-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.75rem;
  justify-content: flex-end;
  align-items: center;
}
.icon-button {
  font-size: 18px;
}
.hidden-input {
  display: none;
}
</style>
