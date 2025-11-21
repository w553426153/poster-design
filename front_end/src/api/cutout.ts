import fetch from '@/utils/axios'
import type { TCommonUploadCb } from './ai'

type TUploadProgressCbData = {
  loaded: number
  total: number
}

type RemoveBgResponse = {
  status: string
  file_path: string
  url: string
}

export const removeBg = (file: File, cb?: TCommonUploadCb) => {
  const formData = new FormData()
  formData.append('file', file)
  const extra = cb
    ? {
        onUploadProgress: (progress: TUploadProgressCbData) => {
          cb(Math.floor((progress.loaded / progress.total) * 100), 0)
        },
        onDownloadProgress: (progress: TUploadProgressCbData) => {
          cb(100, Math.floor((progress.loaded / progress.total) * 100))
        },
      }
    : {}
  // 统一走 /api 前缀，由 axios 拦截器 + config.API_URL 处理
  // 实际请求路径: {API_URL}/cutout/remove-bg  =>  /api/cutout/remove-bg
  return fetch<RemoveBgResponse>('cutout/remove-bg', formData, 'post', {}, extra)
}
