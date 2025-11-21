import fetch from '@/utils/axios'

export interface PosterTaskPayload {
  prompt: string
  references?: string[]
  base_images?: string[]
  gen_num?: number
  width?: number
  height?: number
  mode?: string
}

export interface PosterTaskResponse {
  code: number
  message: string
  data?: {
    task_id?: string
    status?: string
    image_urls?: string[]
  }
}

export const createPosterTask = (payload: PosterTaskPayload) =>
  // 实际请求路径: {API_URL}/poster/tasks  =>  /api/poster/tasks
  fetch<PosterTaskResponse>('poster/tasks', payload, 'post', {}, { timeout: 180000 })

export const getPosterTask = (taskId: string) =>
  fetch<PosterTaskResponse>(`poster/tasks/${taskId}`, {}, 'get')
