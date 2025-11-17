<template>
  <div class="psd-uploader">
    <el-upload
      class="upload-demo"
      drag
      action="/"
      :auto-upload="false"
      :show-file-list="false"
      :limit="1"
      :on-change="handleFileChange"
      accept=".psd,.psb"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        Drop PSD file here or <em>click to upload</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          Only PSD files with a size less than 20MB
        </div>
      </template>
    </el-upload>

    <div v-if="processing" class="processing-container">
      <el-progress
        :percentage="progress"
        :status="progressStatus"
        :stroke-width="10"
      />
      <div class="status-message">{{ statusMessage }}</div>
    </div>

    <div v-if="result" class="result-container">
      <el-result
        icon="success"
        title="Processing Complete"
        :sub-title="`File processed successfully: ${result.file_path}`"
      >
        <template #extra>
          <el-button type="primary" @click="downloadResult">
            Download Processed File
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { processPSD, downloadProcessedFile, PSDProcessResponse } from '@/api/psd'

export default defineComponent({
  name: 'PSDUploader',
  components: {
    UploadFilled
  },
  emits: ['processed'],
  setup(_, { emit }) {
    const processing = ref(false)
    const progress = ref(0)
    const statusMessage = ref('')
    const result = ref<PSDProcessResponse | null>(null)
    const currentFile = ref<File | null>(null)

    const progressStatus = ref('')

    const resetState = () => {
      processing.value = false
      progress.value = 0
      statusMessage.value = ''
      result.value = null
      progressStatus.value = ''
    }

    const handleFileChange = (uploadFile: any) => {
      // Reset state when a new file is selected
      resetState()
      const raw: File | undefined = uploadFile?.raw || uploadFile // element-plus UploadFile or native File
      if (!raw) {
        ElMessage.error('无法读取文件，请重试')
        return false
      }

      // Validate file type
      const name = raw.name?.toLowerCase?.() || ''
      if (!name.endsWith('.psd') && !name.endsWith('.psb')) {
        ElMessage.error('Only PSD files are supported')
        return false
      }

      // Validate file size (20MB limit)
      if (raw.size > 20 * 1024 * 1024) {
        ElMessage.error('File size should not exceed 20MB')
        return false
      }

      currentFile.value = raw
      processPSDFile(raw)
      return false // Prevent auto upload
    }

    const processPSDFile = async (file: File) => {
      try {
        processing.value = true
        statusMessage.value = 'Uploading file...'
        progressStatus.value = ''

        const response = await processPSD(
          file,
          {
            skipOcr: false,
            outputFormat: 'png'
          },
          (uploadProgress: number) => {
            progress.value = Math.min(90, uploadProgress) // Cap at 90% for processing
          }
        )

        statusMessage.value = 'Processing file...'
        progress.value = 95
        
        // Small delay to show processing state
        await new Promise(resolve => setTimeout(resolve, 500))
        
        result.value = response
        progress.value = 100
        progressStatus.value = 'success'
        statusMessage.value = 'Processing complete!'
        
        ElMessage.success('PSD processed successfully')
        // 向父组件抛出完成事件，携带后端返回（含 canvas 数据）
        emit('processed', response)
      } catch (error: any) {
        console.error('Error processing PSD:', error)
        progressStatus.value = 'exception'
        statusMessage.value = 'Error processing file: ' + (error.message || 'Unknown error')
        ElMessage.error('Failed to process PSD: ' + (error.message || 'Unknown error'))
      } finally {
        processing.value = false
      }
    }

    const downloadResult = () => {
      if (result.value?.file_path) {
        const originalName = currentFile.value?.name || 'processed'
        const fileName = originalName.replace(/\.(psd|psb)$/i, '_processed.png')
        downloadProcessedFile(result.value.file_path, fileName)
      }
    }

    return {
      processing,
      progress,
      progressStatus,
      statusMessage,
      result,
      handleFileChange,
      downloadResult
    }
  }
})
</script>

<style scoped>
.psd-uploader {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.upload-demo {
  margin-bottom: 20px;
}

.processing-container {
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.status-message {
  margin-top: 10px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.result-container {
  margin-top: 20px;
  text-align: center;
}
</style>
