/*
 * @Author: Jeremy Yu
 * @Date: 2024-03-03 19:00:00
 * @Description: 裁剪组件公共方法
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @Date: 2024-03-03 19:00:00
 */

import Qiniu from '@/common/methods/QiNiu'
import { TCommonUploadCb } from '@/api/ai'
import { TImageCutoutState } from './index.vue'
import api from '@/api'
import { getImage } from '@/common/methods/getImgDetail'
import _config from '@/config'
import { Ref } from 'vue'

const apiBaseUrl = _config.API_URL.replace(/\/$/, '')

const buildAbsoluteUrl = (url: string) => {
  if (!url) {
    return ''
  }
  if (/^https?:\/\//i.test(url)) {
    return url
  }
  return `${apiBaseUrl}${url.startsWith('/') ? '' : '/'}${url}`
}

/** 选择图片 */
export const selectImageFile = async (state: TImageCutoutState, raw: Ref<HTMLElement | null>, file: File, successCb?: (result: string, fileName: string) => void, uploadCb?: TCommonUploadCb) => {
  if (!raw.value) return

  raw.value.addEventListener('load', () => {
    state.offsetWidth = (raw.value as HTMLElement).offsetWidth
  })

  if (state.rawImage && state.rawImage.startsWith('blob:')) {
    URL.revokeObjectURL(state.rawImage)
  }
  const objectUrl = URL.createObjectURL(file)
  state.rawImage = objectUrl
  state.progressText = '上传中..'
  state.progress = 0

  try {
    const result = await api.cutout.removeBg(file, (up: number, dp: number) => {
      uploadCb && uploadCb(up, dp)
      if (dp) {
        state.progressText = dp === 100 ? '' : '导入中..'
        state.progress = dp
      } else {
        state.progressText = up < 100 ? '上传中..' : '正在处理，请稍候..'
        state.progress = up < 100 ? up : 0
      }
    })

    const url = buildAbsoluteUrl(result.url || '')
    state.cutImage = url
    successCb && successCb(url, file.name)
    state.progressText = ''
  } catch (error) {
    console.error('remove background failed', error)
    state.progressText = '处理失败，请重试'
  } finally {
    state.progress = 0
  }
}

export async function uploadCutPhotoToCloud(cutImage: string) {
  try {
    const response = await fetch(cutImage)
    const buffer = await response.arrayBuffer()
    const file = new File([buffer], `cut_image_${Math.random()}.png`)
    // upload
    const qnOptions = { bucket: 'xp-design', prePath: 'user' }
    const result = await Qiniu.upload(file, qnOptions)
    const { width, height } = await getImage(file)
    const url = _config.IMG_URL + result.key
    await api.material.addMyPhoto({ width, height, url })
    return url
  } catch (e) {
    console.error(`upload cut file error: msg: ${e}`)
    return ''
  }
}
