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
  fetch<PosterTaskResponse>('api/poster/tasks', payload, 'post', {}, { timeout: 180000 })

export const getPosterTask = (taskId: string) =>
  fetch<PosterTaskResponse>(`api/poster/tasks/${taskId}`, {}, 'get')
