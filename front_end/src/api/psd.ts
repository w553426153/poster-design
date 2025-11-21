import fetch from '@/utils/axios'
import { ElMessage } from 'element-plus'
import appConfig from '@/config'

export interface PSDProcessOptions {
  skipOcr?: boolean
  outputFormat?: 'png' | 'jpg' | 'jpeg' | 'webp'
}

export interface PSDProcessResponse {
  status: 'success' | 'error'
  file_path?: string
  message: string
  canvas?: CanvasData
}

export interface CanvasData {
  width: number
  height: number
  background: { color: string; image_url?: string }
  clouds: Array<{
    type: 'image' | 'text'
    width: number
    height: number
    top: number
    left: number
    opacity: number
    image_url?: string
    src?: any
  }>
}

/**
 * Process PSD file by removing text layers
 * @param file PSD file to process
 * @param options Processing options
 * @param onProgress Progress callback
 * @returns Promise with processing result
 */
export const processPSD = async (
  file: File, 
  options: PSDProcessOptions = {},
  onProgress?: (progress: number) => void
): Promise<PSDProcessResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  // 通过表单传递参数，避免误入 headers
  if (typeof options.skipOcr === 'boolean') formData.append('skip_ocr', String(options.skipOcr))
  formData.append('output_format', options.outputFormat || 'png')
  formData.append('return_canvas', 'true')
  
  try {
    // 走统一的 axios 封装，由 appConfig.API_URL 统一加上 /api 前缀
    // 实际请求路径: {API_URL}/psd/process => /api/psd/process
    const response = await fetch<PSDProcessResponse>('psd/process', formData, 'post', {}, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: ProgressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    
    if (response.status === 'error') {
      throw new Error(response.message || 'Failed to process PSD file')
    }
    
    return response
  } catch (error: any) {
    console.error('Error processing PSD:', error)
    ElMessage.error(error.message || 'Failed to process PSD file')
    throw error
  }
}

/**
 * Download processed file
 * @param filePath Relative path of the file to download
 * @param fileName Optional custom filename for the download
 */
export const downloadProcessedFile = (filePath: string, fileName?: string) => {
  try {
    const apiBase = appConfig.API_URL.replace(/\/$/, '')
    const url = `${apiBase}/psd/download/${encodeURIComponent(filePath)}`
    const link = document.createElement('a')
    link.href = url
    link.download = fileName || filePath.split('/').pop() || 'processed_file.png'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error: any) {
    console.error('Error downloading file:', error)
    ElMessage.error(error.message || 'Failed to download file')
    throw error
  }
}

/**
 * Get the full URL for a processed file
 * @param filePath Relative path of the file
 * @returns Full URL to access the file
 */
export const getFileUrl = (filePath: string): string => {
  const apiBase = appConfig.API_URL.replace(/\/$/, '')
  return `${apiBase}/files/${encodeURIComponent(filePath)}`
}
