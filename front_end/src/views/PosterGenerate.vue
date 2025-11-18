<template>
  <div class="poster-generate modal-mode">
    <aside class="side-panel">
      <h2>海报生成助手</h2>
      <p class="desc">选择参考模板或上传图片，帮助 AI 更好理解你的需求。</p>
      <div class="quota-tip">
        引用区：{{ referenceImages.length }}/{{ MAX_REFERENCE_IMAGES }}
        <span>引用+底图最多 {{ MAX_REFERENCE_IMAGES }} 张</span>
      </div>
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
      <div class="reference-strip">
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
        <el-input
          v-model="inputText"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 4 }"
          placeholder="描述你想要的海报或提出问题"
        />
        <div class="chat-actions">
          <input ref="imageInput" class="hidden-input" type="file" accept="image/*" @change="handleImageSelect" />
          <el-tooltip content="上传底图" placement="top">
            <el-button
              circle
              text
              class="icon-button"
              :loading="uploading"
              :disabled="uploading || !canAddMoreImages"
              @click="triggerImage"
            >
              <el-icon>
                <UploadFilled />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-button
            type="primary"
            @click="sendMessage"
            :loading="sending"
            :disabled="sending || (!inputText && !referenceImages.length)"
          >
            发送
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import posterTemplates from '@/assets/data/poster_templates.json'
import { computed, nextTick, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, UploadFilled } from '@element-plus/icons-vue'
import appConfig from '@/config'
import apiRequest from '@/utils/axios'
import { createPosterTask, getPosterTask } from '@/api/poster'
import { useRouter } from 'vue-router'
import { useWidgetStore } from '@/store'
import wImageSetting from '@/components/modules/widgets/wImage/wImageSetting'

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
}

const MAX_REFERENCE_IMAGES = 2
const POLL_INTERVAL = 5000
const DEFAULT_OSS_FOLDER = 'poster/base'
const apiHost = appConfig.API_URL && appConfig.API_URL.trim().length
  ? appConfig.API_URL
  : (typeof window !== 'undefined' ? window.location.origin : '')
const apiBase = apiHost.replace(/\/$/, '')

const categoryOrder = ['产品类', '品牌类', '节气类']

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

const currentCategory = computed(() => posterCategories.find((cat) => cat.id === activeTab.value))
const currentPage = computed(() => (currentCategory.value ? pageMap[currentCategory.value.id] : 1))
const totalPages = computed(() => {
  const examples = currentCategory.value?.examples || []
  return Math.max(1, Math.ceil(examples.length / 20))
})
const displayedExamples = computed(() => {
  const cat = currentCategory.value
  if (!cat) return []
  const page = currentPage.value
  const start = (page - 1) * 20
  return cat.examples.slice(start, start + 20)
})

const canAddMoreImages = computed(() => referenceImages.value.length < MAX_REFERENCE_IMAGES)
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
}

const handleExampleSelect = (example: PosterExample) => {
  if (!ensureImageQuota()) return
  addImageToStrip({ src: example.cover, remote: example.cover, title: example.title, kind: 'reference' })
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
    addImageToStrip({ src: preview, remote, title: files[0].name, kind: 'base', fileKey })
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

const changePage = (delta: number) => {
  const cat = currentCategory.value
  if (!cat) return
  const next = currentPage.value + delta
  if (next >= 1 && next <= totalPages.value) {
    pageMap[cat.id] = next
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
    router.push({ name: 'Home' })
  }
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.src = url
  img.onload = () => {
    const setting = JSON.parse(JSON.stringify(wImageSetting))
    setting.url = url
    setting.width = img.width
    setting.height = img.height
    widgetStore.addWidget(setting)
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
  height: 70vh;
  background: #f5f6f8;
}
.poster-generate.modal-mode {
  height: calc(90vh - 60px);
}
.side-panel {
  width: 32%;
  min-width: 320px;
  background: #ffffff;
  border-right: 1px solid #e7e7e7;
  padding: 2rem;
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
}

.example-grid {
  flex:1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding-right: 1rem 0.5rem 1rem 0;
  align-content: start;
}
.example-card {
  border: 1px solid #e8eaec;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fafafa;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: fit-content;
}
.example-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
}
.example-card.disabled {
  opacity: 0.45;
  pointer-events: none;
  transform: none;
  box-shadow: none;
}
.example-card img {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  display: block;
}
.example-card p {
  margin: 0;
  padding: 0.5rem;
  font-size: 12px;
  color: #555;
  text-align: center;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1rem 0;
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
.chat-input {
  padding: 1rem 1.5rem 1.5rem;
  border-top: 1px solid #e7e7e7;
  background: #fff;
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
